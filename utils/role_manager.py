import logging
from typing import Optional, Tuple

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


def get_max_manageable_role_position(guild: discord.Guild) -> int:
    bot_member = guild.me
    if bot_member is None or bot_member.top_role.is_default():
        return 1

    return max(1, bot_member.top_role.position - 1)


async def get_role_position(db, guild: discord.Guild) -> int:
    guild_obj = await db.select_one(model.Guilds, {"server": guild.id})
    mode = get_toprole_mode(guild_obj)
    if mode == TOPROLE_MODE_OFF:
        return 1

    max_manageable_position = get_max_manageable_role_position(guild)
    if mode == TOPROLE_MODE_AUTO:
        return max_manageable_position

    top_role = guild.get_role(guild_obj.get("role", 0)) if isinstance(guild_obj, dict) else None
    if top_role is None or top_role.is_default():
        return 1

    role_position = max(1, top_role.position - 1)
    return min(role_position, max_manageable_position)


def get_color_role(guild: discord.Guild, user_id: int) -> Optional[discord.Role]:
    return discord.utils.get(guild.roles, name=f"{COLOR_ROLE_PREFIX}{user_id}")


async def create_or_update_color_role(
    guild: discord.Guild,
    user_id: int,
    primary_val: int,
    secondary_val: Optional[int],
    db,
) -> Tuple[discord.Role, bool, Optional[Tuple[Optional[int], Optional[int]]]]:
    role = get_color_role(guild, user_id)
    role_position = await get_role_position(db, guild)
    new_colors = (primary_val, secondary_val)

    if role is None:
        role = await guild.create_role(
            name=f"{COLOR_ROLE_PREFIX}{user_id}",
            color=discord.Color(primary_val),
            secondary_color=discord.Color(secondary_val) if secondary_val is not None else None,
        )
        if role.position != role_position:
            await role.edit(position=role_position)
        return role, True, None

    current_colors = (
        role.color.value if role.color else None,
        role.secondary_color.value if role.secondary_color else None,
    )
    position_changed = role.position != role_position
    colors_changed = current_colors != new_colors

    if colors_changed or position_changed:
        prev_colors = current_colors if colors_changed else None
        edit_kwargs = {}

        if colors_changed:
            edit_kwargs["color"] = discord.Color(primary_val)
            edit_kwargs["secondary_color"] = discord.Color(secondary_val) if secondary_val is not None else None
        if position_changed:
            edit_kwargs["position"] = role_position

        await role.edit(**edit_kwargs)
        return role, True, prev_colors

    return role, False, None


async def assign_role_if_missing(member: discord.Member, role: discord.Role, reason: str = "HueTweaker color role") -> None:
    if role not in member.roles:
        await member.add_roles(role, reason=reason)
