import logging
from typing import Tuple, Optional

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.history_manager import update_history
from utils.color_parse import fetch_color_representation, color_parser, check_black
from utils.role_manager import create_or_update_color_role, assign_role_if_missing, get_color_role
from views.global_view import GlobalLayout
from views.purge import PurgeView
from views.set import Layout

logger = logging.getLogger(__name__)


class ForceCog(BaseCog):

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

            role, role_updated, prev_colors = await create_or_update_color_role(
                interaction.guild, username.id, primary_val, secondary_val, self.db
            )

            if not role_updated:
                description = self.msg['color_same']
                undo_lock = True
            else:
                display_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
                if is_black:
                    description = self.msg['force_set_black'].format(display_color)
                else:
                    description = self.msg['force_set_set'].format(username.name, display_color)
                await update_history(self.db, username.id, interaction.guild.id, primary_val)

            await assign_role_if_missing(username, role)

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
            err_description = self.get_http_error_description(e)
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
            role = get_color_role(interaction.guild, username.id)
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
            await self.handle_cooldown_error(interaction, error)
        elif isinstance(error, app_commands.MissingPermissions):
            await self.handle_permission_error(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ForceCog(bot))
