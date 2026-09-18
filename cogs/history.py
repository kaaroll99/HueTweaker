import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from database import model
from utils.color_format import ColorUtils
from utils.history_manager import history_colors
from views.global_view import GlobalLayout
from views.history import HistoryView

logger = logging.getLogger(__name__)


class HistoryCog(BaseCog):

    @app_commands.command(name="history", description="View your color change history on server")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def history(self, interaction: discord.Interaction) -> None:
        docs_page = "commands/history"
        try:
            await interaction.response.defer(ephemeral=True)

            row = await self.db.select_one(model.History, {"user_id": interaction.user.id, "guild_id": interaction.guild.id})
            colors = history_colors(row)

            if not colors:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['history_no_history'], docs_page))
                return

            image = ColorUtils.generate_color_list_image(interaction.user.display_name, colors)
            file = discord.File(fp=ColorUtils.to_bytes(image), filename="color_history.png")
            view = HistoryView(self.msg, self.msg['history_title'], self.bot, file, docs_page,
                               colors=colors, author_id=interaction.user.id)
            await interaction.followup.send(view=view, file=file, ephemeral=True)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "history", e)

        finally:
            logger.info("%s[%s] issued bot command: /history", interaction.user.name, interaction.locale)

    @history.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HistoryCog(bot))
