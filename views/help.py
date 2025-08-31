import logging

import discord
from discord.ext import commands

from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)


class HelpSelect(discord.ui.ActionRow['HelpView']):
    def __init__(self, help_data: dict, msg: dict):
        super().__init__()
        self.help_data = help_data
        self.msg = msg

    @discord.ui.select(
        placeholder="Choose a command",
        min_values=1,
        max_values=1,
        options=[
            discord.SelectOption(label="/help", value="help", emoji="ℹ️"),
            discord.SelectOption(label="/set", value="set", emoji="🌈"),
            discord.SelectOption(label="/remove", value="remove", emoji="🗑️"),
            discord.SelectOption(label="/select", value="select", emoji="⭐"),
            discord.SelectOption(label="/check", value="check", emoji="🔍"),
            discord.SelectOption(label="/force set", value="forceset", emoji="⚙️"),
            discord.SelectOption(label="/force remove", value="forceremove", emoji="🔄"),
            discord.SelectOption(label="/force purge", value="forcepurge", emoji="💥"),
            discord.SelectOption(label="/setup toprole", value="toprole", emoji="💫"),
            discord.SelectOption(label="/setup select", value="setupselect", emoji="💫"),
            discord.SelectOption(label="/vote", value="vote", emoji="🗳️"),
        ],
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await self.view.on_select(interaction, select.values[0])


class HelpView(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        bot: commands.Bot,
        help_data: dict,
        author_id: int,
        description: str | None = None,
        docs_button: bool = False,
        docs_key: str | None = None
    ):
        super().__init__()
        self.msg = messages
        self.bot = bot
        self.help_data = help_data
        self.author_id = author_id
        self.docs_button = docs_button
        self.docs_key = docs_key

        self.description = description or self.msg['help_desc'].format(len(bot.guilds))

        self.desc_display = discord.ui.TextDisplay(self.description)
        container = discord.ui.Container(accent_colour=discord.Color(0xFCF5AB))
        container.add_item(self.desc_display)

        if self.docs_button:
            docs_button_body = discord.ui.Button(
                label="See details of the command in the documentation",
                style=discord.ButtonStyle.link,
                emoji="<:docs:1362879505613586643>",
                url=f"https://huetweaker.gitbook.io/docs/commands/{self.docs_key}"
            )
            container.add_item(discord.ui.ActionRow(docs_button_body))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="https://i.imgur.com/rXe4MHa.png")
        container.add_item(gallery)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(HelpSelect(help_data, messages))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        invite_button = discord.ui.Button(
            label='Add HueTweaker to your server',
            style=discord.ButtonStyle.link,
            emoji="<:star:1362879443625971783>",
            url="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot"
        )
        support_button = discord.ui.Button(
            label="Join support server",
            style=discord.ButtonStyle.url,
            emoji="<:bubble:1362879391423533226>",
            url="https://discord.gg/tYdK4pD6ks"
        )
        privacy_button = discord.ui.Button(
            label="Privacy Policy",
            style=discord.ButtonStyle.url,
            emoji="<:docs:1362879505613586643>",
            url="https://huetweaker.gitbook.io/docs/main/privacy-policy"
        )
        terms_button = discord.ui.Button(
            label="Terms of Service",
            style=discord.ButtonStyle.url,
            emoji="<:docs:1362879505613586643>",
            url="https://huetweaker.gitbook.io/docs/main/terms-of-service"
        )

        container.add_item(discord.ui.ActionRow(invite_button, support_button))
        container.add_item(discord.ui.ActionRow(privacy_button, terms_button))

        self.add_item(container)

    async def on_select(self, interaction: discord.Interaction, selected_key: str):
        try:
            data = self.help_data[selected_key]
            desc_display = (
                f"## Details for /{data['name']} command:\n\n"
                f"{data['desc']}\n\n"
                f"**{self.msg['com_syntax']}**\n {data['usage']}\n\n"
                f"**{self.msg['com_example']}**\n {data['example']}\n\n"
            )
            docs_key = data['docs']
        except Exception as e:
            description = self.msg['exception']
            view = GlobalLayout(messages=self.msg, description=description, docs_page="commands/help")
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
            await interaction.response.edit_message(view=view)

        new_view = HelpView(messages=self.msg, bot=self.bot, help_data=self.help_data, author_id=self.author_id, description=desc_display, docs_button=True, docs_key=docs_key)
        await interaction.response.edit_message(view=new_view)
