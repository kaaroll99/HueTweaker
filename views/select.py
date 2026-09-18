import logging

import discord

from constants import ACCENT_COLOR, BANNER_URL
from utils.color_format import format_color_label
from utils.color_parse import BLACK_HEX, NEAR_BLACK_HEX
from utils.history_manager import update_history
from utils.role_manager import apply_color_role
from views.global_view import error_description, make_docs_button, make_invite_button, safe_defer
from views.set import Layout

logger = logging.getLogger(__name__)

PALETTE_SIZE = 10


def extract_palette(row: dict | None) -> list[tuple[int, str]]:
    """``[(slot, hex), ...]`` for the non-empty slots of a ``server_selections`` row."""
    colors: list[tuple[int, str]] = []
    if row:
        for i in range(1, PALETTE_SIZE + 1):
            value = row.get(f"hex_{i}")
            if isinstance(value, str) and value.strip():
                colors.append((i, value.strip().lstrip("#").lower()))
    return colors


class ColorSelect(discord.ui.ActionRow['SelectView']):
    def __init__(self, color_options: list[tuple[int, str]]):
        super().__init__()
        self.color_map = {str(slot): hex_value for slot, hex_value in color_options}
        self.children[0].options = [
            discord.SelectOption(
                label=f"Color {i}",
                value=str(slot),
                description=format_color_label(hex_value),
            )
            for i, (slot, hex_value) in enumerate(color_options, start=1)
        ]

    @discord.ui.select(
        placeholder="Select a color...",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await self.view.apply_palette_color(interaction, self.color_map.get(select.values[0]))


class SelectView(discord.ui.LayoutView):
    def __init__(self, messages, description, bot, color_options, file=None, docs_page: str = "",
                 author_id: int | None = None):
        super().__init__()
        self.msg = messages
        self.description = description
        self.bot = bot
        self.file = file
        self.docs_page = docs_page
        self.author_id = author_id

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(f"### {self.description}"))

        gallery = discord.ui.MediaGallery()
        if self.file:
            gallery.add_item(media="attachment://" + self.file.filename)
        else:
            gallery.add_item(media=BANNER_URL)
        container.add_item(gallery)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ColorSelect(color_options))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button()))

        self.add_item(container)

    async def apply_palette_color(self, interaction: discord.Interaction, hex_value: str | None) -> None:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg['revert_not_author'], ephemeral=True)
            return
        if not hex_value:
            return
        if not await safe_defer(interaction, ephemeral=True, thinking=True):
            return

        try:
            if hex_value == BLACK_HEX:
                hex_value = NEAR_BLACK_HEX
            color_int = int(hex_value, 16)
            result = await apply_color_role(
                interaction.guild, interaction.user, color_int, None, self.bot.db, self.bot.user.id
            )
            if result.changed:
                description = self.msg['select_set'].format(format_color_label(color_int))
                await update_history(self.bot.db, interaction.user.id, interaction.guild.id, color_int)
            else:
                description = self.msg['color_same']

            view = Layout.from_result(self.msg, result, color_int, interaction.user.id, description)
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] selected palette color #%s", interaction.user.name, interaction.locale, hex_value)

        except Exception as e:
            logger.warning("%s[%s] failed to apply palette color: %r", interaction.user.name, interaction.locale, e)
            try:
                await interaction.followup.send(error_description(self.msg, e), ephemeral=True)
            except discord.HTTPException:
                pass
