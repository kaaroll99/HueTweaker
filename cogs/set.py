import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from bot import db, cmd_messages
from database import model
from utils.color_parse import fetch_color_representation, color_parser
from utils.cooldown_check import is_user_on_cooldown


async def dynamic_cooldown(interaction: discord.Interaction):
    return await is_user_on_cooldown(interaction)


class SetCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="set", description="Set color using HEX code or CSS color name")
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    @app_commands.checks.dynamic_cooldown(dynamic_cooldown, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)

            color = fetch_color_representation(interaction, color)
            color_match = color_parser(color)

            with db as db_session:
                query = db_session.select(model.guilds_class("guilds"), {"server": interaction.guild.id})

            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
            role_position = 1
            if role is None:
                role = await interaction.guild.create_role(name=f"color-{interaction.user.id}")
            if query:
                top_role = discord.utils.get(interaction.guild.roles, id=query[-1].get("role", None))
                if top_role:
                    role_position = max(1, top_role.position - 1)
            await role.edit(colour=discord.Colour(int(color_match, 16)), position=role_position)

            await interaction.user.add_roles(role)
            embed.description = cmd_messages['color_set'].format(color_match)
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
            logging.info(f"{interaction.user.name}[{interaction.locale}] issued bot command: /set {color}")

    @set.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = cmd_messages["cool_down_with_api"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
