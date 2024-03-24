import logging
import discord
from discord.ext import commands
import config
from database import database, model
from config import bot

messages_file = config.load_yml('assets/messages.yml')
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
        logging.info(f"Bot has been added to guild: {guild.id}(mem: {guild.member_count})")
        try:
            channel = bot.get_channel(config_file['io_channel'])
            if channel is not None:
                owner_name = guild.owner.name if guild.owner else "-"
                embed = discord.Embed(title=f"", description=f"**Bot has been added to guild ({len(bot.guilds)})**\n"
                                                             f"> ID: `{guild.id}`\n"
                                                             f"> Members: `{guild.member_count} ({owner_name})`\n"
                                                             f"> Lang: `{guild.preferred_locale}`",
                                      color=0x23A55A)
                embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                await channel.send(embed=embed)
            else:
                logging.warning(f"I/O channel not found.")
        except Exception as e:
            logging.warning(f"I/O channel error - {e.__class__.__name__}: {e}")

    @commands.Cog.listener()
    async def on_guild_remove(self, guild):
        db = database.Database(url=f"sqlite:///databases/guilds.db")
        db.connect()
        db.delete(model.guilds_class("guilds"), {"server": guild.id})
        logging.info(f"Bot has been removed from guild: {guild.id}(mem: {guild.member_count})")
        try:
            channel = bot.get_channel(config_file['io_channel'])
            if channel is not None:
                embed = discord.Embed(title=f"", description=f"**Bot has been removed from guild ({len(bot.guilds)})**\n"
                                                             f"> ID: `{guild.id}`\n"
                                                             f"> Members: `{guild.member_count}`\n"
                                                             f"> Lang: `{guild.preferred_locale}`", color=0xF23F42)
                embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                await channel.send(embed=embed)
            else:
                logging.warning(f"I/O channel not found.")
        except Exception as e:
            logging.warning(f"I/O channel error - {e.__class__.__name__}: {e}")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
