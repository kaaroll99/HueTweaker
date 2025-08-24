import discord


class GlobalLayout(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        description: str = "",
        docs_page: str = ""
    ):
        super().__init__()
        self.msg = messages
        self.description = description
        self.docs_page = docs_page

        container = discord.ui.Container(accent_colour=discord.Color(0xFCF5AB))
        container.add_item(
            discord.ui.TextDisplay(self.description)
        )
        # gallery = discord.ui.MediaGallery()
        # gallery.add_item(media="https://i.imgur.com/rXe4MHa.png")
        # container.add_item(gallery)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        docs_button = discord.ui.Button(
            label='See documentation',
            style=discord.ButtonStyle.link,
            emoji="<:docs:1362879505613586643>",
            url=f"https://huetweaker.gitbook.io/docs/{self.docs_page}"
        )
        invite_button = discord.ui.Button(
            label='Add HueTweaker to your server',
            style=discord.ButtonStyle.link,
            emoji="<:star:1362879443625971783>",
            url="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot"
        )
        container.add_item(discord.ui.ActionRow(docs_button, invite_button))

        self.add_item(container)
