import discord

from constants import ACCENT_COLOR
from views.global_view import make_docs_button
from views.set import apply_from_button


class MatchView(discord.ui.LayoutView):
    """Suggested colors (``/match``, ``/harmony``): one numbered button per entry, 5 per row.

    An entry is a color int or a ``(primary, secondary)`` gradient, which gets a 🌈 button.
    """

    def __init__(self, messages, description, bot, file, entries: list[int | tuple[int, int]], author_id: int,
                 docs_page: str = "commands/match", source: str = "match"):
        super().__init__()
        self.msg = messages
        self.bot = bot
        self.file = file
        self.author_id = author_id
        self.docs_page = docs_page
        self.source = source

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(description))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="attachment://" + file.filename)
        container.add_item(gallery)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        buttons = []
        for i, entry in enumerate(entries, start=1):
            primary, secondary = entry if isinstance(entry, tuple) else (entry, None)
            if secondary is None:
                button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.secondary)
            else:
                button = discord.ui.Button(label=str(i), emoji="🌈", style=discord.ButtonStyle.primary)
            button.callback = self._make_callback(primary, secondary)
            buttons.append(button)
        for start in range(0, len(buttons), 5):
            container.add_item(discord.ui.ActionRow(*buttons[start:start + 5]))
        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page)))

        self.add_item(container)

    def _make_callback(self, primary: int, secondary: int | None):
        async def _callback(interaction: discord.Interaction):
            await apply_from_button(self, interaction, (primary, secondary, None), self.source, "color_set")
        return _callback
