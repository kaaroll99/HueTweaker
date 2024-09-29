import logging
from datetime import datetime, timedelta
from io import BytesIO

import discord
from discord import app_commands, Embed
from discord.ext import commands

from bot_init import bot
from utils.color_format import ColorUtils
from utils.color_imput_type import color_type
from utils.lang_loader import load_lang


class CheckCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="check", description="Check color information (HEX, RGB, HSL, CMYK)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    async def check(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        lang = load_lang(str(interaction.locale))
        try:
            await interaction.response.defer(ephemeral=True)
            color = color_type(interaction, color)
            color_utils = ColorUtils(color)
            output_color = color_utils.color_converter()
            if output_color is None:
                raise ValueError
            image = color_utils.generate_image(output_color['RGB'])

            embed.title = lang['check_title'].format(output_color['Input'])

            embed.add_field(name=f"<:star:1269288950174978100> Hex:",
                            value=f"{output_color['Hex'].upper()}",
                            inline=False)
            embed.add_field(name=f"<:star:1269288950174978100> RGB:",
                            value=f"rgb({output_color['RGB'][0] * 255:.0f}, {output_color['RGB'][1] * 255:.0f},"
                                  f" {output_color['RGB'][2] * 255:.0f})",
                            inline=False)
            embed.add_field(name=f"<:star:1269288950174978100> HSL:",
                            value=f"hsl({output_color['HSL'][0]:.2f}, {output_color['HSL'][1] * 100:.2f}%,"
                                  f" {output_color['HSL'][2] * 100:.2f}%)",
                            inline=False)
            embed.add_field(name=f"<:star:1269288950174978100> CMYK:",
                            value=f"cmyk({output_color['CMYK'][0] * 100:.2f}%, {output_color['CMYK'][1] * 100:.2f}%,"
                                  f" {output_color['CMYK'][2] * 100:.2f}%, {output_color['CMYK'][3] * 100:.2f}%)",
                            inline=False)
            embed.add_field(name=lang['check_css'],
                            value=f"{', '.join(str(x) for x in output_color['Similars'][:5]) if output_color['Similars'] else '-'}",
                            inline=False)

            image_bytes = BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            file = discord.File(fp=image_bytes, filename="color_fill.png")

            embed.color = int(output_color['Hex'].strip("#"), 16)
            embed.set_image(url="attachment://" + file.filename)
            embed.set_footer(text=lang['footer_message'], icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed, file=file)
        except ValueError:
            embed.clear_fields()
            embed.description = lang['check_color_format']
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed.clear_fields()
            embed.description = lang['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed)
        finally:
            logging.info(
                f"{interaction.user.name}[{interaction.locale}] issued bot command: /check {color}")

    @check.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        lang = load_lang(str(interaction.locale))
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = lang["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CheckCog(bot))
