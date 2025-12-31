import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional

import discord
from discord import app_commands
from discord.ext import commands

from database import model
from utils.history_manager import update_history
from utils.color_parse import fetch_color_representation, color_parser, check_black
from views.cooldown import CooldownLayout
from views.global_view import GlobalLayout
from views.purge import PurgeView
from views.set import Layout

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
    @app_commands.describe(username="Username",
                           color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)",
                           secondary_color="Secondary color for gradient (optional)")
    @app_commands.guild_only()
    async def forceset(self, interaction: discord.Interaction, username: discord.Member, color: str, secondary_color: str = None) -> None:
        description = ""
        undo_lock = False
        prev_colors: Optional[Tuple[Optional[int], Optional[int]]] = None
        try:
            await interaction.response.defer(ephemeral=True)

            primary_hex = color_parser(fetch_color_representation(interaction, color))
            secondary_hex = color_parser(fetch_color_representation(interaction, secondary_color)) if secondary_color else None
            primary_hex, secondary_hex, is_black = check_black(primary_hex, secondary_hex)

            if primary_hex is None or (secondary_hex is None and secondary_color):
                raise ValueError

            primary_val = int(primary_hex, 16)
            secondary_val = int(secondary_hex, 16) if secondary_hex else None
            new_colors_val: Tuple[int, Optional[int]] = (primary_val, secondary_val)

            role = discord.utils.get(interaction.guild.roles, name=f"color-{username.id}")

            role_position = 1
            guild_obj = await self.db.select_one(model.Guilds, {"server": interaction.guild.id})
            if guild_obj:
                top_role = discord.utils.get(interaction.guild.roles, id=guild_obj["role"])
                if top_role:
                    role_position = max(1, top_role.position - 1)

            role_updated = False
            if role is None:
                role = await interaction.guild.create_role(
                    name=f"color-{username.id}",
                    color=discord.Color(new_colors_val[0]),
                    secondary_color=discord.Color(new_colors_val[1]) if new_colors_val[1] is not None else None
                )
                if role_position > 1:
                    await role.edit(position=role_position)
                role_updated = True

            else:
                current_colors_val = (
                    role.color.value if role.color else None,
                    role.secondary_color.value if role.secondary_color else None
                )

                if current_colors_val != new_colors_val:
                    prev_colors = current_colors_val
                    await role.edit(
                        color=discord.Color(new_colors_val[0]),
                        secondary_color=discord.Color(new_colors_val[1]) if new_colors_val[1] is not None else None,
                        position=role_position
                    )
                    role_updated = True
                else:
                    description = self.msg['color_same']
                    undo_lock = True

            if role_updated:
                display_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
                if is_black:
                    description = self.msg['force_set_black'].format(display_color)
                else:
                    description = self.msg['force_set_set'].format(username.name, display_color)
                await update_history(self.db, username.id, interaction.guild.id, primary_val)

            if role and role not in username.roles:
                await username.add_roles(role)

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
            view = GlobalLayout(messages=self.msg, description=self.msg['color_format'], docs_page="commands/force-set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] issued bot command: /set (invalid format)", interaction.user.name, interaction.user.id)

        except discord.HTTPException as e:
            err_description = self.msg['exception']
            if e.code == 50013:
                err_description = self.msg['err_50013']
            elif e.code == 670006:
                err_description = self.msg['err_670006']
            else:
                err_description = self.msg['err_http'].format(e.code, e.text)
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/force-set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.warning("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/force-set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            log_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
            logger.info("%s[%s] issued bot command: /force set %s", interaction.user.name, interaction.locale, log_color)

    @group.command(name="remove", description="Remove the color of the user")
    @app_commands.describe(username="Username")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def forceremove(self, interaction: discord.Interaction, username: discord.Member) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"color-{username.id}")
            if role is not None:
                await username.remove_roles(role)
                await role.delete()
                description = self.msg['force_remove_remove'].format(username.name)
            else:
                description = self.msg['force_remove_no_color']

            view = GlobalLayout(messages=self.msg, description=description, docs_page="commands/force-remove")
            await interaction.followup.send(view=view)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/force-remove")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /force remove %s", interaction.user.name, interaction.locale, username.name)

    @group.command(name="purge", description="Remove all color roles (irreversible)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction) -> None:
        view = PurgeView(messages=self.msg, author_id=interaction.user.id, db=self.db, description=self.msg['purge_confirm'])

        try:
            await interaction.response.defer(ephemeral=True)
            await interaction.followup.send(view=view)
        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/force-purge")
            await interaction.followup.send(view=view)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
        finally:
            logger.info("%s[%s] issued bot command: /force purge", interaction.user.name, interaction.locale)

    @forceset.error
    @forceremove.error
    @purge.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            view = CooldownLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            view = GlobalLayout(messages=self.msg, description=self.msg['no_permissions'])
            await interaction.followup.send(view=view)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ForceCog(bot))
