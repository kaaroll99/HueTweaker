import logging
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from database import model
from utils.color_parse import fetch_color_representation, color_parser

logger = logging.getLogger(__name__)


class ForceCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

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
            color = fetch_color_representation(interaction, color)
            color_match = color_parser(color)

            with self.db as db_session:
                guild_row = db_session.select_one(model.guilds_class("guilds"), {"server": interaction.guild.id})

            async with self.bot.get_guild_lock(interaction.guild.id):
                role = discord.utils.get(interaction.guild.roles, name=f"color-{username.id}")
                role_position = 1
                if role is None:
                    role = await interaction.guild.create_role(name=f"color-{username.id}")
                if guild_row:
                    top_role = discord.utils.get(interaction.guild.roles, id=guild_row.get("role", None))
                    if top_role:
                        role_position = max(1, top_role.position - 1)

                # Fast return jeśli taki sam kolor
                try:
                    if role.colour and int(color_match, 16) == role.colour.value:
                        await username.add_roles(role)
                    else:
                        await role.edit(colour=discord.Colour(int(color_match, 16)), position=role_position)
                        await username.add_roles(role)
                except Exception:
                    await role.edit(colour=discord.Colour(int(color_match, 16)), position=role_position)
                    await username.add_roles(role)
            embed.description = self.msg['force_set_set'].format(username.name, color)
            embed.color = discord.Colour(int(color_match, 16))

        except ValueError:
            embed.description = self.msg['color_format']

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = self.msg['err_50013']
            else:
                embed.description = self.msg['err_http'].format(e.code, e.text)
            logger.critical("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logger.info("%s[%s] issued bot command: /force set %s %s", interaction.user.name, interaction.locale, username.name, color)

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
                embed.description = self.msg['force_remove_remove'].format(username.name)
            else:
                embed.description = self.msg['force_remove_no_color']

        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logger.info("%s[%s] issued bot command: /force remove %s", interaction.user.name, interaction.locale, username.name)

    @group.command(name="purge", description="Remove all color roles (irreversible)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        view = discord.ui.View()
        try:
            await interaction.response.defer(ephemeral=True)

            embed.description = self.msg['purge_confirm']

            individual_button = discord.ui.Button(label=self.msg['bttn_ind'], style=discord.ButtonStyle.green,
                                                  custom_id="individual_roles")
            statinc_button = discord.ui.Button(label=self.msg['bttn_stat'], style=discord.ButtonStyle.green,
                                               custom_id="static_roles")
            both_button = discord.ui.Button(label=self.msg['bttn_both'], style=discord.ButtonStyle.green,
                                            custom_id="both")
            individual_button.callback = self.__confirm_callback
            statinc_button.callback = self.__confirm_callback
            both_button.callback = self.__confirm_callback

            view.add_item(individual_button)
            view.add_item(statinc_button)
            view.add_item(both_button)

        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view)
            logger.info("%s[%s] issued bot command: /force purge", interaction.user.name, interaction.locale)

    async def __confirm_callback(self, interaction: discord.Interaction):
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        view = discord.ui.View()

        async def del_static_roles():
            with self.db as db_session:
                db_session.delete(model.select_class("select"), {"server_id": interaction.guild.id})
                

        async def del_individual_roles():
            pattern = re.compile(f"color-\\d{18,19}")
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

            embed.description = self.msg['purge_ok']

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=self.msg['exception'], value=f"", inline=False)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed, view=view)

    @forceset.error
    @forceremove.error
    @purge.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title="", description=self.msg['no_permissions'],
                                         color=4539717, timestamp=datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ForceCog(bot))
