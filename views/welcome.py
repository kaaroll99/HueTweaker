import discord

from constants import ACCENT_COLOR, BANNER_URL, SUPPORT_SERVER_URL
from views.global_view import make_docs_button


class WelcomeLayout(discord.ui.LayoutView):
    def __init__(self, description: str):
        super().__init__(timeout=None)
        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        gallery = discord.ui.MediaGallery()
        gallery.add_item(media=BANNER_URL)
        container.add_item(gallery)
        container.add_item(discord.ui.TextDisplay(description))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
        support_button = discord.ui.Button(
            label="Join support server",
            style=discord.ButtonStyle.url,
            emoji="<:bubble:1362879391423533226>",
            url=SUPPORT_SERVER_URL,
        )
        container.add_item(discord.ui.ActionRow(make_docs_button(label="Quick start"), support_button))
        self.add_item(container)
