import logging
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands
from discord.ui import View, Button, Modal, TextInput, Select

from bot import db, cmd_messages
from database import model
from utils.color_format import ColorUtils
from utils.data_loader import load_json


class SetupEmbedView(discord.ui.View):
    def __init__(self, colors_data: dict, guild_id: int):
        super().__init__(timeout=180)
        self.guild_id = guild_id
        self.colors_data = colors_data or {}

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
            with db as session:
                query = session.create(model.select_class("select"), {"server_id": interaction.guild.id})
            
            if query:
                with db as session:
                    query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                new_colors = query_result[0] if query_result else {}
                
                new_embed = discord.Embed(title=cmd_messages['setup_select_embed_title'], color=4539717)
                new_embed.description = f"{cmd_messages['setup_select_embed_desc']}\n"
                
                for i in range(1, 11):
                    color_val = new_colors.get(f"hex_{i}")
                    if color_val:
                        new_embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        new_embed.description += f"**{i}.** -\n"
                
                new_embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                new_view = SetupEmbedView(new_colors, interaction.guild.id)
                await interaction.response.send_message(embed=new_embed, view=new_view, ephemeral=True)
            else:
                logging.error(f"Failed to create color list for server {interaction.guild.id}")
        except Exception as e:
            logging.error(f"Error creating color list: {str(e)}")


    async def edit_color_callback(self, interaction: discord.Interaction):
        try:
            with db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                
            colors_data = query_result[0]
            available_colors = []
            
            for i in range(1, 11):
                color_key = f"hex_{i}"
                if colors_data.get(color_key):
                    available_colors.append((i, colors_data[color_key]))
            
            modal = ColorSelectionModal(available_colors)
            await interaction.response.send_modal(modal)
        except Exception as e:
            logging.error(f"Error in edit_color_callback: {str(e)}")


class ColorSelectionModal(Modal):
    def __init__(self, available_colors):
        super().__init__(title=cmd_messages['setup_select_form_title'])
                
        self.color_index = TextInput(
            label=cmd_messages['setup_select_form_index'],
            placeholder=cmd_messages['setup_select_form_pl_index'],
            style=discord.TextStyle.short,
            required=True,
            min_length=1,
            max_length=2
        )
        self.add_item(self.color_index)
        
        self.color_input = TextInput(
            label=cmd_messages['setup_select_form_color'],
            placeholder=cmd_messages['setup_select_form_pl_color'],
            style=discord.TextStyle.short,
            required=False
        )
        self.add_item(self.color_input)
        
        self.available_colors = {str(i): hex_value for i, hex_value in available_colors}
    
    
    async def on_submit(self, interaction: discord.Interaction):
        try:
            selected_index = int(self.color_index.value)
            try:
                if selected_index > 10 or selected_index < 1:
                    raise ValueError
                if self.color_input.value == "":
                    new_color_value = None
                else:     
                    new_color_value = ColorUtils.color_parser(self.color_input.value)
                
                with db as session:
                    session.update(
                        model.select_class("select"),
                        {"server_id": interaction.guild.id},
                        {f"hex_{str(selected_index)}": new_color_value}
                    )
                    
                with db as session:
                    query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                colors_data = query_result[0] if query_result else {}
                
                embed = discord.Embed(title=cmd_messages['setup_select_embed_title'], color=4539717)
                embed.description = f"{cmd_messages['setup_select_embed_desc']}\n"
                for i in range(1, 11):
                    color_val = colors_data.get(f"hex_{i}")
                    if color_val:
                        embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        embed.description += f"**{i}.** -\n"
                
                view = SetupEmbedView(colors_data, interaction.guild.id)
                embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                await interaction.response.send_message(
                    embed=embed,
                    view=view,
                    ephemeral=True
                )
                
            except ValueError:
                with db as session:
                    query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
                colors_data = query_result[0] if query_result else {}
                
                main_embed = discord.Embed(title=cmd_messages['setup_select_embed_title'], color=4539717)
                main_embed.description = f"{cmd_messages['setup_select_embed_desc']}\n"
                main_embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                for i in range(1, 11):
                    color_val = colors_data.get(f"hex_{i}")
                    if color_val:
                        main_embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        main_embed.description += f"**{i}.** -\n"
                
                warn_embed = discord.Embed(title="", description=cmd_messages['color_format'], color=4539717)
                warn_embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
                
                view = SetupEmbedView(colors_data, interaction.guild.id)
                
                await interaction.response.send_message(
                    embeds=[main_embed, warn_embed],
                    view=view,
                    ephemeral=True
                )
                
        except Exception as e:
            embed = discord.Embed(title=cmd_messages['setup_select_embed_title'], color=4539717)
            embed.description = cmd_messages['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
            await interaction.followup.send(embed=embed)
            
            
class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    group = app_commands.Group(name="setup", description="Setup bot on your server")

    @group.command(name="select", description="Setup static colors on server")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        embed = Embed(title=cmd_messages['setup_select_embed_title'], color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)
            with db as session:
                query_result = session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            colors_data = query_result[0] if query_result else {}

            if not any(colors_data.values()):
                embed.description = cmd_messages['setup_select_create_info']
            else:
                embed.description = f"{cmd_messages['setup_select_embed_desc']}\n"
                for i in range(1, 11):
                    color_val = colors_data.get(f"hex_{i}")
                    if color_val:
                        embed.description += f"**{i}.** #{color_val}\n"
                    else:
                        embed.description += f"**{i}.** -\n"

            view = SetupEmbedView(colors_data, interaction.guild.id)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view, ephemeral=True)
        except Exception as e:
            embed.clear_fields()
            embed.description = cmd_messages['exception']
            await interaction.followup.send(embed=embed, ephemeral=True)
            self.bot.logger.critical(f"{interaction.user.name}[{interaction.user.id}] exception: {repr(e)}")


    @group.command(name="toprole", description="Setup top role for color roles")
    @app_commands.describe(role_name="Role name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(self, interaction: discord.Interaction, role_name: discord.Role) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)

            pattern = re.compile(f"color-\\d{{18,19}}")
            top_role = discord.utils.get(interaction.guild.roles, id=role_name.id)

            with db as db_session:
                query = db_session.select(model.guilds_class("guilds"), {"server": interaction.guild.id})

            if top_role.position == 0:
                if query:
                    db.delete(model.guilds_class(f"guilds"), {"server": interaction.guild.id})
                embed.description = cmd_messages['toprole_reset']
            else:
                if query:
                    db.update(model.guilds_class(f"guilds"), {"server": interaction.guild.id},
                              {"role": role_name.id})
                else:
                    db.create(model.guilds_class(f"guilds"), {"server": interaction.guild.id, "role": role_name.id})

                embed.description = cmd_messages['toprole_set'].format(role_name.name)

                for role in interaction.guild.roles:
                    if pattern.match(role.name):
                        role = discord.utils.get(interaction.guild.roles, id=role.id)
                        await role.edit(position=max(1, top_role.position - 1))

                for i, static_role in enumerate(interaction.guild.roles, start=1):
                    if i > 5:
                        break
                    role = discord.utils.get(interaction.guild.roles, name=f"color-static-{i}")
                    if role:
                        await role.edit(position=top_role.position + 1)

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = cmd_messages['err_50013']
            else:
                embed.description = cmd_messages['err_http'].format(e.code, e.text)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")

        except Exception as e:
            embed.clear_fields()
            embed.description = cmd_messages['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user.name}[{interaction.locale}] issued bot command: /setup toprole")

    @toprole.error
    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = cmd_messages["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title="", description=cmd_messages['no_permissions'],
                                         color=4539717, timestamp=datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
