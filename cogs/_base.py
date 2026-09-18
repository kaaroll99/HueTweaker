import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from views.cooldown import CooldownLayout
from views.global_view import GlobalLayout, error_description, http_error_description

logger = logging.getLogger(__name__)


class BaseCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    async def handle_cooldown_error(
        self, interaction: discord.Interaction, error: app_commands.CommandOnCooldown
    ) -> None:
        retry_time = datetime.now() + timedelta(seconds=error.retry_after)
        response = self.msg["cool_down"].format(int(retry_time.timestamp()))
        view = CooldownLayout(messages=self.msg, description=response)
        if interaction.response.is_done():
            await interaction.followup.send(
                view=view, ephemeral=True, delete_after=error.retry_after
            )
        else:
            await interaction.response.send_message(
                view=view, ephemeral=True, delete_after=error.retry_after
            )

    async def handle_permission_error(self, interaction: discord.Interaction) -> None:
        view = GlobalLayout(messages=self.msg, description=self.msg["no_permissions"])
        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=True)
        else:
            await interaction.response.send_message(view=view, ephemeral=True)

    def get_http_error_description(self, error: discord.HTTPException) -> str:
        return http_error_description(self.msg, error)

    def describe_error(self, error: Exception) -> str:
        """User-facing text for a failed color operation (role errors, Discord errors, other)."""
        return error_description(self.msg, error)

    def log_command_error(self, interaction: discord.Interaction, command: str, error: Exception) -> None:
        """Expected failures (permissions, role limit, Discord API) are warnings; the rest is critical."""
        if isinstance(error, discord.HTTPException):
            logger.warning("%s[%s] /%s raised HTTP exception: %s", interaction.user.name, interaction.user.id, command, error.text)
        elif isinstance(error, (ValueError, LookupError)) or error.__class__.__module__.startswith("utils."):
            logger.warning("%s[%s] /%s failed: %r", interaction.user.name, interaction.user.id, command, error)
        else:
            logger.critical("%s[%s] /%s raised critical exception - %r", interaction.user.name, interaction.user.id, command, error)

    @staticmethod
    async def respond(interaction: discord.Interaction, view: discord.ui.LayoutView, **kwargs) -> None:
        """Reply in whatever state the interaction is in: initial response, edit of the deferred
        response (replacing any attachments), or a follow-up when the original was already used."""
        if not interaction.response.is_done():
            await interaction.response.send_message(view=view, ephemeral=True, **kwargs)
            return
        try:
            await interaction.edit_original_response(content=None, view=view, attachments=[], **kwargs)
        except discord.HTTPException:
            await interaction.followup.send(view=view, ephemeral=True, **kwargs)
