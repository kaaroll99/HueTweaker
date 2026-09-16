import logging

import discord
from discord.ext import commands

from constants import COLOR_ROLE_PREFIX
from database import model

logger = logging.getLogger(__name__)


class JoinListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db

    @commands.Cog.listener()
    async def on_raw_member_remove(self, payload: discord.RawMemberRemoveEvent):
        user_id = payload.user.id
        guild = self.bot.get_guild(payload.guild_id)
        try:
            if guild is not None:
                role = discord.utils.get(guild.roles, name=f"{COLOR_ROLE_PREFIX}{user_id}")
                if role is not None:
                    await role.delete(reason="HueTweaker: member left the server")
                    logger.info("Deleted color role of user %s who left guild %s", user_id, payload.guild_id)

            await self.db.delete(model.History, {"user_id": user_id, "guild_id": payload.guild_id})

        except discord.NotFound:
            pass
        except discord.HTTPException as e:
            logger.warning("Cleanup after user %s left guild %s failed: %s", user_id, payload.guild_id, e)

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info("Bot has been added to guild: %s", guild.name)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logger.info("Bot has been removed from guild: %s", guild.name)
        await self.db.delete(model.Guilds, {"server": guild.id})
        await self.db.delete_all(model.History, {"guild_id": guild.id})


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
