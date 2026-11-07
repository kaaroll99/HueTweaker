import discord

from constants import ACCENT_COLOR, BANNER_URL
from utils.color_format import Colors, format_colors_label
from views.global_view import make_docs_button, make_invite_button
from views.set import apply_from_button


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
        """Apply a palette style; a gradient needs Server Boost but, unlike elsewhere, no vote."""
        if not colors:
            return
        primary, secondary, tertiary = colors
        if primary == 0 and secondary is None:
            colors = (1, None, tertiary)  # Discord treats #000000 as "no color"
        await apply_from_button(self, interaction, colors, "select", "select_set", require_vote=False)
