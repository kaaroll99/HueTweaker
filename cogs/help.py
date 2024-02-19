import discord
from discord import app_commands, Embed
from discord.ext import commands
import datetime
import config
import logging

from config import bot

messages_file = config.load_yml('messages.yml')
config_file = config.load_yml('config.yml')


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Informacje o bocie oraz lista dostępnych poleceń.")
    async def help(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            embed: Embed = discord.Embed(title="Informacje o bocie", description=f"",
                                  color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())

            command_list = []
            for slash_command in bot.tree.walk_commands():
                command_list.append(slash_command.name)

            view_command_list = ", ".join([f'`/{command}`' for command in command_list])

            embed.add_field(name=f"{messages_file['item_icon']} Lista dostępnych poleceń:", value=view_command_list,
                            inline=False)
        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /help (len:{len(embed)})")


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
