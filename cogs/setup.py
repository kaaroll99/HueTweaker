import logging
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands
from discord.ui import Button, Modal, TextInput

from database import model
from utils.color_parse import color_parser
from views.global_view import GlobalLayout
from views.cooldown import CooldownLayout

logger = logging.getLogger(__name__)


class SetupEmbedView(discord.ui.View):
    def __init__(self, colors_data: dict, guild_id: int, bot: commands.Bot):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.colors_data = colors_data or {}
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

        if not any(self.colors_data.values()):
            create_button = Button(label="CREATE", style=discord.ButtonStyle.primary, custom_id="create_button")
            create_button.callback = self.create_callback
            self.add_item(create_button)
        else:
            edit_button = Button(label="ADD/EDIT COLOR", style=discord.ButtonStyle.success, custom_id="edit_color")
            edit_button.callback = self.edit_color_callback
            self.add_item(edit_button)

    async def create_callback(self, interaction: discord.Interaction):
        try:
            with self.db as session:
                query = session.create(model.select_class("select"), {"server_id": interaction.guild.id})

            if query:
                with self.db as session:
                    query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                new_colors = query_result[0] if query_result else {}

                new_embed = discord.Embed(title=self.msg['setup_select_embed_title'], color=4539717)
                new_embed.description = f"{self.msg['setup_select_embed_desc']}\n"

                for i in range(1, 11):
                    color_val = new_colors.get(f"hex_{i}")
                    if color_val:
                        new_embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        new_embed.description += f"**{i}.** -\n"

                new_embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                new_view = SetupEmbedView(new_colors, interaction.guild.id, self.bot)
                await interaction.response.send_message(embed=new_embed, view=new_view, ephemeral=True)
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
            try:
                import re
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

                embed = discord.Embed(title=self.msg['setup_select_embed_title'], color=4539717)
                embed.description = f"{self.msg['setup_select_embed_desc']}\n"
                for i in range(1, 11):
                    color_val = colors_data.get(f"hex_{i}")
                    if color_val:
                        embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        embed.description += f"**{i}.** -\n"

                view = SetupEmbedView(colors_data, interaction.guild.id, self.bot)
                embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                await interaction.response.send_message(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )

            except ValueError:
                with self.db as session:
                    query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                colors_data = query_result[0] if query_result else {}

                main_embed = discord.Embed(title=self.msg['setup_select_embed_title'], color=4539717)
                main_embed.description = f"{self.msg['setup_select_embed_desc']}\n"
                main_embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                for i in range(1, 11):
                    color_val = colors_data.get(f"hex_{i}")
                    if color_val:
                        main_embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        main_embed.description += f"**{i}.** -\n"

                warn_embed = discord.Embed(title="", description=self.msg['color_format'], color=4539717)
                warn_embed.set_image(url="https://i.imgur.com/rXe4MHa.png")

                view = SetupEmbedView(colors_data, interaction.guild.id, self.bot)

                await interaction.response.send_message(
                    embeds=[main_embed, warn_embed],
                    view=view,
                    ephemeral=True
                )

        except Exception as e:
            embed = discord.Embed(title=self.msg['setup_select_embed_title'], color=4539717)
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
            await interaction.followup.send(embed=embed)


class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    group = app_commands.Group(name="setup", description="Setup bot on your server")

    @group.command(name="select", description="Setup static colors on server")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        embed = Embed(title=self.msg['setup_select_embed_title'], color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)
            with self.db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            colors_data = query_result[0] if query_result else {}

            if not any(colors_data.values()):
                embed.description = self.msg['setup_select_create_info']
            else:
                embed.description = f"{self.msg['setup_select_embed_desc']}\n"
                for i in range(1, 11):
                    color_val = colors_data.get(f"hex_{i}")
                    if color_val:
                        embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        embed.description += f"**{i}.** -\n"

            view = SetupEmbedView(colors_data, interaction.guild.id, self.bot)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            await interaction.followup.send(embed=embed, ephemeral=True)
            logger.critical("%s[%s] exception: %r", interaction.user.name, interaction.user.id, e)

    @group.command(name="toprole", description="Setup top role for color roles")
    @app_commands.describe(role_name="Role name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(self, interaction: discord.Interaction, role_name: discord.Role) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            pattern = re.compile(r"color-\\d{18,19}")
            top_role = discord.utils.get(interaction.guild.roles, id=role_name.id)

            with self.db as db_session:
                guild_row = db_session.select_one(model.guilds_class("guilds"), {"server": interaction.guild.id})

            if top_role.position == 0:
                if guild_row:
                    self.db.delete(model.guilds_class("guilds"), {"server": interaction.guild.id})
                description = self.msg['toprole_reset']
            else:
                if guild_row:
                    self.db.update(model.guilds_class("guilds"), {"server": interaction.guild.id}, {"role": role_name.id})
                else:
                    self.db.create(model.guilds_class("guilds"), {"server": interaction.guild.id, "role": role_name.id})

                description = self.msg['toprole_set'].format(role_name.name)

                for role in interaction.guild.roles:
                    if pattern.match(role.name):
                        role = discord.utils.get(interaction.guild.roles, id=role.id)
                        await role.edit(position=max(1, top_role.position - 1))

            view = GlobalLayout(messages=self.msg, description=description, docs_page="commands/setup-toprole")
            await interaction.followup.send(view=view)

        except discord.HTTPException as e:
            if e.code == 50013:
                err_description = self.msg['err_50013']
            else:
                err_description = self.msg['err_http'].format(e.code, e.text)
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/setup-toprole")
            logger.critical("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/setup-toprole")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /setup toprole", interaction.user.name, interaction.locale)

    @toprole.error
    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            view = CooldownLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title="", description=self.msg['no_permissions'],
                                         color=4539717, timestamp=datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
