import discord
from database import model
from typing import Any


class SetCountButton(discord.ui.Button):
    def __init__(self, color_item: str, db: Any):
        super().__init__(label="<:star:1362879443625971783>", style=discord.ButtonStyle.primary)
        self.color_item = color_item
        self.db = db

    async def callback(self, interaction) -> None:
        role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")

        if role is None:
            role_position = 1
            with self.db as db_session:
                guild_row = db_session.select_one(model.guilds_class("guilds"), {"server": interaction.guild.id})

            if guild_row:
                top_role = discord.utils.get(interaction.guild.roles, id=guild_row.get("role", None))
                if top_role:
                    role_position = max(1, top_role.position - 1)
            role = await interaction.guild.create_role(
                name=f"color-{interaction.user.id}",
                colour=discord.Colour(int(self.color_item, 16))
            )
            if role_position > 1:
                await role.edit(position=role_position)

        else:
            new_val = int(self.color_item, 16)
            if not role.colour or role.colour.value != new_val:
                await role.edit(colour=discord.Colour(new_val))
            if role not in interaction.user.roles:
                await interaction.user.add_roles(role, reason="Static color selection")
        await interaction.response.edit_message(view=self.view)


class TestlLayout(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        description: str = "",
        docs_page: str = "",
        query: list = None,
        db: Any = None
    ):
        super().__init__()
        self.msg = messages
        self.description = description
        self.docs_page = docs_page
        self.query = query if query is not None else []
        self.db = db

        container = discord.ui.Container(accent_colour=discord.Color(0xFCF5AB))
        container.add_item(
            discord.ui.TextDisplay(self.description)
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        available_colors = []

        colors_data = query[0]
        for i in range(1, 11):
            color_key = f"hex_{i}"
            color_value = colors_data.get(color_key)
            if isinstance(color_value, str) and color_value.strip():
                available_colors.append((i, color_value.strip()))

        for color_item in available_colors:
            container.add_item(
                discord.ui.Section(
                    discord.ui.MediaGallery().add_item(media="https://i.imgur.com/rXe4MHa.png"),
                    accessory=SetCountButton(color_item=color_item[1], db=self.db)
                )
            )

        docs_button = discord.ui.Button(
            label=self.msg.get('invite_button', 'See documentation'),
            style=discord.ButtonStyle.link,
            emoji="<:docs:1362879505613586643>",
            url=f"https://huetweaker.gitbook.io/docs/{self.docs_page}"
        )
        invite_button = discord.ui.Button(
            label=self.msg.get('invite_button', 'Add HueTweaker to your server'),
            style=discord.ButtonStyle.link,
            emoji="<:star:1362879443625971783>",
            url="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot"
        )
        container.add_item(discord.ui.ActionRow(docs_button, invite_button))

        self.add_item(container)
