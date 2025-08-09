import datetime
import logging

import discord
from discord import app_commands, Embed
from discord.ext import commands


class VoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.msg = bot.messages

    @app_commands.command(name="vote", description="View links to vote")
    async def vote(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            embed = discord.Embed(title=self.msg['vote_title'].format(self.bot.user.name), description=f"",
                                   color=4539717, timestamp=datetime.datetime.now())
            await interaction.response.defer(ephemeral=True)
            embed.description = self.msg['vote_desc']
            embed.add_field(name=f"", value=self.msg['vote_topgg'], inline=False)
            embed.add_field(name=f"", value=self.msg['vote_dbl'], inline=False)

        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logging.critical(f"{interaction.user.name}[{interaction.locale}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{self.bot.user.name} by kaaroll99", icon_url=self.bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user.name}[{interaction.user.id}] issued bot command: /vote")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoteCog(bot))
