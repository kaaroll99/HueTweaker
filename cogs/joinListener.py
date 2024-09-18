import logging
from datetime import datetime

import discord
from discord.ext import commands

from bot_init import bot
from config import db
from database import model
from utils.data_loader import load_yml

config_file = load_yml('assets/config.yml')


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
    async def on_guild_join(self, guild):
        try:
            channel = bot.get_channel(config_file['io_channel'])
            if channel and guild.member_count is not None:
                logging.info(f"Bot has been added to guild: {guild.id} (mem: {guild.member_count})")
                owner_name = guild.owner.name if guild.owner else "-"
                embed = discord.Embed(title=f"", description=f"Bot has been added to guild (****)\n"
                                                             f"> **Guild:** {guild.name}\n"
                                                             f"> **ID:** `{guild.id}`\n"
                                                             f"> **Members:** `{guild.member_count}` `[{owner_name}]`",
                                      color=0x23A55A, timestamp=datetime.now())
                await channel.send(embed=embed)
            else:
                logging.warning(f"I/O channel not found or member_count is None.")
        except Exception as e:
            logging.warning(f"Log channel error - {e.__class__.__name__}: {e}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        with db as db_session:
            db_session.delete(model.guilds_class("guilds"), {"server": guild.id})
        try:
            channel = bot.get_channel(config_file['io_channel'])
            if channel and guild.member_count is not None:
                logging.info(f"Bot has been removed from guild: {guild.id} (mem: {guild.member_count})")
                owner_name = guild.owner.name if guild.owner else "-"
                embed = discord.Embed(title=f"",
                                      description=f"Bot has been removed from guild (****)\n"
                                                  f"> **Guild:** {guild.name}\n"
                                                  f"> **ID:** `{guild.id}`\n"
                                                  f"> **Members:** `{guild.member_count}` `[{owner_name}]`",
                                      color=0xF23F42, timestamp=datetime.now())
                await channel.send(embed=embed)
            else:
                logging.warning(f"Log channel not found or member_count is None.")
        except Exception as e:
            logging.warning(f"Log channel error - {e.__class__.__name__}: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
