import json
import discord
from discord import app_commands, Embed
from discord.ext import commands
from datetime import datetime, timedelta
import config
import color_format
from config import bot
import logging
import re

messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


class CheckCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="check", description="Check color information (HEX, RGB, HSL, CMYK, Integer)")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    async def check(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        try:
            await interaction.response.defer(ephemeral=True)
            color_match = color
            with open("assets/css-color-names.json", "r", encoding="utf-8") as file:
                data = json.load(file)
            color_match = color_match.lower().replace(" ", "")
            if color_match in map(lambda x: x.lower(), data.keys()):
                color_match = data[color_match]
            elif re.match(r"^(#?[0-9a-fA-F]{6})$", color_match):
                color_match = color_match.strip("#")
            else:
                raise ValueError

            output_color = color_format.color_converter(color_match)

            image = color_format.generate_image_from_rgb_float([float(val) for val in output_color['RGB']])

            embed.title = f"Details for color: **{output_color['Input']}**"

            embed.add_field(name=f"{messages_file['item_icon']} Hex:",
                            value=f"{output_color['Hex'].upper()}",
                            inline=False)
            embed.add_field(name=f"{messages_file['item_icon']} RGB:",
                            value=f"rgb({output_color['RGB'][0] * 255:.0f}, {output_color['RGB'][1] * 255:.0f},"
                                  f" {output_color['RGB'][2] * 255:.0f})",
                            inline=False)
            embed.add_field(name=f"{messages_file['item_icon']} HSL:",
                            value=f"hsl({output_color['HSL'][0]:.2f}, {output_color['HSL'][1] * 100:.2f}%,"
                                  f" {output_color['HSL'][2] * 100:.2f}%)",
                            inline=False)
            embed.add_field(name=f"{messages_file['item_icon']} CMYK:",
                            value=f"cmyk({output_color['CMYK'][0] * 100:.2f}%, {output_color['CMYK'][1] * 100:.2f}%,"
                                  f" {output_color['CMYK'][2] * 100:.2f}%, {output_color['CMYK'][3] * 100:.2f}%)",
                            inline=False)
            embed.add_field(name=f"{messages_file['item_icon']} The most similar CSS colors:",
                            value=f"{', '.join(str(x) for x in output_color['Similars']) if output_color['Similars'] else '-'}",
                            inline=False)

            image.save("output/color_fill.png")
            embed.color = int(output_color['Hex'].strip("#"), 16)
            file = discord.File("output/color_fill.png")
            embed.set_image(url="attachment://" + file.filename)
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed, file=file)
        except ValueError:
            embed.clear_fields()
            embed.description = f"**{messages_file['exception']} Incorrect color format**"
            embed.add_field(value=f"**Correct formats:**\n* 9932f0\n* rgb(153, 50, 240)\n* hsl(272.53, 86.36%, 56.86%)"
                                  f"\n* cmyk(36.25%, 79.17%, 0.00%, 5.88%)\n* 10040048"
                                  f"\n* [CSS color](https://huetweaker.gitbook.io/docs/main/colors)",
                            name="", inline=False)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed)
        finally:
            logging.info(
                f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /check {color}")

    @check.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = f"⚠️ Please cool down. Retry <t:{int(retry_time.timestamp())}:R>"
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(CheckCog(bot))
