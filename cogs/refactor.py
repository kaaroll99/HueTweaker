"""TEMPORARY: ``/refactor`` renames every legacy ``color-<user_id>`` role of a server at once.

Remove this cog (file + entry in ``bot.py``) once servers have migrated; without it legacy roles
still migrate one by one on their owner's next color change.
"""

import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.role_manager import refactor_legacy_roles
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)

DOCS_PAGE = "commands/refactor"


class RefactorCog(BaseCog):

    @app_commands.command(name="refactor", description="Rename old color-<id> roles to readable member names")
    @app_commands.checks.cooldown(1, 300.0, key=lambda i: i.guild_id)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def refactor(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            result = await refactor_legacy_roles(self.db, interaction.guild)
            if not (result.renamed or result.orphans or result.skipped or result.failed):
                description = self.msg['refactor_nothing']
            else:
                description = self.msg['refactor_done'].format(result.renamed, result.orphans, result.failed)
                if result.failed:
                    description += self.msg['refactor_failed_hint']
            await self.respond(interaction, GlobalLayout(self.msg, description, DOCS_PAGE))
            logger.info("%s[%s] refactored color roles in guild %s: %s", interaction.user.name, interaction.user.id,
                        interaction.guild_id, result)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), DOCS_PAGE))
            self.log_command_error(interaction, "refactor", e)

        finally:
            logger.info("%s[%s] issued bot command: /refactor", interaction.user.name, interaction.locale)

    @refactor.error
    async def refactor_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)
        elif isinstance(error, app_commands.MissingPermissions):
            await self.handle_permission_error(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RefactorCog(bot))
