import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from utils.color_format import color_presets
from views.cooldown import CooldownLayout
from views.global_view import GlobalLayout, error_description, http_error_description

logger = logging.getLogger(__name__)


def preset_choices(current: str) -> list[app_commands.Choice[str]]:
    """Return autocomplete choices for the preset names containing ``current`` (Discord shows 25)."""
    typed = current.strip().lower()
    return [
        app_commands.Choice(name=name, value=name.lower())
        for name, _ in color_presets().values()
        if typed in name.lower()
    ][:25]


class BaseCog(commands.Cog):
    """Base of the command cogs: shared database, messages, vote checker and error replies."""

    _command_ids: dict[str, int] | None = None

    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages
        self.votes = bot.votes

    @staticmethod
    def remember_commands(app_commands_list: list[app_commands.AppCommand]) -> None:
        """Cache the synced command ids that ``mention`` needs."""
        BaseCog._command_ids = {cmd.name: cmd.id for cmd in app_commands_list}

    async def mention(self, name: str) -> str:
        """Return a clickable ``</name:id>`` mention, or plain text while the command ids are unknown."""
        if BaseCog._command_ids is None:
            try:
                self.remember_commands(await self.bot.tree.fetch_commands())
            except discord.HTTPException:
                return f"`/{name}`"
        command_id = BaseCog._command_ids.get(name.split()[0])
        return f"</{name}:{command_id}>" if command_id else f"`/{name}`"

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
        """Return the user-facing text for a failed color operation (role, Discord or other error)."""
        return error_description(self.msg, error)

    def log_command_error(self, interaction: discord.Interaction, command: str, error: Exception) -> None:
        """Log expected failures (permissions, role limit, Discord API) as warnings, the rest as critical."""
        if isinstance(error, discord.HTTPException):
            logger.warning("%s[%s] /%s raised HTTP exception: %s", interaction.user.name, interaction.user.id, command, error.text)
        elif isinstance(error, (ValueError, LookupError)) or error.__class__.__module__.startswith("utils."):
            logger.warning("%s[%s] /%s failed: %r", interaction.user.name, interaction.user.id, command, error)
        else:
            logger.critical("%s[%s] /%s raised critical exception - %r", interaction.user.name, interaction.user.id, command, error)

    @staticmethod
    async def respond(interaction: discord.Interaction, view: discord.ui.LayoutView, **kwargs) -> None:
        """Reply in whatever state the interaction is in.

        Sends the initial response, edits the deferred response (replacing any attachments), or
        sends a follow-up when the original can no longer be edited.
        """
        if not interaction.response.is_done():
            await interaction.response.send_message(view=view, ephemeral=True, **kwargs)
            return
        try:
            await interaction.edit_original_response(content=None, view=view, attachments=[], **kwargs)
        except discord.HTTPException:
            await interaction.followup.send(view=view, ephemeral=True, **kwargs)
