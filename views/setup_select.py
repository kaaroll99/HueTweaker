import logging
import re

import discord
from discord.ext import commands
from discord.ui import Button, Modal, TextInput

from constants import ACCENT_COLOR
from database import model
from utils.color_format import format_color_label
from utils.color_parse import BLACK_HEX, NEAR_BLACK_HEX, color_parser
from views.global_view import error_description, make_docs_button

logger = logging.getLogger(__name__)

PALETTE_SIZE = 10


def _error_view(text: str) -> discord.ui.LayoutView:
    view = discord.ui.LayoutView()
    container = discord.ui.Container(accent_colour=discord.Color.red())
    container.add_item(discord.ui.TextDisplay(text))
    view.add_item(container)
    return view


async def refresh_setup_view(interaction: discord.Interaction, bot: commands.Bot, warning: str | None = None) -> None:
    """Re-render the panel from the database (optionally with a warning line)."""
    select_obj = await bot.db.select_one(model.Select, {"server_id": interaction.guild.id})
    await interaction.response.edit_message(view=SetupView(select_obj or {}, interaction.guild.id, bot, warning=warning))


class SetupView(discord.ui.LayoutView):
    def __init__(self, colors_data: dict, guild_id: int, bot: commands.Bot, warning: str | None = None):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.colors_data = colors_data or {}
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))

        container.add_item(discord.ui.TextDisplay(self.msg['setup_select_embed_desc']))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        color_list = ""
        for i in range(1, PALETTE_SIZE + 1):
            color_val = self.colors_data.get(f"hex_{i}")
            if color_val:
                color_list += f"**{i}.** {format_color_label(color_val)}\n"
            else:
                color_list += f"**{i}.** -\n"

        container.add_item(discord.ui.TextDisplay(color_list))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        docs_button = make_docs_button("commands/setup-select")
        has_row = bool(self.colors_data)
        if not has_row:
            create_button = Button(
                label="Create color list",
                style=discord.ButtonStyle.primary,
                emoji="<:star:1362879443625971783>",
                custom_id="create_button")
            create_button.callback = self.create_callback
            container.add_item(discord.ui.ActionRow(create_button, docs_button))
        else:
            edit_button = Button(
                label="Add/Edit color on list",
                style=discord.ButtonStyle.primary,
                emoji="<:star:1362879443625971783>",
                custom_id="edit_color")
            edit_button.callback = self.edit_color_callback
            container.add_item(discord.ui.ActionRow(edit_button, docs_button))

        if warning:
            container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
            container.add_item(discord.ui.TextDisplay(warning))

        self.add_item(container)

    async def create_callback(self, interaction: discord.Interaction):
        try:
            if await self.db.select_one(model.Select, {"server_id": interaction.guild.id}) is None:
                await self.db.create(model.Select, {"server_id": interaction.guild.id})
            await refresh_setup_view(interaction, self.bot)
        except Exception as e:
            logger.error("Error creating color list for guild %s: %r", interaction.guild.id, e)
            await interaction.response.edit_message(view=_error_view(error_description(self.msg, e)))

    async def edit_color_callback(self, interaction: discord.Interaction):
        try:
            await interaction.response.send_modal(ColorSelectionModal(self.bot))
        except Exception as e:
            logger.error("Error opening the color modal for guild %s: %r", interaction.guild.id, e)


class ColorSelectionModal(Modal):
    def __init__(self, bot: commands.Bot):
        super().__init__(title=bot.messages['setup_select_form_title'])
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

        self.color_index = TextInput(
            label=self.msg['setup_select_form_index'],
            placeholder=self.msg['setup_select_form_pl_index'],
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.color_index)

        self.color_input = TextInput(
            label=self.msg['setup_select_form_color'],
            placeholder=self.msg['setup_select_form_pl_color'],
            style=discord.TextStyle.short,
            required=False,
            max_length=32,
        )
        self.add_item(self.color_input)

    async def on_submit(self, interaction: discord.Interaction):
        try:
            digits = re.sub(r"\D", "", self.color_index.value)
            index_value = int(digits) if digits else 0
            if not 1 <= index_value <= PALETTE_SIZE:
                raise ValueError

            raw = self.color_input.value.strip()
            if raw == "":
                new_color_value = None
            else:
                parsed = color_parser(raw)
                if parsed is None:
                    # Invalid input must not silently clear the slot.
                    raise ValueError
                new_color_value = NEAR_BLACK_HEX if parsed == BLACK_HEX else parsed

            criteria = {"server_id": interaction.guild.id}
            await self.db.upsert(model.Select, criteria, {f"hex_{index_value}": new_color_value})
            await refresh_setup_view(interaction, self.bot)

        except ValueError:
            await refresh_setup_view(interaction, self.bot, warning=self.msg['color_format'])

        except Exception as e:
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
            await interaction.response.edit_message(view=_error_view(error_description(self.msg, e)))
