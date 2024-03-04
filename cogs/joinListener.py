import logging
import discord
from discord.ext import commands
from discord import app_commands, Embed
import config
import datetime
from config import bot
from database import database, model

messages_file = config.load_yml('messages.yml')
config_file = config.load_yml('config.yml')


class JoinListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        role = discord.utils.get(member.guild.roles, name=f"color-{member.id}")
        if role is not None:
            await role.delete()

    @commands.Cog.listener()
    async def on_guild_join(self, guild):
        logging.info(f"Bot has been added to guild: {guild.name}(id={guild.id}, mem={guild.member_count})")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        db = database.Database(url=f"sqlite:///databases/guilds.db")
        db.connect()
        db.delete(model.guilds_class("guilds"), {"server": guild.id})
        logging.info(f"Bot has been removed from guild: {guild.name}(id={guild.id}, mem={guild.member_count})")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
