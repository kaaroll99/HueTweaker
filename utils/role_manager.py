"""Bot-managed color roles: one ``color-<user_id>`` role per member.

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

from constants import COLOR_ROLE_PATTERN, COLOR_ROLE_PREFIX, DISCORD_ROLE_LIMIT, HTTP_MAX_ROLES_REACHED
from database import model

logger = logging.getLogger(__name__)

TOPROLE_MODE_AUTO = "auto"
TOPROLE_MODE_CUSTOM = "custom"
TOPROLE_MODE_OFF = "off"
TOPROLE_MODES = {TOPROLE_MODE_AUTO, TOPROLE_MODE_CUSTOM, TOPROLE_MODE_OFF}

_color_role_re = re.compile(COLOR_ROLE_PATTERN)
_guild_locks: dict[int, asyncio.Lock] = {}

Colors = Tuple[int, Optional[int]]


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


def color_role_name(user_id: int) -> str:
    return f"{COLOR_ROLE_PREFIX}{user_id}"


def is_color_role(role: discord.Role) -> bool:
    return _color_role_re.match(role.name) is not None


def get_color_role(guild: discord.Guild, user_id: int) -> Optional[discord.Role]:
    return discord.utils.get(guild.roles, name=color_role_name(user_id))


def role_colors(role: discord.Role) -> Colors:
    return role.color.value, (role.secondary_color.value if role.secondary_color else None)


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
    color_role_ids = {role.id for role in roles if is_color_role(role)}
    if not color_role_ids:
        return False
    top_position = await get_role_position(db, guild, bot_user_id, roles=roles)
    max_position = await get_max_manageable_role_position(guild, bot_user_id, roles=roles)
    return await move_roles_to_block(guild, color_role_ids, top_position, roles=roles, max_position=max_position)


def _color_kwargs(primary_val: int, secondary_val: Optional[int]) -> dict:
    return {
        "color": discord.Color(primary_val),
        "secondary_color": discord.Color(secondary_val) if secondary_val is not None else None,
    }


async def apply_color_role(
    guild: discord.Guild,
    member: discord.Member,
    primary_val: int,
    secondary_val: Optional[int],
    db,
    bot_user_id: int,
) -> ApplyResult:
    """Give ``member`` the color: create or recolor their ``color-<id>`` role, assign it, and keep
    the color-role block positioned. ``changed`` is False when the role already had these colors."""
    async with get_guild_lock(guild.id):
        roles = await guild.fetch_roles()
        role = discord.utils.get(roles, name=color_role_name(member.id))
        new_colors: Colors = (primary_val, secondary_val)
        changed = False
        prev_colors: Optional[Colors] = None

        if role is None:
            if len(roles) >= DISCORD_ROLE_LIMIT:
                raise RoleLimitReached()
            try:
                role = await guild.create_role(
                    name=color_role_name(member.id),
                    reason="HueTweaker color role",
                    **_color_kwargs(primary_val, secondary_val),
                )
            except discord.HTTPException as e:
                if e.code == HTTP_MAX_ROLES_REACHED:
                    raise RoleLimitReached() from e
                raise
            changed = True
            roles = await guild.fetch_roles()
        else:
            current_colors = role_colors(role)
            if current_colors != new_colors:
                prev_colors = current_colors
                updated_role = await role.edit(reason="HueTweaker color change", **_color_kwargs(primary_val, secondary_val))
                if updated_role is not None:
                    role = updated_role
                changed = True

        if discord.utils.get(member.roles, id=role.id) is None:
            await member.add_roles(role, reason="HueTweaker color role")

        await place_color_roles(db, guild, bot_user_id, roles=roles)

        live_role = discord.utils.get(guild.roles, id=role.id)
        return ApplyResult(role=live_role or role, changed=changed, prev_colors=prev_colors)


async def revert_color_role(guild: discord.Guild, role_id: int, prev_colors: Optional[Colors]) -> Optional[discord.Role]:
    """Undo a color change. ``prev_colors=None`` means the role did not exist before: delete it.
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


async def remove_color_role(guild: discord.Guild, user_id: int, reason: str = "HueTweaker: color removed") -> bool:
    """Delete the member's color role (deleting a role also unassigns it). Returns False if none."""
    async with get_guild_lock(guild.id):
        role = get_color_role(guild, user_id)
        if role is None:
            return False
        try:
            await role.delete(reason=reason)
        except discord.NotFound:
            return False
        return True


@dataclass
class PurgeResult:
    deleted: int = 0
    failed: int = 0


async def purge_color_roles(guild: discord.Guild, reason: str = "HueTweaker: purge") -> PurgeResult:
    """Delete every ``color-<user_id>`` role. Roles the bot cannot manage are counted as failed."""
    result = PurgeResult()
    async with get_guild_lock(guild.id):
        for role in list(guild.roles):
            if not is_color_role(role):
                continue
            try:
                await role.delete(reason=reason)
                result.deleted += 1
            except discord.NotFound:
                continue
            except discord.Forbidden:
                result.failed += 1
            except discord.HTTPException as e:
                logger.warning("Purge in guild %s: could not delete %s: %s", guild.id, role.name, e)
                result.failed += 1
    return result
