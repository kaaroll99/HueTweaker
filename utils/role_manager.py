"""Bot-managed color roles: one role per member, named ``🎨 <display name>``.

Ownership lives in the ``member_color_roles`` table (guild, user -> role id); the name is cosmetic. Legacy
roles named ``color-<user_id>`` are still recognized by name and get bound (and renamed) the next
time their owner changes color, so no bulk migration is needed. A row whose role was deleted by
hand is simply stale: lookups ignore it and the next write replaces or removes it.

Every mutation (create / recolor / remove / purge) runs under a per-guild ``asyncio.Lock`` so two
interactions (e.g. a double click on a favorites button, or ``/force set`` racing ``/set``) cannot
create two roles for the same member.
"""

import asyncio
import logging
import re
from dataclasses import dataclass
from typing import Optional, Tuple, cast

import discord

from constants import (
    COLOR_ROLE_NAME_PREFIX,
    COLOR_ROLE_PATTERN,
    COLOR_ROLE_PREFIX,
    DISCORD_ROLE_LIMIT,
    DISCORD_ROLE_NAME_MAX,
    HTTP_MAX_ROLES_REACHED,
)
from database import model

logger = logging.getLogger(__name__)

TOPROLE_MODE_AUTO = "auto"
TOPROLE_MODE_CUSTOM = "custom"
TOPROLE_MODE_OFF = "off"
TOPROLE_MODES = {TOPROLE_MODE_AUTO, TOPROLE_MODE_CUSTOM, TOPROLE_MODE_OFF}

_color_role_re = re.compile(COLOR_ROLE_PATTERN)
_guild_locks: dict[int, asyncio.Lock] = {}

# (primary, secondary, tertiary): a solid color, a gradient, or the holographic style.
Colors = Tuple[int, Optional[int], Optional[int]]


class ColorRoleError(Exception):
    """A predictable failure with a user-facing message in ``messages.yml``."""

    message_key = "exception"


class RoleLimitReached(ColorRoleError):
    message_key = "err_role_limit"


@dataclass
class ApplyResult:
    role: discord.Role
    changed: bool                  # role created or recolored (position moves don't count)
    prev_colors: Optional[Colors]  # colors before the change; None for a freshly created role


def get_guild_lock(guild_id: int) -> asyncio.Lock:
    lock = _guild_locks.get(guild_id)
    if lock is None:
        lock = _guild_locks[guild_id] = asyncio.Lock()
    return lock


def color_role_name(member: discord.Member) -> str:
    return f"{COLOR_ROLE_NAME_PREFIX}{member.display_name}"[:DISCORD_ROLE_NAME_MAX]


def legacy_color_role_name(user_id: int) -> str:
    return f"{COLOR_ROLE_PREFIX}{user_id}"


def is_legacy_color_role(role: discord.Role) -> bool:
    return _color_role_re.match(role.name) is not None


def looks_like_color_role(role: discord.Role) -> bool:
    """Cheap name-only pre-filter (no DB): a legacy name or the ``🎨`` prefix. Not authoritative."""
    return is_legacy_color_role(role) or role.name.startswith(COLOR_ROLE_NAME_PREFIX)


async def _lookup_color_role(
    db, guild: discord.Guild, user_id: int, roles: Optional[list[discord.Role]] = None
) -> Tuple[Optional[discord.Role], Optional[dict]]:
    """``(role, row)``: the bound role if it still exists, else the legacy ``color-<id>`` role."""
    roles = roles if roles is not None else guild.roles
    row = await db.select_one(model.ColorRoles, {"guild_id": guild.id, "user_id": user_id})
    if row is not None:
        role = discord.utils.get(roles, id=row["role_id"])
        if role is not None:
            return role, row
    return discord.utils.get(roles, name=legacy_color_role_name(user_id)), row


async def find_color_role(
    db, guild: discord.Guild, user_id: int, roles: Optional[list[discord.Role]] = None
) -> Optional[discord.Role]:
    """The member's color role, or None. Read-only."""
    role, _ = await _lookup_color_role(db, guild, user_id, roles)
    return role


async def color_role_ids(db, guild: discord.Guild, roles: list[discord.Role]) -> set[int]:
    """Ids of every existing color role in the guild: bound ones plus unmigrated legacy ones."""
    existing = {role.id for role in roles}
    bound = {row["role_id"] for row in await db.select(model.ColorRoles, {"guild_id": guild.id})}
    legacy = {role.id for role in roles if is_legacy_color_role(role)}
    return (bound & existing) | legacy


def role_colors(role: discord.Role) -> Colors:
    return (
        role.color.value,
        role.secondary_color.value if role.secondary_color else None,
        role.tertiary_color.value if role.tertiary_color else None,
    )


def get_toprole_mode(guild_obj: Optional[dict]) -> str:
    if not isinstance(guild_obj, dict):
        return TOPROLE_MODE_OFF

    mode = guild_obj.get("mode")
    if mode in TOPROLE_MODES:
        return mode

    return TOPROLE_MODE_CUSTOM if guild_obj.get("role") else TOPROLE_MODE_OFF


async def get_bot_member(guild: discord.Guild, bot_user_id: int) -> Optional[discord.Member]:
    if guild.me is not None:
        return guild.me
    try:
        return await guild.fetch_member(bot_user_id)
    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
        return None


async def get_max_manageable_role_position(
    guild: discord.Guild,
    bot_user_id: int,
    roles: Optional[list[discord.Role]] = None,
) -> int:
    """Highest position the bot can place a role at: one below its own top role."""
    bot_member = await get_bot_member(guild, bot_user_id)
    if bot_member is None:
        return 1

    if roles is None:
        roles = await guild.fetch_roles()

    role_lookup = {role.id: role for role in roles}
    bot_role_ids = getattr(bot_member, "_roles", ())
    bot_roles = [role_lookup[role_id] for role_id in bot_role_ids if role_id in role_lookup]
    if not bot_roles:
        return 1

    top_role = max(bot_roles)
    return max(1, top_role.position - 1)


async def get_role_position(
    db,
    guild: discord.Guild,
    bot_user_id: int,
    roles: Optional[list[discord.Role]] = None,
) -> int:
    """Target position for the *top* of the color-role block, according to the guild's mode."""
    guild_obj = await db.select_one(model.Guilds, {"server": guild.id})
    mode = get_toprole_mode(guild_obj)
    if mode == TOPROLE_MODE_OFF:
        return 1

    if roles is None:
        roles = await guild.fetch_roles()

    max_manageable_position = await get_max_manageable_role_position(guild, bot_user_id, roles=roles)
    if mode == TOPROLE_MODE_AUTO:
        return max_manageable_position

    top_role = discord.utils.get(roles, id=guild_obj.get("role", 0)) if isinstance(guild_obj, dict) else None
    if top_role is None or top_role.is_default():
        return 1

    role_position = max(1, top_role.position - 1)
    return min(role_position, max_manageable_position)


async def move_roles_to_block(
    guild: discord.Guild,
    role_ids: set[int],
    top_position: int,
    reason: str = "HueTweaker color role placement",
    roles: Optional[list[discord.Role]] = None,
    max_position: Optional[int] = None,
) -> bool:
    """Arrange ``role_ids`` as one contiguous block whose highest role sits at ``top_position``
    (or as high as the count allows). Idempotent: nothing is sent when the block is already in
    place. Roles above ``max_position`` (the bot's reach) are never touched. Returns True when
    a request was made."""
    if not role_ids:
        return False

    source_roles = roles if roles is not None else await guild.fetch_roles()
    all_roles = sorted(source_roles)
    non_default = [r for r in all_roles if not r.is_default()]

    moving = [r for r in non_default if r.id in role_ids]
    static = [r for r in non_default if r.id not in role_ids]

    if not moving:
        return False

    insert_idx = max(0, min(top_position - len(moving), len(static)))
    new_order = [*static[:insert_idx], *moving, *static[insert_idx:]]

    payload: dict[discord.abc.Snowflake, int] = {}
    for new_idx, item in enumerate(new_order, start=1):
        if item.position == new_idx:
            continue
        if max_position is not None and (item.position > max_position or new_idx > max_position):
            continue
        payload[item] = new_idx

    if not payload:
        return False

    await guild.edit_role_positions(
        cast(dict[discord.abc.Snowflake, int], payload),
        reason=reason,
    )
    return True


async def place_color_roles(
    db,
    guild: discord.Guild,
    bot_user_id: int,
    roles: Optional[list[discord.Role]] = None,
) -> bool:
    """Keep all color roles of the guild in one block at the configured position."""
    if roles is None:
        roles = await guild.fetch_roles()
    block_ids = await color_role_ids(db, guild, roles)
    if not block_ids:
        return False
    top_position = await get_role_position(db, guild, bot_user_id, roles=roles)
    max_position = await get_max_manageable_role_position(guild, bot_user_id, roles=roles)
    return await move_roles_to_block(guild, block_ids, top_position, roles=roles, max_position=max_position)


def _color_kwargs(primary_val: int, secondary_val: Optional[int], tertiary_val: Optional[int] = None) -> dict:
    # Always send all three, so a switch to a solid color also clears the gradient/holographic parts.
    return {
        "color": discord.Color(primary_val),
        "secondary_color": discord.Color(secondary_val) if secondary_val is not None else None,
        "tertiary_color": discord.Color(tertiary_val) if tertiary_val is not None else None,
    }


async def apply_color_role(
    guild: discord.Guild,
    member: discord.Member,
    primary_val: int,
    secondary_val: Optional[int],
    db,
    bot_user_id: int,
    tertiary_val: Optional[int] = None,
) -> ApplyResult:
    """Give ``member`` the color: create or recolor their color role (renaming a legacy or outdated
    name in the same edit), bind it in ``member_color_roles``, assign it, and keep the color-role block
    positioned. ``changed`` is False when the role already had these colors (a rename alone is not
    a change). ``tertiary_val`` is only valid for the holographic style (``HOLOGRAPHIC_COLORS``)."""
    async with get_guild_lock(guild.id):
        roles = await guild.fetch_roles()
        role, row = await _lookup_color_role(db, guild, member.id, roles)
        new_colors: Colors = (primary_val, secondary_val, tertiary_val)
        name = color_role_name(member)
        changed = False
        prev_colors: Optional[Colors] = None

        if role is None:
            if len(roles) >= DISCORD_ROLE_LIMIT:
                raise RoleLimitReached()
            try:
                role = await guild.create_role(
                    name=name,
                    reason="HueTweaker color role",
                    **_color_kwargs(*new_colors),
                )
            except discord.HTTPException as e:
                if e.code == HTTP_MAX_ROLES_REACHED:
                    raise RoleLimitReached() from e
                raise
            try:
                await _bind_color_role(db, guild.id, member.id, role.id, row)
            except Exception:
                # Without the row nothing would find this role again; don't leave an orphan behind.
                await role.delete(reason="HueTweaker: could not save color role")
                raise
            changed = True
            roles = await guild.fetch_roles()
        else:
            if row is None or row["role_id"] != role.id:
                await _bind_color_role(db, guild.id, member.id, role.id, row)
            edits: dict = {}
            current_colors = role_colors(role)
            if current_colors != new_colors:
                prev_colors = current_colors
                edits.update(_color_kwargs(*new_colors))
                changed = True
            if role.name != name:
                edits["name"] = name
            if edits:
                updated_role = await role.edit(reason="HueTweaker color change", **edits)
                if updated_role is not None:
                    role = updated_role

        if discord.utils.get(member.roles, id=role.id) is None:
            await member.add_roles(role, reason="HueTweaker color role")

        await place_color_roles(db, guild, bot_user_id, roles=roles)

        live_role = discord.utils.get(guild.roles, id=role.id)
        return ApplyResult(role=live_role or role, changed=changed, prev_colors=prev_colors)


async def _bind_color_role(db, guild_id: int, user_id: int, role_id: int, row: Optional[dict]) -> None:
    if row is None:
        await db.create(model.ColorRoles, {"guild_id": guild_id, "user_id": user_id, "role_id": role_id})
    else:
        await db.update(model.ColorRoles, {"guild_id": guild_id, "user_id": user_id}, {"role_id": role_id})


async def revert_color_role(guild: discord.Guild, role_id: int, prev_colors: Optional[Colors]) -> Optional[discord.Role]:
    """Undo a color change. ``prev_colors=None`` means the role did not exist before: delete it
    (its ``member_color_roles`` row goes stale and is replaced on the next change).
    Returns the role (None when it was deleted or no longer exists)."""
    async with get_guild_lock(guild.id):
        role = guild.get_role(role_id)
        if role is None:
            return None
        if prev_colors is None:
            await role.delete(reason="HueTweaker: undo color change")
            return None
        updated = await role.edit(reason="HueTweaker: undo color change", **_color_kwargs(*prev_colors))
        return updated or role


async def remove_color_role(db, guild: discord.Guild, user_id: int, reason: str = "HueTweaker: color removed") -> bool:
    """Delete the member's color role (deleting a role also unassigns it) and its ``member_color_roles``
    row, stale or not. Returns False if the member had no role."""
    async with get_guild_lock(guild.id):
        role, row = await _lookup_color_role(db, guild, user_id)
        removed = False
        if role is not None:
            try:
                await role.delete(reason=reason)
                removed = True
            except discord.NotFound:
                pass
        if row is not None:
            await db.delete(model.ColorRoles, {"guild_id": guild.id, "user_id": user_id})
        return removed


@dataclass
class PurgeResult:
    deleted: int = 0
    failed: int = 0


async def purge_color_roles(db, guild: discord.Guild, reason: str = "HueTweaker: purge") -> PurgeResult:
    """Delete every color role (bound and legacy). Roles the bot cannot manage are counted as failed
    and keep their ``member_color_roles`` row; all other rows of the guild are removed."""
    result = PurgeResult()
    async with get_guild_lock(guild.id):
        roles = list(guild.roles)
        purge_ids = await color_role_ids(db, guild, roles)
        kept: list[int] = []
        for role in roles:
            if role.id not in purge_ids:
                continue
            try:
                await role.delete(reason=reason)
            except discord.NotFound:
                continue
            except discord.Forbidden:
                result.failed += 1
                kept.append(role.id)
            except discord.HTTPException as e:
                logger.warning("Purge in guild %s: could not delete %s: %s", guild.id, role.name, e)
                result.failed += 1
                kept.append(role.id)
            else:
                result.deleted += 1

        for row in await db.select(model.ColorRoles, {"guild_id": guild.id}):
            if row["role_id"] not in kept:
                await db.delete(model.ColorRoles, {"id": row["id"]})
    return result


@dataclass
class RefactorResult:
    renamed: int = 0
    orphans: int = 0   # legacy roles whose owner left the server: deleted
    skipped: int = 0   # owner already has another bound color role
    failed: int = 0    # roles above the bot or other Discord errors


async def _members_by_id(guild: discord.Guild, user_ids: list[int]) -> dict[int, discord.Member]:
    """Resolve members in batches of 100 over the gateway (no per-member REST call)."""
    found: dict[int, discord.Member] = {}
    missing: list[int] = []
    for uid in user_ids:
        member = guild.get_member(uid)
        if member is None:
            missing.append(uid)
        else:
            found[uid] = member
    for i in range(0, len(missing), 100):
        batch = missing[i:i + 100]
        for member in await guild.query_members(user_ids=batch, limit=len(batch), cache=True):
            found[member.id] = member
    return found


async def refactor_legacy_roles(db, guild: discord.Guild, reason: str = "HueTweaker: color role rename") -> RefactorResult:
    """Temporary (``/refactor``): bind every legacy ``color-<user_id>`` role of the guild and rename it
    to ``🎨 <display name>`` now instead of on its owner's next color change. Roles whose owner left the
    server are deleted, as the leaver cleanup would have done. The guild lock is taken per role so
    ``/set`` keeps working while a large guild is processed."""
    result = RefactorResult()
    legacy = [role for role in await guild.fetch_roles() if is_legacy_color_role(role)]
    if not legacy:
        return result

    owners = {role.id: int(role.name.split("-", 1)[1]) for role in legacy}
    members = await _members_by_id(guild, list(set(owners.values())))

    for role in legacy:
        user_id = owners[role.id]
        async with get_guild_lock(guild.id):
            try:
                member = members.get(user_id)
                if member is None:
                    await role.delete(reason="HueTweaker: owner left the server")
                    result.orphans += 1
                    continue
                bound, row = await _lookup_color_role(db, guild, user_id)
                if row is not None and bound is not None and bound.id != role.id:
                    result.skipped += 1
                    continue
                # Bind first: a renamed role without a row could no longer be found by its legacy name.
                await _bind_color_role(db, guild.id, user_id, role.id, row)
                await role.edit(name=color_role_name(member), reason=reason)
                result.renamed += 1
            except discord.NotFound:
                continue
            except discord.HTTPException as e:
                logger.warning("Refactor in guild %s: could not update %s: %s", guild.id, role.name, e)
                result.failed += 1
    return result
