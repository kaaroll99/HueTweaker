import logging

import discord

from constants import ACCENT_COLOR
from database import model
from utils.color_format import ColorUtils, format_color_label
from utils.history_manager import update_history
from utils.role_manager import create_or_update_color_role, assign_role_if_missing
from views.global_view import GlobalLayout, make_docs_button, make_invite_button
from views.set import Layout

logger = logging.getLogger(__name__)

FAVORITES_LIMIT = 10
FAVORITES_IMAGE_NAME = "favorites.png"


def extract_favorite_colors(row: dict | None) -> list[tuple[int, str]]:
    """Return ``[(slot, hex), ...]`` for non-empty favorite slots."""
    colors: list[tuple[int, str]] = []
    if row:
        for i in range(1, FAVORITES_LIMIT + 1):
            value = row.get(f"hex_{i}")
            if isinstance(value, str) and value.strip():
                colors.append((i, value.strip()))
    return colors


def render_favorites_file(nick: str, colors: list[tuple[int, str]]) -> discord.File:
    int_colors = [int(hx, 16) for _, hx in colors]
    image = ColorUtils.generate_color_list_image(nick, int_colors)
    return discord.File(fp=ColorUtils.to_bytes(image), filename=FAVORITES_IMAGE_NAME)


class RemoveSelect(discord.ui.ActionRow['FavoritesView']):
    def __init__(self, messages, bot, author_id, nick, docs_page, colors):
        super().__init__()
        self.msg = messages
        self.bot = bot
        self.author_id = author_id
        self.nick = nick
        self.docs_page = docs_page

        self.children[0].options = [
            discord.SelectOption(label=f"{pos}. {format_color_label(hx)}", value=str(slot))
            for pos, (slot, hx) in enumerate(colors, start=1)
        ]

    @discord.ui.select(placeholder="Remove a favorite...", min_values=1, max_values=1, options=[])
    async def remove_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg.get('revert_not_author', "You can't use this."), ephemeral=True)
            return

        slot = int(select.values[0])
        try:
            await self.bot.db.update(model.Favorites, {"user_id": interaction.user.id}, {f"hex_{slot}": None})

            row = await self.bot.db.select_one(model.Favorites, {"user_id": interaction.user.id})
            colors = extract_favorite_colors(row)

            if not colors:
                view = GlobalLayout(messages=self.msg, description=self.msg['favorites_no_colors'], docs_page=self.docs_page)
                await interaction.response.edit_message(view=view, attachments=[])
                return

            view, file = FavoritesView.build(self.msg, self.bot, self.author_id, colors, self.nick, self.docs_page)
            await interaction.response.edit_message(view=view, attachments=[file])
            logger.info("%s[%s] removed a favorite color (slot %s)", interaction.user.name, interaction.locale, slot)

        except Exception as e:
            logger.critical("%s[%s] raise critical exception while removing favorite - %r", interaction.user.name, interaction.locale, e)
            if not interaction.response.is_done():
                await interaction.response.send_message(self.msg['exception'], ephemeral=True)


class FavoritesView(discord.ui.LayoutView):
    def __init__(self, messages, bot, author_id, colors, nick, docs_page: str = ""):
        super().__init__()
        self.msg = messages
        self.bot = bot
        self.author_id = author_id
        self.colors = colors
        self.nick = nick
        self.docs_page = docs_page

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(self.msg['favorites_list_title']))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="attachment://" + FAVORITES_IMAGE_NAME)
        container.add_item(gallery)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        buttons = []
        for pos, (slot, hx) in enumerate(colors, start=1):
            button = discord.ui.Button(label=str(pos), style=discord.ButtonStyle.secondary)
            button.callback = self._make_apply_callback(int(hx, 16))
            buttons.append(button)
        for start in range(0, len(buttons), 5):
            container.add_item(discord.ui.ActionRow(*buttons[start:start + 5]))

        container.add_item(RemoveSelect(self.msg, self.bot, self.author_id, self.nick, self.docs_page, colors))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button()))

        self.add_item(container)

    @classmethod
    def build(cls, messages, bot, author_id, colors, nick, docs_page: str = ""):
        file = render_favorites_file(nick, colors)
        view = cls(messages, bot, author_id, colors, nick, docs_page)
        return view, file

    def _make_apply_callback(self, color_int: int):
        async def _callback(interaction: discord.Interaction):
            await self._apply_favorite(interaction, color_int)
        return _callback

    async def _apply_favorite(self, interaction: discord.Interaction, color_int: int) -> None:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg.get('revert_not_author', "You can't use these buttons."), ephemeral=True)
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
                description = self.msg['favorites_applied'].format(format_color_label(color_int))
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
            logger.info("%s[%s] applied favorite color %s", interaction.user.name, interaction.locale, hex_str)

        except discord.HTTPException as e:
            await interaction.response.send_message(self.msg['exception'], ephemeral=True)
            logger.warning("%s[%s] HTTP exception while applying favorite: %s", interaction.user.name, interaction.locale, e)
        except Exception as e:
            await interaction.response.send_message(self.msg['exception'], ephemeral=True)
            logger.critical("%s[%s] raise critical exception while applying favorite - %r", interaction.user.name, interaction.locale, e)
