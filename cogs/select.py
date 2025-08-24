import logging
from datetime import datetime, timedelta
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from database import model
from utils.color_format import ColorUtils
from views.select import SelectView
from views.global_view import GlobalLayout
from views.cooldown import CooldownLayout

logger = logging.getLogger(__name__)


class SelectCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    @app_commands.command(name="select", description="Choose one of the static colors on the server")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        color_options = []
        color_map = {}

        try:
            await interaction.response.defer(ephemeral=True)
            with self.db as db_session:
                query = db_session.select(model.select_class("select"), {"server_id": interaction.guild.id})

            if query and len(query) > 0:
                colors_data = query[0]
                for i in range(1, 11):
                    color_key = f"hex_{i}"
                    color_value = colors_data.get(color_key)
                    if isinstance(color_value, str) and color_value.strip():
                        color_options.append((i, color_value.strip()))

                color_map = {str(idx): hexv for idx, hexv in color_options}

            if not color_options:
                description = self.msg['select_no_colors']
            else:
                color_values = [color for _, color in color_options]
                description = self.msg['available_colors']
                image = ColorUtils.generate_colored_text_grid(interaction.user.name, color_values)
                image_bytes = BytesIO()
                image.save(image_bytes, format='PNG')
                image_bytes.seek(0)
                file = discord.File(fp=image_bytes, filename="color_select.png")

                view = SelectView(self.msg, description, self.bot, color_options, color_map, file)
                await interaction.followup.send(view=view, file=file)

        except discord.HTTPException as e:
            if e.code == 50013:
                err_description = self.msg['err_50013']
            elif e.code == 10062:
                pass
            else:
                err_description = self.msg['err_http'].format(e.code, e.text)
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.error("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/select")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /select", interaction.user.name, interaction.locale)

    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            view = CooldownLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SelectCog(bot))
