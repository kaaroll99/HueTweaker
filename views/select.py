import logging

import discord

from database import model

logger = logging.getLogger(__name__)


class ColorSelect(discord.ui.ActionRow['SelectView']):
    def __init__(self, color_options, color_map, db, bot):
        super().__init__()
        self.color_map = color_map
        self.db = db
        self.bot = bot
        self._options = [
            discord.SelectOption(
                label=f"Color {i}",
                value=str(index),
                description=f"#{color}"
            )
            for i, (index, color) in enumerate(color_options, start=1)
        ]

        self.children[0].options = self._options

    @discord.ui.select(
        placeholder="Select a color...",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        selected_value = select.values[0]
        color = self.color_map.get(selected_value)
        if not color:
            return

        role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")

        if role is None:
            role_position = 1
            guild_obj = self.db.select_one(model.Guilds, {"server": interaction.guild.id})

            if guild_obj:
                top_role = discord.utils.get(interaction.guild.roles, id=guild_obj["role"])
                if top_role:
                    role_position = max(1, top_role.position - 1)

            role = await interaction.guild.create_role(
                name=f"color-{interaction.user.id}",
                colour=discord.Colour(int(color, 16))
            )
            if role_position > 1:
                await role.edit(position=role_position)

        try:
            new_val = int(color, 16)
            if not role.colour or role.colour.value != new_val:
                await role.edit(colour=discord.Colour(new_val))
            if role not in interaction.user.roles:
                await interaction.user.add_roles(role, reason="Static color selection")

        except Exception as e:
            logger.error("Failed to edit role: %s", e)
            if not interaction.response.is_done():
                await interaction.response.send_message(
                    "Failed to change color due to insufficient permissions.",
                    ephemeral=True
                )
            return

        if not interaction.response.is_done():
            await interaction.response.defer()


class SelectView(discord.ui.LayoutView):
    def __init__(self, messages, description, bot, color_options, color_map, file=None, docs_page: str = ""):
        super().__init__()
        self.msg = messages
        self.description = description
        self.bot = bot
        self.file = file
        self.docs_page = docs_page

        container = discord.ui.Container(accent_colour=discord.Color(0xFCF5AB))
        container.add_item(discord.ui.TextDisplay(f"### {self.description}"))

        if self.file:
            gallery = discord.ui.MediaGallery()
            gallery.add_item(media="attachment://" + self.file.filename)
            container.add_item(gallery)
        else:
            gallery = discord.ui.MediaGallery()
            gallery.add_item(media="https://i.imgur.com/rXe4MHa.png")
            container.add_item(gallery)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ColorSelect(color_options, color_map, bot.db, bot))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

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
