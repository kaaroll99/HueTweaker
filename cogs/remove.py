import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from constants import COLOR_ROLE_PREFIX
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)


class RemoveCog(BaseCog):

    @app_commands.command(name="remove", description="Remove the color")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def remove(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"{COLOR_ROLE_PREFIX}{interaction.user.id}")
            if role is not None:
                await interaction.user.remove_roles(role)
                await role.delete()
                description = self.msg['color_remove']
            else:
                description = self.msg['color_remove_no_color']
            view = GlobalLayout(messages=self.msg, description=description)
            await interaction.followup.send(view=view)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/remove")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /remove", interaction.user.name, interaction.locale)

    @remove.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemoveCog(bot))
