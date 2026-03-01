import datetime
import logging

import discord
from discord import app_commands
from discord.ext import commands

from constants import BANNER_URL

logger = logging.getLogger(__name__)


class VoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.msg = bot.messages

    @app_commands.command(name="vote", description="View links to vote")
    async def vote(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(
            title=self.msg['vote_title'].format(self.bot.user.name),
            description="",
            color=4539717,
            timestamp=datetime.datetime.now(),
        )
        try:
            await interaction.response.defer(ephemeral=True)
            embed.description = self.msg['vote_desc']
            embed.add_field(name="", value=self.msg['vote_topgg'], inline=False)
            embed.add_field(name="", value=self.msg['vote_dbl'], inline=False)

        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.locale, e)
        finally:
            embed.set_footer(text=f"{self.bot.user.name} by kaaroll99", icon_url=self.bot.user.avatar)
            embed.set_image(url=BANNER_URL)
            await interaction.followup.send(embed=embed)
            logger.info("%s[%s] issued bot command: /vote", interaction.user.name, interaction.user.id)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoteCog(bot))
