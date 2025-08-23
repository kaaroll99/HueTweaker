import logging

import discord
from discord.ext import commands

from database import model

logger = logging.getLogger(__name__)


class JoinListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            role = discord.utils.get(member.guild.roles, name=f"color-{member.id}")
            if role is not None:
                await role.delete()
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logger.info("Bot has been added to guild: %s", guild.name)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        logger.info("Bot has been removed from guild: %s", guild.name)
        with self.db as db_session:
            db_session.delete(model.guilds_class("guilds"), {"server": guild.id})


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
