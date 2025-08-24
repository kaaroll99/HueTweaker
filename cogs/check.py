import logging
from datetime import datetime, timedelta
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from utils.color_format import ColorUtils
from utils.color_parse import fetch_color_representation
from views.check import CheckLayout
from views.global_view import GlobalLayout
from views.cooldown import CooldownLayout

logger = logging.getLogger(__name__)


class CheckCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.msg = bot.messages

    @app_commands.command(name="check", description="Check color information (HEX, RGB, HSL, CMYK)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    async def check(self, interaction: discord.Interaction, color: str) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            color = fetch_color_representation(interaction, color)
            color_utils = ColorUtils(color, find_similar_colors=True)
            output_color = color_utils.color_converter()
            if output_color is None:
                raise ValueError
            image = color_utils.generate_image(output_color['RGB'])

            description = self.msg['check_title'].format(output_color['Input'])
            elements = []

            elements.append(("<:star:1362879443625971783> Hex:", output_color['Hex'].upper()))
            elements.append(("<:star:1362879443625971783> RGB:",
                             f"rgb({output_color['RGB'][0] * 255:.0f}, {output_color['RGB'][1] * 255:.0f}, {output_color['RGB'][2] * 255:.0f})"))
            elements.append(("<:star:1362879443625971783> HSL:",
                            f"hsl({output_color['HSL'][0]:.2f}, {output_color['HSL'][1] * 100:.2f}%,{output_color['HSL'][2] * 100:.2f}%)"))
            elements.append(("<:star:1362879443625971783> CMYK:",
                            f"cmyk({output_color['CMYK'][0] * 100:.2f}%, {output_color['CMYK'][1] * 100:.2f}%, {output_color['CMYK'][2] * 100:.2f}%, {output_color['CMYK'][3] * 100:.2f}%)"))
            elements.append((self.msg['check_css'], f"{', '.join(str(x) for x in output_color['Similars'][:5]) if output_color['Similars'] else '-'}", ""))

            image_bytes = BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            file = discord.File(fp=image_bytes, filename="color_fill.png")
            image_url = "attachment://" + file.filename

            view = CheckLayout(messages=self.msg, description=description, image=image_url, elements=elements)
            await interaction.followup.send(view=view, file=file)

        except ValueError:
            view = GlobalLayout(messages=self.msg, description=self.msg['check_color_format'], docs_page="commands/check")
            await interaction.followup.send(view=view)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/check")
            await interaction.followup.send(view=view)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /check %s", interaction.user.name, interaction.locale, color)

    @check.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            view = CooldownLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CheckCog(bot))
