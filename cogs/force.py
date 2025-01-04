import logging
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from bot import db, cmd_messages
from database import model
from utils.color_format import ColorUtils
from utils.color_imput_type import color_type
from utils.data_loader import load_yml


class ForceCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    group = app_commands.Group(name="force", description="Modify the color of specific user")

    @group.command(name="set", description="Setting the color of the user")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(username="Username", color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    @app_commands.guild_only()
    async def forceset(self, interaction: discord.Interaction, username: discord.Member, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)
            color = color_type(interaction, color)
            color_match = ColorUtils.color_parser(color)

            with db as db_session:
                query = db_session.select(model.guilds_class("guilds"), {"server": interaction.guild.id})

            role = discord.utils.get(interaction.guild.roles, name=f"color-{username.id}")
            role_position = 1
            if role is None:
                role = await interaction.guild.create_role(name=f"color-{username.id}")
            if query:
                top_role = discord.utils.get(interaction.guild.roles, id=query[-1].get("role", None))
                if top_role:
                    role_position = max(1, top_role.position - 1)
            await role.edit(colour=discord.Colour(int(color_match, 16)), position=role_position)

            await username.add_roles(role)
            embed.description = cmd_messages['force_set_set'].format(username.name, color)
            embed.color = discord.Colour(int(color_match, 16))

        except ValueError:
            embed.description = cmd_messages['color_format']

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
                f"{interaction.user.name}[{interaction.locale}] issued bot command: /force set {username.name} {color}")

    @group.command(name="remove", description="Remove the color of the user")
    @app_commands.describe(username="Username")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def forceremove(self, interaction: discord.Interaction, username: discord.Member) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"color-{username.id}")
            if role is not None:
                await username.remove_roles(role)
                await role.delete()
                embed.description = cmd_messages['force_remove_remove'].format(username.name)
            else:
                embed.description = cmd_messages['force_remove_no_color']

        except Exception as e:
            embed.clear_fields()
            embed.description = cmd_messages['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user.name}[{interaction.locale}] issued bot command: /force remove {username.name}")

    @group.command(name="purge", description="Remove all color roles (irreversible)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        view = discord.ui.View()
        try:
            await interaction.response.defer(ephemeral=True)

            embed.description = cmd_messages['purge_confirm']

            individual_button = discord.ui.Button(label=cmd_messages['bttn_ind'], style=discord.ButtonStyle.green,
                                                  custom_id="individual_roles")
            statinc_button = discord.ui.Button(label=cmd_messages['bttn_stat'], style=discord.ButtonStyle.green,
                                               custom_id="static_roles")
            both_button = discord.ui.Button(label=cmd_messages['bttn_both'], style=discord.ButtonStyle.green,
                                            custom_id="both")
            individual_button.callback = self.__confirm_callback
            statinc_button.callback = self.__confirm_callback
            both_button.callback = self.__confirm_callback

            view.add_item(individual_button)
            view.add_item(statinc_button)
            view.add_item(both_button)

        except Exception as e:
            embed.clear_fields()
            embed.description = cmd_messages['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view)
            logging.info(
                f"{interaction.user.name}[{interaction.locale}] issued bot command: /force purge")

    @staticmethod
    async def __confirm_callback(interaction: discord.Interaction):
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        view = discord.ui.View()

        async def del_static_roles():
            for i, static_role in enumerate(interaction.guild.roles, start=1):
                if i > 5:
                    break
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{i}")
                if role:
                    await role.delete()

        async def del_individual_roles():
            pattern = re.compile(f"color-\\d{{18,19}}")
            for role in interaction.guild.roles:
                if pattern.match(role.name):
                    role = discord.utils.get(interaction.guild.roles, id=role.id)
                    await role.delete()

        try:
            if interaction.data['custom_id'] == 'individual_roles':
                await del_individual_roles()
            elif interaction.data['custom_id'] == 'static_roles':
                await del_static_roles()
            elif interaction.data['custom_id'] == 'both':
                await del_individual_roles()
                await del_static_roles()

            embed.description = cmd_messages['purge_ok']

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=cmd_messages['exception'], value=f"", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed, view=view)

    @forceset.error
    @forceremove.error
    @purge.error
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
    await bot.add_cog(ForceCog(bot))
