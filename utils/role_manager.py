import logging
from typing import Optional, Tuple, cast

import discord

from constants import COLOR_ROLE_PREFIX
from database import model

logger = logging.getLogger(__name__)

TOPROLE_MODE_AUTO = "auto"
TOPROLE_MODE_CUSTOM = "custom"
TOPROLE_MODE_OFF = "off"
TOPROLE_MODES = {TOPROLE_MODE_AUTO, TOPROLE_MODE_CUSTOM, TOPROLE_MODE_OFF}


def get_toprole_mode(guild_obj: Optional[dict]) -> str:
    if not isinstance(guild_obj, dict):
        return TOPROLE_MODE_OFF

    mode = guild_obj.get("mode")
    if mode in TOPROLE_MODES:
        return mode

    return TOPROLE_MODE_CUSTOM if guild_obj.get("role") else TOPROLE_MODE_OFF


async def get_bot_member(guild: discord.Guild, bot_user_id: int) -> Optional[discord.Member]:
    try:
        return await guild.fetch_member(bot_user_id)
    except (discord.Forbidden, discord.HTTPException, discord.NotFound):
        return None


async def get_max_manageable_role_position(
    guild: discord.Guild,
    bot_user_id: int,
    roles: Optional[list[discord.Role]] = None,
) -> int:
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


async def move_role_to_position(
    guild: discord.Guild,
    role: discord.Role,
    position: int,
    reason: str = "HueTweaker color role placement",
) -> None:
    if role.is_default() or role.position == position:
        return

    roles = sorted(await guild.fetch_roles())
    change_range = range(min(role.position, position), max(role.position, position) + 1)
    roles_in_range = [item for item in roles[1:] if item.position in change_range and item.id != role.id]

    if role.position > position:
        ordered_roles = [role, *roles_in_range]
    else:
        ordered_roles = [*roles_in_range, role]

    payload = {item: next_position for item, next_position in zip(ordered_roles, change_range)}
    await guild.edit_role_positions(
        cast(dict[discord.abc.Snowflake, int], payload),
        reason=reason,
    )


def get_color_role(guild: discord.Guild, user_id: int) -> Optional[discord.Role]:
    return discord.utils.get(guild.roles, name=f"{COLOR_ROLE_PREFIX}{user_id}")


async def create_or_update_color_role(
    guild: discord.Guild,
    user_id: int,
    primary_val: int,
    secondary_val: Optional[int],
    db,
    bot_user_id: int,
) -> Tuple[discord.Role, bool, Optional[Tuple[Optional[int], Optional[int]]]]:
    roles = await guild.fetch_roles()
    role = discord.utils.get(roles, name=f"{COLOR_ROLE_PREFIX}{user_id}")
    role_position = await get_role_position(db, guild, bot_user_id, roles=roles)
    new_colors = (primary_val, secondary_val)

    if role is None:
        role = await guild.create_role(
            name=f"{COLOR_ROLE_PREFIX}{user_id}",
            color=discord.Color(primary_val),
            secondary_color=discord.Color(secondary_val) if secondary_val is not None else None,
        )
        if role.position != role_position:
            await move_role_to_position(guild, role, role_position)
        return role, True, None

    current_colors = (
        role.color.value if role.color else None,
        role.secondary_color.value if role.secondary_color else None,
    )
    position_changed = role.position != role_position
    colors_changed = current_colors != new_colors

    if colors_changed or position_changed:
        prev_colors = current_colors if colors_changed else None

        if colors_changed:
            updated_role = await role.edit(
                color=discord.Color(primary_val),
                secondary_color=discord.Color(secondary_val) if secondary_val is not None else None,
            )
            if updated_role is not None:
                role = updated_role
        if position_changed:
            await move_role_to_position(guild, role, role_position)
        return role, True, prev_colors

    return role, False, None


async def assign_role_if_missing(member: discord.Member, role: discord.Role, reason: str = "HueTweaker color role") -> None:
    if role not in member.roles:
        await member.add_roles(role, reason=reason)
