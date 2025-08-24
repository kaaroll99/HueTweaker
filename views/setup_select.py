import logging
import re
import discord
from discord.ext import commands
from discord.ui import Button, Modal, TextInput

from database import model
from utils.color_parse import color_parser

logger = logging.getLogger(__name__)


class SetupView(discord.ui.LayoutView):
    def __init__(self, colors_data: dict, guild_id: int, bot: commands.Bot):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.colors_data = colors_data or {}
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

        container = discord.ui.Container(accent_colour=discord.Color(0xFCF5AB))

        container.add_item(discord.ui.TextDisplay(self.msg['setup_select_embed_desc']))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))
        color_list = ""
        for i in range(1, 11):
            color_val = self.colors_data.get(f"hex_{i}")
            if color_val:
                color_list += f"**{i}.** #{color_val}\n"
            else:
                color_list += f"**{i}.** -\n"

        container.add_item(discord.ui.TextDisplay(color_list))

        # # obrazek
        # gallery = discord.ui.MediaGallery()
        # gallery.add_item(media="https://i.imgur.com/rXe4MHa.png")
        # container.add_item(gallery)

        # separator
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        docs_button = discord.ui.Button(
            label="See documentation",
            style=discord.ButtonStyle.link,
            emoji="<:docs:1362879505613586643>",
            url="https://huetweaker.gitbook.io/docs/commands/setup-select"
        )
        if not any(self.colors_data.values()):
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

        self.add_item(container)

    async def create_callback(self, interaction: discord.Interaction):
        try:
            with self.db as session:
                query = session.create(model.select_class("select"), {"server_id": interaction.guild.id})

            if query:
                with self.db as session:
                    query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                new_colors = query_result[0] if query_result else {}

                new_view = SetupView(new_colors, interaction.guild.id, self.bot)
                await interaction.response.edit_message(view=new_view)
            else:
                logger.error("Failed to create color list for server %s", interaction.guild.id)
        except Exception as e:
            logger.error("Error creating color list: %s", str(e))

    async def edit_color_callback(self, interaction: discord.Interaction):
        try:
            with self.db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})

            colors_data = query_result[0]
            available_colors = []

            for i in range(1, 11):
                color_key = f"hex_{i}"
                if colors_data.get(color_key):
                    available_colors.append((i, colors_data[color_key]))

            modal = ColorSelectionModal(available_colors, self.bot)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logger.error("Error in edit_color_callback: %s", str(e))


class ColorSelectionModal(Modal):
    def __init__(self, available_colors, bot: commands.Bot):
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
            required=False
        )
        self.add_item(self.color_input)

        self.available_colors = {str(i): hex_value for i, hex_value in available_colors}

    async def on_submit(self, interaction: discord.Interaction):
        try:
            index_value = int(re.sub(r"\D", "", self.color_index.value))
            if not isinstance(index_value, int) or index_value > 10 or index_value < 1:
                raise ValueError
            if self.color_input.value == "":
                new_color_value = None
            else:
                new_color_value = color_parser(self.color_input.value)

            with self.db as session:
                session.update(
                    model.select_class("select"),
                    {"server_id": interaction.guild.id},
                    {f"hex_{str(index_value)}": new_color_value}
                )

            with self.db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            colors_data = query_result[0] if query_result else {}

            new_view = SetupView(colors_data, interaction.guild.id, self.bot)
            await interaction.response.edit_message(view=new_view)

        except ValueError:
            with self.db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            colors_data = query_result[0] if query_result else {}

            warn_text = self.msg['color_format']

            # zamiast dwóch embedów – w view dorzucamy dodatkowy TextDisplay
            new_view = SetupView(colors_data, interaction.guild.id, self.bot)
            new_view.add_item(discord.ui.TextDisplay(warn_text))

            await interaction.response.edit_message(view=new_view)

        except Exception as e:
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
            err_view = discord.ui.LayoutView()
            container = discord.ui.Container(accent_colour=discord.Color.red())
            container.add_item(discord.ui.TextDisplay(self.msg['exception']))
            err_view.add_item(container)
            await interaction.response.edit_message(view=err_view)
