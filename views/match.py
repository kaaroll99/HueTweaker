import discord

from constants import ACCENT_COLOR
from views.global_view import make_docs_button
from views.set import apply_from_button


class MatchView(discord.ui.LayoutView):
    """``/match`` result: one button per avatar color, plus a 🌈 gradient of the first two."""

    def __init__(self, messages, description, bot, file, colors: list[int], author_id: int,
                 docs_page: str = "commands/match"):
        super().__init__()
        self.msg = messages
        self.bot = bot
        self.file = file
        self.author_id = author_id
        self.docs_page = docs_page

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(description))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="attachment://" + file.filename)
        container.add_item(gallery)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        buttons = []
        for i, color in enumerate(colors, start=1):
            button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.secondary)
            button.callback = self._make_callback(color, None)
            buttons.append(button)
        if len(colors) >= 2:
            gradient_button = discord.ui.Button(label=str(len(colors) + 1), emoji="🌈", style=discord.ButtonStyle.primary)
            gradient_button.callback = self._make_callback(colors[0], colors[1])
            buttons.append(gradient_button)
        container.add_item(discord.ui.ActionRow(*buttons))
        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page)))

        self.add_item(container)

    def _make_callback(self, primary: int, secondary: int | None):
        async def _callback(interaction: discord.Interaction):
            await apply_from_button(self, interaction, (primary, secondary, None), "match", "color_set")
        return _callback
