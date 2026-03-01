import discord

from constants import ACCENT_COLOR, DOCS_BASE_URL
from views.global_view import make_invite_button


class CheckLayout(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        description: str = "",
        image: str = None,
        elements: list = None,
    ):
        super().__init__()
        self.msg = messages

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(description))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        for element in elements:
            container.add_item(
                discord.ui.TextDisplay(f"**{element[0]}**\n> {element[1]}")
            )
            container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media=image)
        container.add_item(gallery)

        docs_button = discord.ui.Button(
            label="Check more colors",
            style=discord.ButtonStyle.link,
            emoji="<:docs:1362879505613586643>",
            url=f"{DOCS_BASE_URL}/main/colors",
        )
        container.add_item(discord.ui.ActionRow(docs_button, make_invite_button()))

        self.add_item(container)
