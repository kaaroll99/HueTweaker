import logging
from datetime import datetime

import discord
from discord.ext import commands

from bot import db
from database import model
from utils.data_loader import load_yml


class JoinListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        try:
            role = discord.utils.get(member.guild.roles, name=f"color-{member.id}")
            if role is not None:
                await role.delete()
        except discord.HTTPException:
            pass

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with db as db_session:
            db_session.delete(model.guilds_class("guilds"), {"server": guild.id})


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
