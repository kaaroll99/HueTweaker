import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from database import model
from utils.color_format import ColorUtils
from views.global_view import GlobalLayout
from views.select import SelectView, extract_palette

logger = logging.getLogger(__name__)


class SelectCog(BaseCog):

    @app_commands.command(name="select", description="Choose one of the static colors on the server")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        docs_page = "commands/select"
        try:
            await interaction.response.defer(ephemeral=True)
            palette_row = await self.db.select_one(model.Select, {"server_id": interaction.guild.id})
            color_options = extract_palette(palette_row)

            if not color_options:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['select_no_colors'], docs_page))
                return

            color_values = [color for _, color in color_options]
            image = ColorUtils.generate_color_list_image(interaction.user.display_name, color_values)
            file = discord.File(fp=ColorUtils.to_bytes(image), filename="color_select.png")

            view = SelectView(self.msg, self.msg['available_colors'], self.bot, color_options, file,
                              docs_page=docs_page, author_id=interaction.user.id)
            await interaction.followup.send(view=view, file=file, ephemeral=True)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "select", e)

        finally:
            logger.info("%s[%s] issued bot command: /select", interaction.user.name, interaction.locale)

    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SelectCog(bot))
