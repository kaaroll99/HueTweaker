import logging

import discord

from constants import ACCENT_COLOR, BANNER_URL
from utils.history_manager import update_history
from utils.role_manager import create_or_update_color_role, assign_role_if_missing
from views.global_view import make_docs_button, make_invite_button
from views.set import Layout

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
                interaction.guild,
                interaction.user.id,
                new_val,
                None,
                self.db,
                self.bot.user.id,
            )
            await assign_role_if_missing(interaction.user, role)

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


class HistoryView(discord.ui.LayoutView):
    def __init__(self, messages, description, bot, file=None, docs_page: str = "",
                 colors: list[int] | None = None, author_id: int | None = None):
        super().__init__()
        self.msg = messages
        self.description = description
        self.bot = bot
        self.file = file
        self.docs_page = docs_page
        self.colors = colors or []
        self.author_id = author_id

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(self.description))

        gallery = discord.ui.MediaGallery()
        if self.file:
            gallery.add_item(media="attachment://" + self.file.filename)
        else:
            gallery.add_item(media=BANNER_URL)
        container.add_item(gallery)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        if self.colors:
            buttons = []
            for i, color_int in enumerate(self.colors, start=1):
                button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.secondary)
                button.callback = self._make_restore_callback(color_int)
                buttons.append(button)
            container.add_item(discord.ui.ActionRow(*buttons))

        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button()))

        self.add_item(container)

    def _make_restore_callback(self, color_int: int):
        async def _callback(interaction: discord.Interaction):
            await self._restore_color(interaction, color_int)
        return _callback

    async def _restore_color(self, interaction: discord.Interaction, color_int: int) -> None:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg.get('revert_not_author', "You can't use these buttons."), ephemeral=True
            )
            return

        hex_str = f"#{color_int:06X}"
        try:
            role, role_updated, prev_colors = await create_or_update_color_role(
                interaction.guild,
                interaction.user.id,
                color_int,
                None,
                self.bot.db,
                self.bot.user.id,
            )
            await assign_role_if_missing(interaction.user, role)

            if role_updated:
                description = self.msg['history_restored'].format(hex_str)
                undo_lock = False
                await update_history(self.bot.db, interaction.user.id, interaction.guild.id, color_int)
            else:
                description = self.msg['color_same']
                undo_lock = True

            view = Layout(
                messages=self.msg,
                color=discord.Color(color_int),
                display_color=hex_str,
                prev_colors=prev_colors,
                role_id=role.id if role else None,
                author_id=interaction.user.id,
                description=description,
                undo_lock=undo_lock,
            )
            await interaction.response.send_message(view=view, ephemeral=True)
            logger.info("%s[%s] restored color %s from history", interaction.user.name, interaction.locale, hex_str)
        except discord.HTTPException as e:
            await interaction.response.send_message(self.msg['exception'], ephemeral=True)
            logger.warning("%s[%s] HTTP exception while restoring color: %s", interaction.user.name, interaction.locale, e)
        except Exception as e:
            await interaction.response.send_message(self.msg['exception'], ephemeral=True)
            logger.critical("%s[%s] raise critical exception while restoring color - %r", interaction.user.name, interaction.locale, e)
