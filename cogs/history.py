import logging
from datetime import datetime, timedelta

from io import BytesIO
import discord
from discord import app_commands
from discord.ext import commands

from database import model
from utils.color_format import ColorUtils
from views.cooldown import CooldownLayout
from views.global_view import GlobalLayout
from views.history import HistoryView

logger = logging.getLogger(__name__)


class HistoryCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    @app_commands.command(name="history", description="View your color change history on server")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def history(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            data = self.db.select(model.history_class("history"), {"user_id": interaction.user.id, "guild_id": interaction.guild.id})

            colors = []
            if data:
                entry = data[0]
                for i in range(1, 6):
                    color_val = entry.get(f"color_{i}")
                    if color_val is not None:
                        colors.append(color_val)
            if not colors:
                description = self.msg['history_no_history']
                file = None
            else:
                description = self.msg['history_title']
                image = ColorUtils.generate_int_colors_grid(colors)
                image_bytes = BytesIO()
                image.save(image_bytes, format='PNG')
                image_bytes.seek(0)
                file = discord.File(fp=image_bytes, filename="color_history.png")

            view = HistoryView(self.msg, description, self.bot, file, "commands/history")
            if file:
                await interaction.followup.send(view=view, file=file)
            else:
                await interaction.followup.send(view=view)


        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/history")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /history", interaction.user.name, interaction.locale)

    @history.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            view = CooldownLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HistoryCog(bot))
