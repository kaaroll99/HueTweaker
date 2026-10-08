import asyncio
import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.color_format import ColorUtils, dominant_colors
from views.global_view import GlobalLayout
from views.match import MatchView

logger = logging.getLogger(__name__)

# 4 colors + the gradient button fill one row of 5 buttons.
MATCH_COLORS = 4


class MatchCog(BaseCog):

    @app_commands.command(name="match", description="Get username colors that match your avatar")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def match(self, interaction: discord.Interaction) -> None:
        docs_page = "commands/match"
        try:
            await interaction.response.defer(ephemeral=True)

            avatar = await interaction.user.display_avatar.replace(size=128, static_format="png").read()
            colors = await asyncio.to_thread(dominant_colors, avatar, MATCH_COLORS)
            if not colors:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['match_no_colors'], docs_page))
                return

            entries = [*colors, (colors[0], colors[1])] if len(colors) >= 2 else colors
            image = ColorUtils.generate_color_list_image(interaction.user.display_name, entries)
            file = discord.File(fp=ColorUtils.to_bytes(image), filename="color_match.png")
            view = MatchView(self.msg, self.msg['match_title'], self.bot, file, colors,
                             author_id=interaction.user.id, docs_page=docs_page)
            await interaction.followup.send(view=view, file=file, ephemeral=True)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "match", e)

        finally:
            logger.info("%s[%s] issued bot command: /match", interaction.user.name, interaction.locale)

    @match.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(MatchCog(bot))
