import json
import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from color_format import ColorUtils
from config import bot, hex_regex, rgb_regex, hsl_regex, cmyk_regex, load_yml

config_file = load_yml('config.yml')
token_file = load_yml('token.yml')
lang = load_yml('lang/en.yml')

class CheckCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="check", description="Check color information (HEX, RGB, HSL, CMYK)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    async def check(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        try:
            await interaction.response.defer(ephemeral=True)
            if color.startswith("<@") and color.endswith(">"):
                cleaned_color = color.replace("<", "").replace(">", "").replace("@", "")
                copy_role = discord.utils.get(interaction.guild.roles, name=f"color-{cleaned_color}")
                if copy_role is None:
                    raise ValueError
                else:
                    color = str(copy_role.color)
            elif color == "random":
                color = "#{:06x}".format(random.randint(0, 0xFFFFFF))
            color_match = color
            with open("assets/css-color-names.json", "r", encoding="utf-8") as file:
                data = json.load(file)
            color_match = color_match.lower().replace(" ", "")
            if color_match in map(lambda x: x.lower(), data.keys()):
                color_match = data[color_match]
                color_type = "hex"
            elif hex_regex.match(color_match):
                if len(color_match.strip("#")) == 3:
                    color_match = ''.join([x * 2 for x in color_match.strip("#")])
                else:
                    color_match = color_match.strip("#")
                color_type = "hex"
            elif rgb_regex.match(color_match):
                color_type = "rgb"
            elif hsl_regex.match(color_match):
                color_type = "hsl"
            elif cmyk_regex.match(color_match):
                color_type = "cmyk"
            else:
                raise ValueError

            color_utils = ColorUtils(color_match)
            output_color = color_utils.color_converter(color_type)
            image = color_utils.generate_image_from_rgb_float(output_color['RGB'])

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

            image.save("output/color_fill.png")
            embed.color = int(output_color['Hex'].strip("#"), 16)
            file = discord.File("output/color_fill.png")
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
                f"{interaction.user.name}[{interaction.user.id}] issued bot command: /check {color}")

    @check.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = lang["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CheckCog(bot))
