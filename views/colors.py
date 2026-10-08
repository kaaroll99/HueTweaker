import logging
from functools import lru_cache
from io import BytesIO

import discord

from constants import ACCENT_COLOR
from utils.color_format import ColorUtils, color_presets
from utils.data_loader import load_json
from views.global_view import make_docs_button, make_invite_button

logger = logging.getLogger(__name__)

GRADIENTS = "Gradients"

GROUP_EMOJI = {
    GRADIENTS: "🌈", "Red": "🟥", "Pink": "🩷", "Orange": "🟧", "Yellow": "🟨", "Purple": "🟪",
    "Green": "🟩", "Blue": "🟦", "Brown": "🟫", "White": "⬜", "Gray": "⬛",
}


@lru_cache(maxsize=1)
def color_groups() -> dict[str, list[str]]:
    return load_json("assets/css-color-groups.json")


def book_groups() -> dict[str, int]:
    return {GRADIENTS: len(color_presets()), **{group: len(names) for group, names in color_groups().items()}}


@lru_cache(maxsize=None)
def _group_png(group: str) -> bytes:
    if group == GRADIENTS:
        image = ColorUtils.generate_preset_book_image()
    else:
        image = ColorUtils.generate_color_book_image(color_groups()[group])
    return ColorUtils.to_bytes(image).getvalue()


def group_file(group: str) -> discord.File:
    return discord.File(fp=BytesIO(_group_png(group)), filename=f"colors_{group.lower()}.png")


class GroupSelect(discord.ui.ActionRow['ColorBookView']):
    def __init__(self, selected: str):
        super().__init__()
        self.children[0].options = [
            discord.SelectOption(
                label=group if group == GRADIENTS else f"{group} colors",
                value=group,
                emoji=GROUP_EMOJI.get(group),
                description=f"{count} presets" if group == GRADIENTS else f"{count} colors",
                default=group == selected,
            )
            for group, count in book_groups().items()
        ]

    @discord.ui.select(
        placeholder="Choose a color group...",
        min_values=1,
        max_values=1,
        options=[]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await self.view.show_group(interaction, select.values[0])


class ColorBookView(discord.ui.LayoutView):
    def __init__(self, messages, group: str, author_id: int | None = None, docs_page: str = "main/colors"):
        super().__init__()
        self.msg = messages
        self.group = group
        self.author_id = author_id
        self.docs_page = docs_page
        self.file = group_file(group)

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        if group == GRADIENTS:
            title = self.msg['colors_gradients_title']
        else:
            title = self.msg['colors_title'].format(group, color_groups()[group][0].lower())
        container.add_item(discord.ui.TextDisplay(title))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="attachment://" + self.file.filename)
        container.add_item(gallery)

        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        container.add_item(GroupSelect(group))
        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button()))

        self.add_item(container)

    async def show_group(self, interaction: discord.Interaction, group: str) -> None:
        if self.author_id is not None and interaction.user.id != self.author_id:
            await interaction.response.send_message(self.msg['revert_not_author'], ephemeral=True)
            return

        view = ColorBookView(self.msg, group, self.author_id, self.docs_page)
        try:
            await interaction.response.edit_message(view=view, attachments=[view.file])
        except (discord.NotFound, discord.InteractionResponded) as e:
            logger.warning("%s[%s] could not update colors view: %s", interaction.user.name, interaction.user.id, e)
