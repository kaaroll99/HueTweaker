import json
import discord
from discord import app_commands, Embed
from discord.ext import commands
from datetime import datetime, timedelta
from config import bot, db, hex_regex, load_yml
import logging
from color_format import ColorUtils
import re
from database import database, model

messages_file = load_yml('assets/messages.yml')
config_file = load_yml('config.yml')
token_file = load_yml('token.yml')


class SetCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="set", description="Set color using HEX code or CSS color name")
    @app_commands.describe(color="Color HEX or CSS color name")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
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

            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
            if role is None:
                role = await interaction.guild.create_role(name=f"color-{interaction.user.id}")

            if query:
                top_role = discord.utils.get(interaction.guild.roles, id=query[0].get("role", None))
                if top_role:
                    if top_role.position <= 1:
                        await role.edit(position=top_role.position)
                    else:
                        await role.edit(position=top_role.position - 1)

            await role.edit(colour=discord.Colour(int(color_match, 16)))
            await interaction.user.add_roles(role)
            embed.description = f"✨ **Color has been set to __#{color_match}__**"
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
            logging.info(f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /set {color}")

    @set.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = f"⚠️ Please cool down. Retry <t:{int(retry_time.timestamp())}:R>"
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
