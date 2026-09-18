import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.color_format import format_colors_label
from utils.color_parse import parse_color_pair
from utils.history_manager import update_history
from utils.role_manager import apply_color_role, remove_color_role
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
        docs_page = "commands/force-set"
        log_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
        try:
            await interaction.response.defer(ephemeral=True)

            primary_val, secondary_val, is_black = parse_color_pair(interaction, color, secondary_color)
            label = format_colors_label(primary_val, secondary_val)

            result = await apply_color_role(
                interaction.guild, username, primary_val, secondary_val, self.db, interaction.client.user.id
            )

            if not result.changed:
                description = self.msg['color_same']
            else:
                template = self.msg['force_set_black'] if is_black else self.msg['force_set_set']
                description = template.format(username.name, label)
                await update_history(self.db, username.id, interaction.guild.id, primary_val, secondary_val)

            view = Layout.from_result(self.msg, result, primary_val, interaction.user.id, description)
            await self.respond(interaction, view)

        except ValueError:
            await self.respond(interaction, GlobalLayout(self.msg, self.msg['color_format'], docs_page))
            logger.info("%s[%s] issued bot command: /force set (invalid format)", interaction.user.name, interaction.user.id)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "force set", e)

        finally:
            logger.info("%s[%s] issued bot command: /force set %s", interaction.user.name, interaction.locale, log_color)

    @group.command(name="remove", description="Remove the color of the user")
    @app_commands.describe(username="Username")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def forceremove(self, interaction: discord.Interaction, username: discord.Member) -> None:
        docs_page = "commands/force-remove"
        try:
            await interaction.response.defer(ephemeral=True)
            removed = await remove_color_role(interaction.guild, username.id)
            if removed:
                description = self.msg['force_remove_remove'].format(username.name)
            else:
                description = self.msg['force_remove_no_color']
            await self.respond(interaction, GlobalLayout(self.msg, description, docs_page))

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "force remove", e)

        finally:
            logger.info("%s[%s] issued bot command: /force remove %s", interaction.user.name, interaction.locale, username.name)

    @group.command(name="purge", description="Remove all color roles (irreversible)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def purge(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            view = PurgeView(messages=self.msg, author_id=interaction.user.id, description=self.msg['purge_confirm'])
            await interaction.followup.send(view=view, ephemeral=True)
        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), "commands/force-purge"))
            self.log_command_error(interaction, "force purge", e)
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
