import json
import discord
from discord import app_commands, Embed, ui
from discord.ext import commands
from datetime import datetime, timedelta
import config
from config import bot, db, hex_regex
import logging
import re
from database import database, model

messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')

class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    group = app_commands.Group(name="setup", description="Setup bot on your server")

    @group.command(name="select", description="Setup static colors on server")
    @app_commands.checks.cooldown(1, 5.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction, color_1: str, color_2: str,
                     color_3: str = None, color_4: str = None, color_5: str = None) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        try:
            await interaction.response.defer(ephemeral=True)

            local_vars = locals()
            local_vars.pop('self')
            local_vars.pop('interaction')

            with open("assets/css-color-names.json", "r", encoding="utf-8") as file:
                data = json.load(file)

            db.connect()
            query = db.select(model.guilds_class("guilds"), {"server": interaction.guild.id})
            db.close()

            for i, color in enumerate(local_vars.values(), start=1):
                if i > 5:
                    break
                if color:
                    color_match = color
                    color_match = str(color_match).lower().replace(" ", "")
                    if color_match in map(lambda x: str(x).lower(), data.keys()):
                        color_match = data[color_match]
                    elif config.hex_regex.match(color_match):
                        if len(color_match.strip("#")) == 3:
                            color_match = ''.join([x * 2 for x in color_match.strip("#")])
                        else:
                            color_match = color_match.strip("#")
                    else:
                        raise ValueError
                    role = discord.utils.get(interaction.guild.roles, name=f"color-static-{i}")
                    if role is None:
                        role = await interaction.guild.create_role(name=f"color-static-{i}",
                                                                   color=discord.Colour(int(color_match, 16)))
                    else:
                        await role.edit(colour=discord.Colour(int(color_match, 16)))
                    if query:
                        top_role = discord.utils.get(interaction.guild.roles, id=query[0]["role"])
                        if top_role:
                            await role.edit(position=top_role.position + 1)

                    embed.add_field(name=f"", value=f"{role.mention} > {color_match}", inline=False)
                else:
                    role = discord.utils.get(interaction.guild.roles, name=f"color-static-{i}")
                    if role:
                        await role.delete()

        except ValueError:
            embed.clear_fields()
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
            logging.info(f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /setup select")

    @group.command(name="toprole", description="Setup top role for color roles")
    @app_commands.describe(role_name="Role name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(self, interaction: discord.Interaction, role_name: discord.Role) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        try:
            await interaction.response.defer(ephemeral=True)

            pattern = re.compile(f"color-\\d{{18,19}}")
            top_role = discord.utils.get(interaction.guild.roles, id=role_name.id)

            for role in interaction.guild.roles:
                if pattern.match(role.name):
                    role = discord.utils.get(interaction.guild.roles, id=role.id)
                    if top_role.position <= 1:
                        await role.edit(position=top_role.position)
                    else:
                        await role.edit(position=top_role.position - 1)

            for i, static_role in enumerate(interaction.guild.roles, start=1):
                if i > 5:
                    break
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{i}")
                if role:
                    await role.edit(position=top_role.position + 1)


            db.connect()
            query = db.select(model.guilds_class("guilds"), {"server": interaction.guild.id})
            if top_role.position == 0:
                if query:
                    db.delete(model.guilds_class(f"guilds"), {"server": interaction.guild.id})

                embed.description = (f"✨ **Top role settings have been reset**\n\n"
                                     f"💡 Please remember the selected role should be positioned below the bot's highest role."
                                     f" Otherwise it will cause errors when setting the username color.")
            else:
                if query:
                    db.update(model.guilds_class(f"guilds"), {"server": interaction.guild.id},
                              {"role": role_name.id})
                else:
                    db.create(model.guilds_class(f"guilds"), {"server": interaction.guild.id, "role": role_name.id})

                embed.description = (f"✨ **Top role has been set for __{role_name.name}__**\n\n"
                                     f"💡 Remember that the selected role should be under the highest role the bot has."
                                     f" Otherwise, it will cause errors when setting the username color.")
            db.close()

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = (
                    f"**{messages_file.get('exception')} The bot does not have permissions to perform this operation.**"
                    f" Error may have been caused by misconfiguration of top-role bot (`/toprole`). "
                    f"Make sure you have chosen the right role for the bot.\n\n"
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
                f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /setup toprole")

    @toprole.error
    @select.error
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
    await bot.add_cog(SetupCog(bot))
