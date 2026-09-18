import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.role_manager import remove_color_role
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)


class RemoveCog(BaseCog):

    @app_commands.command(name="remove", description="Remove the color")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def remove(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            removed = await remove_color_role(interaction.guild, interaction.user.id)
            description = self.msg['color_remove'] if removed else self.msg['color_remove_no_color']
            await self.respond(interaction, GlobalLayout(self.msg, description, "commands/remove"))

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), "commands/remove"))
            self.log_command_error(interaction, "remove", e)

        finally:
            logger.info("%s[%s] issued bot command: /remove", interaction.user.name, interaction.locale)

    @remove.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemoveCog(bot))
