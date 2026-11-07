import discord

from constants import ACCENT_COLOR, BANNER_URL
from views.global_view import make_docs_button, make_invite_button
from views.set import apply_from_button


class HistoryView(discord.ui.LayoutView):
    def __init__(self, messages, description, bot, file=None, docs_page: str = "",
                 colors: list[tuple[int, int | None, int | None]] | None = None, author_id: int | None = None):
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
            for i, colors in enumerate(self.colors, start=1):
                button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.secondary)
                button.callback = self._make_restore_callback(*colors)
                buttons.append(button)
            container.add_item(discord.ui.ActionRow(*buttons))

        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button()))

        self.add_item(container)

    def _make_restore_callback(self, primary: int, secondary: int | None, tertiary: int | None):
        async def _callback(interaction: discord.Interaction):
            await apply_from_button(self, interaction, (primary, secondary, tertiary), "history", "history_restored")
        return _callback
