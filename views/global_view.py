import discord


class GlobalLayout(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        description: str = ""
    ):
        super().__init__()
        self.msg = messages
        self.description = description

        container = discord.ui.Container(accent_colour=discord.Color(int(4539717, 16)))
        container.add_item(
            discord.ui.TextDisplay(self.description)
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        docs_button = discord.ui.Button(
            label=self.msg.get('invite_button', 'See documentation'),
            style=discord.ButtonStyle.link,
            emoji="<:docs:1362879505613586643>",
            url="https://huetweaker.gitbook.io/docs/"
        )
        invite_button = discord.ui.Button(
            label=self.msg.get('invite_button', 'Add HueTweaker to your server'),
            style=discord.ButtonStyle.link,
            emoji="<:star:1362879443625971783>",
            url="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot"
        )
        container.add_item(discord.ui.ActionRow(docs_button, invite_button))

        self.add_item(container)
