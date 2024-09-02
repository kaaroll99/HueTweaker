import logging
import random
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from config import db
from bot_init import langs, bot
from database import model
from utils.color_format import ColorUtils
from utils.data_loader import load_yml


class SetCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name=app_commands.locale_str("set-name"), description=app_commands.locale_str("set"))
    @app_commands.describe(color=app_commands.locale_str("f-color"))
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            lang = load_yml('lang/'+str(interaction.locale)+'.yml') if str(interaction.locale) in langs else load_yml('lang/en-US.yml')
            await interaction.response.defer(ephemeral=True)
            if color.startswith("<@") and color.endswith(">"):
                cleaned_color = re.sub(r"[<>@]", "", color)
                copy_role = discord.utils.get(interaction.guild.roles, name=f"color-{cleaned_color}")
                if copy_role is None:
                    raise ValueError
                else:
                    color = str(copy_role.color)
            elif color == "random":
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            color_utils = ColorUtils(color)
            color_match = color_utils.color_parser()

            if color_match == -1:
                raise ValueError

            with db as db_session:
                query = db_session.select(model.guilds_class("guilds"), {"server": interaction.guild.id})

            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
            if role is None:
                role = await interaction.guild.create_role(name=f"color-{interaction.user.id}",
                                                           colour=discord.Colour(int(color_match, 16)))

            if query:
                top_role = discord.utils.get(interaction.guild.roles, id=query[0].get("role", None))
                if top_role:
                    new_position = max(1, top_role.position - 1)
                    await role.edit(position=new_position, colour=discord.Colour(int(color_match, 16)))

            await interaction.user.add_roles(role)
            embed.description = lang['color_set'].format(color_match)
            embed.color = discord.Colour(int(color_match, 16))

        except ValueError:
            embed.description = lang['color_format']

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = lang['err_50013']
            else:
                embed.description = lang['err_http'].format(e.code, e.text)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")

        except Exception as e:
            embed.clear_fields()
            embed.description = lang['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=lang['footer_message'], icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user.name}[{interaction.locale}] issued bot command: /set {color}")

    @set.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = load_yml('lang/' + str(interaction.locale) + '.yml') if str(interaction.locale) in langs else load_yml(
            'lang/en-US.yml')
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = lang["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
