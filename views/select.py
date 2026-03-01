import logging

import discord

from constants import ACCENT_COLOR, BANNER_URL
from utils.history_manager import update_history
from utils.role_manager import create_or_update_color_role, assign_role_if_missing
from views.global_view import make_docs_button, make_invite_button

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

        try:
            new_val = int(color, 16)
            role, _, _ = await create_or_update_color_role(
                interaction.guild, interaction.user.id, new_val, None, self.db
            )
            await assign_role_if_missing(interaction.user, role)
            await update_history(self.db, interaction.user.id, interaction.guild.id, new_val)

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

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(f"### {self.description}"))

        gallery = discord.ui.MediaGallery()
        if self.file:
            gallery.add_item(media="attachment://" + self.file.filename)
        else:
            gallery.add_item(media=BANNER_URL)
        container.add_item(gallery)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(ColorSelect(color_options, color_map, bot.db, bot))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button()))

        self.add_item(container)
