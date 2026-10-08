import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from views.colors import ColorBookView, color_groups
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)


class ColorsCog(BaseCog):

    @app_commands.command(name="colors", description="Browse CSS color names with their HEX codes")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    async def colors(self, interaction: discord.Interaction) -> None:
        docs_page = "commands/colors"
        try:
            await interaction.response.defer(ephemeral=True)
            view = ColorBookView(self.msg, next(iter(color_groups())), interaction.user.id)
            await interaction.followup.send(view=view, file=view.file, ephemeral=True)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "colors", e)

        finally:
            logger.info("%s[%s] issued bot command: /colors", interaction.user.name, interaction.locale)

    @colors.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ColorsCog(bot))
