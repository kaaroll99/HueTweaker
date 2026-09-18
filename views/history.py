import logging

import discord

from constants import ACCENT_COLOR, BANNER_URL
from utils.color_format import format_colors_label
from utils.history_manager import update_history
from utils.role_manager import apply_color_role
from views.global_view import error_description, make_docs_button, make_invite_button, safe_defer
from views.set import Layout

logger = logging.getLogger(__name__)


class HistoryView(discord.ui.LayoutView):
    def __init__(self, messages, description, bot, file=None, docs_page: str = "",
                 colors: list[tuple[int, int | None]] | None = None, author_id: int | None = None):
        super().__init__()
        self.msg = messages
        self.description = description
        self.bot = bot
        self.file = file
        self.docs_page = docs_page
        self.colors = colors or []
        self.author_id = author_id

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(self.description))

        gallery = discord.ui.MediaGallery()
        if self.file:
            gallery.add_item(media="attachment://" + self.file.filename)
        else:
            gallery.add_item(media=BANNER_URL)
        container.add_item(gallery)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        if self.colors:
            buttons = []
            for i, (primary, secondary) in enumerate(self.colors, start=1):
                button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.secondary)
                button.callback = self._make_restore_callback(primary, secondary)
                buttons.append(button)
            container.add_item(discord.ui.ActionRow(*buttons))

        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button()))

        self.add_item(container)

    def _make_restore_callback(self, primary: int, secondary: int | None):
        async def _callback(interaction: discord.Interaction):
            await self._restore_color(interaction, primary, secondary)
        return _callback

    async def _restore_color(self, interaction: discord.Interaction, primary: int, secondary: int | None) -> None:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg['revert_not_author'], ephemeral=True
            )
            return

        if not await safe_defer(interaction, ephemeral=True, thinking=True):
            return

        label = format_colors_label(primary, secondary)
        try:
            result = await apply_color_role(
                interaction.guild, interaction.user, primary, secondary, self.bot.db, self.bot.user.id
            )

            if result.changed:
                description = self.msg['history_restored'].format(label)
                await update_history(self.bot.db, interaction.user.id, interaction.guild.id, primary, secondary)
            else:
                description = self.msg['color_same']

            view = Layout.from_result(self.msg, result, primary, interaction.user.id, description)
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] restored color %s from history", interaction.user.name, interaction.locale, label)
        except Exception as e:
            logger.warning("%s[%s] failed to restore color from history: %r", interaction.user.name, interaction.locale, e)
            try:
                await interaction.followup.send(error_description(self.msg, e), ephemeral=True)
            except discord.HTTPException:
                pass
