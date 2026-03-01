import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.data_loader import load_yml
from views.global_view import GlobalLayout
from views.help import HelpView

logger = logging.getLogger(__name__)


class HelpCog(BaseCog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.help_data = load_yml('assets/help_commands.yml')

    @app_commands.command(name="help", description="View information about the bot and a list of available commands")
    async def help(self, interaction: discord.Interaction) -> None:
        view = HelpView(
            messages=self.msg, bot=self.bot, help_data=self.help_data,
            author_id=interaction.user.id,
            description=self.msg['help_desc'].format(len(self.bot.guilds)),
            docs_button=False,
        )
        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(view=view)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/help")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /help", interaction.user.name, interaction.locale)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
