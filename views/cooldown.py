import discord


class CooldownLayout(discord.ui.LayoutView):
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

        thumbnail_block = discord.ui.Section(
            discord.ui.TextDisplay(self.description),
            accessory=discord.ui.Thumbnail(media="https://i.imgur.com/mbQJjik.png"))
        container.add_item(thumbnail_block)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        vote_button = discord.ui.Button(
            label="Vote for the bot to reduce the next cooldown time for 12h",
            style=discord.ButtonStyle.link,
            emoji="<:star:1362879443625971783>",
            url="https://top.gg/bot/1209187999934578738/vote"
        )
        container.add_item(discord.ui.ActionRow(vote_button))

        self.add_item(container)
