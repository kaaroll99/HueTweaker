import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands
from discord.ext import commands

from views.cooldown import CooldownLayout
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)


class BaseCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    async def handle_cooldown_error(
        self, interaction: discord.Interaction, error: app_commands.CommandOnCooldown
    ) -> None:
        retry_time = datetime.now() + timedelta(seconds=error.retry_after)
        response = self.msg["cool_down"].format(int(retry_time.timestamp()))
        view = CooldownLayout(messages=self.msg, description=response)
        if interaction.response.is_done():
            await interaction.followup.send(
                view=view, ephemeral=True, delete_after=error.retry_after
            )
        else:
            await interaction.response.send_message(
                view=view, ephemeral=True, delete_after=error.retry_after
            )

    async def handle_permission_error(self, interaction: discord.Interaction) -> None:
        view = GlobalLayout(messages=self.msg, description=self.msg["no_permissions"])
        if interaction.response.is_done():
            await interaction.followup.send(view=view, ephemeral=True)
        else:
            await interaction.response.send_message(view=view, ephemeral=True)

    def get_http_error_description(self, error: discord.HTTPException) -> str:
        if error.code == 50013:
            return self.msg["err_50013"]
        elif error.code == 670006:
            return self.msg["err_670006"]
        else:
            return self.msg["err_http"].format(error.code, error.text)
