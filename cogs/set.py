from datetime import datetime, timedelta
from typing import Tuple, Optional
import discord
from discord import app_commands
from discord.ext import commands

from database import model
from utils.color_parse import fetch_color_representation, color_parser
from utils.cooldown_check import is_user_on_cooldown

from views.set import Layout
from views.global_view import GlobalLayout

import logging

logger = logging.getLogger(__name__)


async def dynamic_cooldown(interaction: discord.Interaction):
    return await is_user_on_cooldown(interaction)


class SetCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    @app_commands.command(name="set", description="Set color using HEX code or CSS color name")
    @app_commands.describe(
        color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)",
        secondary_color="Secondary color for gradient (optional)"
    )
    @app_commands.checks.dynamic_cooldown(dynamic_cooldown, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str, secondary_color: str = None) -> None:
        description = ""
        undo_lock = False
        prev_colors: Optional[Tuple[Optional[int], Optional[int]]] = None
        try:
            await interaction.response.defer(ephemeral=True)

            primary_hex = color_parser(fetch_color_representation(interaction, color))
            secondary_hex = color_parser(fetch_color_representation(interaction, secondary_color)) if secondary_color else None

            if primary_hex is None or (secondary_hex is None and secondary_color):
                raise ValueError

            primary_val = int(primary_hex, 16)
            secondary_val = int(secondary_hex, 16) if secondary_hex else None
            new_colors_val: Tuple[int, Optional[int]] = (primary_val, secondary_val)

            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")

            if role is None:
                role_position = 1
                with self.db as db_session:
                    guild_row = db_session.select_one(model.guilds_class("guilds"), {"server": interaction.guild.id})
                if guild_row:
                    top_role = discord.utils.get(interaction.guild.roles, id=guild_row.get("role", None))
                    if top_role:
                        role_position = max(1, top_role.position - 1)

                role = await interaction.guild.create_role(
                    name=f"color-{interaction.user.id}",
                    color=discord.Color(new_colors_val[0]),
                    secondary_color=discord.Color(new_colors_val[1]) if new_colors_val[1] is not None else None
                )
                if role_position > 1:
                    await role.edit(position=role_position)

                display_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
                description = self.msg['color_set'].format(display_color)
            else:
                current_colors_val = (
                    role.color.value if role.color else None,
                    role.secondary_color.value if role.secondary_color else None
                )

                if current_colors_val != new_colors_val:
                    prev_colors = current_colors_val
                    await role.edit(
                        color=discord.Color(new_colors_val[0]),
                        secondary_color=discord.Color(new_colors_val[1]) if new_colors_val[1] is not None else None
                    )
                    display_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
                    description = self.msg['color_set'].format(display_color)
                else:
                    description = self.msg['color_same']
                    undo_lock = True

            if role and role not in interaction.user.roles:
                await interaction.user.add_roles(role)

            view = Layout(
                messages=self.msg,
                color=discord.Color(new_colors_val[0]),
                display_color=f"{color}" + (f", {secondary_color}" if secondary_color else ""),
                prev_colors=prev_colors,
                role_id=role.id if role else None,
                author_id=interaction.user.id,
                description=description,
                undo_lock=undo_lock
            )

            await interaction.followup.send(view=view)

        except ValueError:
            view = GlobalLayout(messages=self.msg, description=self.msg['color_format'], docs_page="commands/set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] issued bot command: /set (invalid format)", interaction.user.name, interaction.user.id)

        except discord.HTTPException as e:
            if e.code == 50013:
                err_description = self.msg['err_50013']
            elif e.code == 670006:
                err_description = self.msg['err_670006']
            else:
                err_description = self.msg['err_http'].format(e.code, e.text)
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.error("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            log_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
            logger.info("%s[%s] issued bot command: /set %s", interaction.user.name, interaction.locale, log_color)

    @set.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down_with_api"].format(int(retry_time.timestamp()))
            view = GlobalLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
