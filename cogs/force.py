import json
import discord
from discord import app_commands, Embed
from discord.ext import commands
from datetime import datetime, timedelta
from config import bot, db, hex_regex, load_yml
from color_format import ColorUtils
import logging
import re
from database import database, model

messages_file = load_yml('assets/messages.yml')
config_file = load_yml('config.yml')


class ForceCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.color = config_file['EMBED_COLOR']

    group = app_commands.Group(name="force", description="Modify the color of specific user")

    @group.command(name="set", description="Setting the color of the user")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(user_name="User name", color="Color to set")
    @app_commands.guild_only()
    async def forceset(self, interaction: discord.Interaction, user_name: discord.Member, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        try:
            await interaction.response.defer(ephemeral=True)

            color_utils = ColorUtils(color)
            color_match = color_utils.color_parser()
            if color_match == -1:
                raise ValueError

            db.connect()
            query = db.select(model.guilds_class("guilds"), {"server": interaction.guild.id})
            db.close()
            role = discord.utils.get(interaction.guild.roles, name=f"color-{user_name.id}")
            if role is None:
                role = await interaction.guild.create_role(name=f"color-{user_name.id}")
            if query:
                top_role = discord.utils.get(interaction.guild.roles, id=query[0].get("role", None))
                if top_role and top_role.position < 1:
                    await role.edit(position=top_role.position - 1)
            await role.edit(colour=discord.Colour(int(color_match, 16)))
            await user_name.add_roles(role)
            embed.description = f"✨ **Color has been set for {user_name.name} to __#{color}__**"
            embed.color = discord.Colour(int(color_match, 16))

        except ValueError:
            embed.description = ("⚠️ **Incorrect color format**\n\n"
                                 "Please use hexadecimal format, e.g. __F5DF4D__ \n"
                                 "or name of [CSS color](https://huetweaker.gitbook.io/docs/main/colors), e.g. __royalblue__")

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = (
                    f"**{messages_file.get('exception')} The bot does not have permissions to perform this operation.**"
                    f" Error may have been caused by misconfiguration of top-role bot (`/toprole`). "
                    f"Notify the server administrator of the occurrence of this error.\n\n"
                    f"💡 Use the `/help` command to learn how to properly configure top role")
            else:
                info_embed.description = (f"**{messages_file.get('exception')} Bot could not perform this operation "
                                          f"due to HTTP discord error.**\n\n"
                                          f"{e.code} - {e.text}")
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")

        except Exception as e:
            embed.clear_fields()
            embed.description = (f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**")
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /force set {user_name.name} {color}")

    @group.command(name="remove", description="Remove the color of the user")
    @app_commands.describe(user_name="User name")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def forceremove(self, interaction: discord.Interaction, user_name: discord.Member) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"color-{user_name.id}")
            if role is not None:
                await user_name.remove_roles(role)
                await role.delete()
                embed.description = f"✨ **Color has been removed for {user_name.name}**"
            else:
                embed.description = f"⚠️ **The user with the given name did not have the color set**"

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /force remove {user_name.name}")

    @group.command(name="purge", description="Remove all color roles (irreversible)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        view = discord.ui.View()
        try:
            await interaction.response.defer(ephemeral=True)

            embed.description = (f"**Are you sure you want to remove all roles with user colors?**\n\n"
                                 f"Choose which type of roles you want to remove.\n"
                                 f"⚠️ **The changes will be irreversible.**")

            individual_button = discord.ui.Button(label="INDIVIDUAL ROLES", style=discord.ButtonStyle.green,
                                           custom_id="individual_roles")
            statinc_button = discord.ui.Button(label="STATIC ROLES", style=discord.ButtonStyle.green,
                                               custom_id="static_roles")
            both_button = discord.ui.Button(label="INDIVIDUAL&STATIC ROLES", style=discord.ButtonStyle.green,
                                            custom_id="both")
            individual_button.callback = self.__confirm_callback
            statinc_button.callback = self.__confirm_callback
            both_button.callback = self.__confirm_callback

            view.add_item(individual_button)
            view.add_item(statinc_button)
            view.add_item(both_button)

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view)
            logging.info(
                f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /force purge")

    @staticmethod
    async def __confirm_callback(interaction: discord.Interaction):
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

            embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
            embed.description = (f"**All roles with colors have been successfully removed**")

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file['exception']} {messages_file['exception_description']}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed, view=view)

    @forceset.error
    @forceremove.error
    @purge.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = f"⚠️ Please cool down. Retry <t:{int(retry_time.timestamp())}:R>"
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title="", description=messages_file.get('no_permissions', ''),
                                         color=config_file['EMBED_COLOR'], timestamp=datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ForceCog(bot))
