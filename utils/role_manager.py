import logging
from typing import Optional, Tuple

import discord

from constants import COLOR_ROLE_PREFIX
from database import model

logger = logging.getLogger(__name__)


async def get_role_position(db, guild: discord.Guild) -> int:
    guild_obj = await db.select_one(model.Guilds, {"server": guild.id})
    if guild_obj:
        top_role = discord.utils.get(guild.roles, id=guild_obj["role"])
        if top_role:
            return max(1, top_role.position - 1)
    return 1


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
        if role_position > 1:
            await role.edit(position=role_position)
        return role, True, None

    current_colors = (
        role.color.value if role.color else None,
        role.secondary_color.value if role.secondary_color else None,
    )

    if current_colors != new_colors:
        prev_colors = current_colors
        await role.edit(
            color=discord.Color(primary_val),
            secondary_color=discord.Color(secondary_val) if secondary_val is not None else None,
            position=role_position,
        )
        return role, True, prev_colors

    return role, False, None


async def assign_role_if_missing(member: discord.Member, role: discord.Role, reason: str = "HueTweaker color role") -> None:
    if role not in member.roles:
        await member.add_roles(role, reason=reason)
