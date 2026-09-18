import logging

import discord

from constants import ACCENT_COLOR
from database import model
from utils.color_format import ColorUtils, format_color_label
from utils.history_manager import update_history
from utils.role_manager import apply_color_role
from views.global_view import GlobalLayout, error_description, make_docs_button, make_invite_button, safe_defer
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
                self.msg['revert_not_author'], ephemeral=True)
            return

        slot = int(select.values[0])
        if not await safe_defer(interaction):
            return

        try:
            await self.bot.db.update(model.Favorites, {"user_id": interaction.user.id}, {f"hex_{slot}": None})

            row = await self.bot.db.select_one(model.Favorites, {"user_id": interaction.user.id})
            colors = extract_favorite_colors(row)

            if not colors:
                view = GlobalLayout(messages=self.msg, description=self.msg['favorites_no_colors'], docs_page=self.docs_page)
                await interaction.edit_original_response(view=view, attachments=[])
                return

            view, file = FavoritesView.build(self.msg, self.bot, self.author_id, colors, self.nick, self.docs_page)
            await interaction.edit_original_response(view=view, attachments=[file])
            logger.info("%s[%s] removed a favorite color (slot %s)", interaction.user.name, interaction.locale, slot)

        except Exception as e:
            logger.critical("%s[%s] raise critical exception while removing favorite - %r", interaction.user.name, interaction.locale, e)
            try:
                await interaction.followup.send(error_description(self.msg, e), ephemeral=True)
            except discord.HTTPException:
                pass


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
                self.msg['revert_not_author'], ephemeral=True)
            return

        if not await safe_defer(interaction, ephemeral=True, thinking=True):
            return

        label = format_color_label(color_int)
        try:
            result = await apply_color_role(
                interaction.guild, interaction.user, color_int, None, self.bot.db, self.bot.user.id
            )

            if result.changed:
                description = self.msg['favorites_applied'].format(label)
                await update_history(self.bot.db, interaction.user.id, interaction.guild.id, color_int)
            else:
                description = self.msg['color_same']

            view = Layout.from_result(self.msg, result, color_int, interaction.user.id, description)
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] applied favorite color %s", interaction.user.name, interaction.locale, label)

        except Exception as e:
            logger.warning("%s[%s] failed to apply favorite: %r", interaction.user.name, interaction.locale, e)
            try:
                await interaction.followup.send(error_description(self.msg, e), ephemeral=True)
            except discord.HTTPException:
                pass
