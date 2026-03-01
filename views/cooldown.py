import discord

from constants import ACCENT_COLOR


class CooldownLayout(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        description: str = "",
        docs_page: str = "",
    ):
        super().__init__()

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))

        thumbnail_block = discord.ui.Section(
            discord.ui.TextDisplay(description),
            accessory=discord.ui.Thumbnail(media="https://i.imgur.com/mbQJjik.png"),
        )
        container.add_item(thumbnail_block)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        self.add_item(container)
