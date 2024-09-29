import datetime
import logging

import discord
from discord import app_commands, Embed
from discord.ext import commands

from bot_init import bot,messages
from utils.lang_loader import load_lang


class VoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="vote", description="View links to vote")
    async def vote(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        lang = load_lang(str(interaction.locale))
        try:
            embed: Embed = discord.Embed(title=lang['vote_title'].format(bot.user.name), description=f"",
                                         color=4539717, timestamp=datetime.datetime.now())
            await interaction.response.defer(ephemeral=True)
            embed.description = lang['vote_desc']
            embed.add_field(name=f"", value=lang['vote_topgg'], inline=False)
            embed.add_field(name=f"", value=lang['vote_dbl'], inline=False)

        except Exception as e:
            embed.clear_fields()
            embed.description = lang['exception']
            logging.critical(f"{interaction.user.name}[{interaction.locale}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name} by kaaroll99", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user.name}[{interaction.user.id}] issued bot command: /vote")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoteCog(bot))
