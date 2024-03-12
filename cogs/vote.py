import discord
from discord import app_commands
from discord.ext import commands
import datetime
import config
import logging
from config import bot


messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


class VoteCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="vote", description="View links to vote")
    async def vote(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title=f"Vote for {bot.user.name}", description=f"",
                              color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            embed.description = f"Every 12 hours you can help by voting for the bot on the following pages."
            embed.add_field(name=f"",
                            value=f"✨ [Click here to vote on top.gg](https://top.gg/bot/1209187999934578738/vote)",
                            inline=False)
            embed.add_field(name=f"", value=f"✨ [Click here to vote on discordbotlist.com](https://discordbotlist.com/bots/huetweaker/upvote)",
                            inline=False)
        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name} by kaaroll99", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /vote (len:{len(embed)})")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(VoteCog(bot))
