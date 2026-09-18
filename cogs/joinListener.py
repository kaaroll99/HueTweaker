import logging

import discord
from discord.ext import commands

from database import model
from utils.role_manager import TOPROLE_MODE_CUSTOM, TOPROLE_MODE_OFF, is_color_role, remove_color_role

logger = logging.getLogger(__name__)


class JoinListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        """Fires for every leaver, cached or not (``chunk_guilds_at_startup=False``)."""
        user_id = payload.user.id
        guild = self.bot.get_guild(payload.guild_id)
        try:
            if guild is not None and await remove_color_role(guild, user_id, reason="HueTweaker: member left the server"):
                logger.info("Deleted color role of user %s who left guild %s", user_id, payload.guild_id)
            await self.db.delete(model.History, {"user_id": user_id, "guild_id": payload.guild_id})
        except Exception as e:
            logger.warning("Cleanup after user %s left guild %s failed: %r", user_id, payload.guild_id, e)

    @commands.Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        """If the reference role of ``custom`` placement is deleted, fall back to ``off``."""
        if is_color_role(role):
            return
        try:
            guild_obj = await self.db.select_one(model.Guilds, {"server": role.guild.id})
            if guild_obj and guild_obj.get("mode") == TOPROLE_MODE_CUSTOM and guild_obj.get("role") == role.id:
                await self.db.update(model.Guilds, {"server": role.guild.id}, {"mode": TOPROLE_MODE_OFF, "role": 0})
                logger.info("Reference role %s deleted in guild %s; placement mode reset to off", role.id, role.guild.id)
        except Exception as e:
            logger.warning("Could not check toprole reference after role %s was deleted: %r", role.id, e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info("Bot has been added to guild: %s", guild.name)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logger.info("Bot has been removed from guild: %s", guild.name)
        try:
            await self.db.delete_all(model.Guilds, {"server": guild.id})
            await self.db.delete_all(model.History, {"guild_id": guild.id})
            await self.db.delete_all(model.Select, {"server_id": guild.id})
        except Exception as e:
            logger.warning("Cleanup after leaving guild %s failed: %r", guild.id, e)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
