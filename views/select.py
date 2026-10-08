import logging

import discord

from constants import ACCENT_COLOR, BANNER_URL
from utils.color_format import Colors, decode_style, format_colors_label
from utils.history_manager import update_history
from utils.role_manager import apply_color_role
from views.global_view import error_description, gradient_gate, make_docs_button, make_invite_button, safe_defer
from views.set import Layout

logger = logging.getLogger(__name__)

PALETTE_SIZE = 10


def extract_palette(row: dict | None) -> list[tuple[int, Colors]]:
    """``[(slot, colors), ...]`` for the non-empty slots of a ``server_selections`` row."""
    colors: list[tuple[int, Colors]] = []
    if row:
        for i in range(1, PALETTE_SIZE + 1):
            decoded = decode_style(row.get(f"hex_{i}"))
            if decoded is not None:
                colors.append((i, decoded))
    return colors


class ColorSelect(discord.ui.ActionRow['SelectView']):
    def __init__(self, color_options: list[tuple[int, Colors]]):
        super().__init__()
        self.color_map = {str(slot): style for slot, style in color_options}
        self.children[0].options = [
            discord.SelectOption(
                label=f"Color {i}",
                value=str(slot),
                description=format_colors_label(*style)[:100],
            )
            for i, (slot, style) in enumerate(color_options, start=1)
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

    async def apply_palette_color(self, interaction: discord.Interaction, colors: Colors | None) -> None:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg['revert_not_author'], ephemeral=True)
            return
        if not colors:
            return
        if not await safe_defer(interaction, ephemeral=True, thinking=True):
            return

        primary, secondary, tertiary = colors
        if primary == 0 and secondary is None:
            primary = 1  # Discord treats #000000 as "no color"
        label = format_colors_label(primary, secondary, tertiary)
        try:
            if secondary is not None:
                blocked = await gradient_gate(self.msg, self.bot.votes, interaction.guild, interaction.user.id,
                                              self.docs_page, require_vote=False)
                if blocked is not None:
                    await interaction.followup.send(view=blocked, ephemeral=True)
                    return

            result = await apply_color_role(
                interaction.guild, interaction.user, primary, secondary, self.bot.db, self.bot.user.id,
                tertiary_val=tertiary,
            )
            if result.changed:
                description = self.msg['select_set'].format(label)
                await update_history(self.bot.db, interaction.user.id, interaction.guild.id, primary, secondary, tertiary)
            else:
                description = self.msg['color_same']

            view = Layout.from_result(self.msg, result, primary, interaction.user.id, description)
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] selected palette color %s", interaction.user.name, interaction.locale, label)

        except Exception as e:
            logger.warning("%s[%s] failed to apply palette color: %r", interaction.user.name, interaction.locale, e)
            try:
                await interaction.followup.send(error_description(self.msg, e), ephemeral=True)
            except discord.HTTPException:
                pass
