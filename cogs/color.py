import discord
from discord import app_commands, Embed
from discord.ext import commands
import datetime
import config
import color_format
from config import bot
import logging
import yaml
import re
from database import database

messages_file = config.load_yml('messages.yml')
config_file = config.load_yml('config.yml')


class ColorCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.color = config_file['EMBED_COLOR']

    group = app_commands.Group(name="color", description="...")

    @group.command(name="set", description="Ustawianie koloru nazwy uzytkownika")
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title=f"Kolorowy nick", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            if re.match(r"^([0-9a-fA-F]{6})$", color.upper()):
                role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
                if role is not None:
                    top_role = discord.utils.get(interaction.guild.roles, id=config_file['color_top-role_id'])
                    await role.edit(colour=discord.Colour(int(color, 16)))
                    await role.edit(position=top_role.position - 1)
                    await interaction.user.add_roles(role)
                else:
                    role = await interaction.guild.create_role(name=f"color-{interaction.user.id}")
                    top_role = discord.utils.get(interaction.guild.roles, id=config_file['color_top-role_id'])
                    await role.edit(colour=discord.Colour(int(color, 16)))
                    await role.edit(position=top_role.position - 1)
                    await interaction.user.add_roles(role)
                embed.title = f"✨ Ustawiono kolor na __#{color}__"
                embed.color = discord.Colour(int(color, 16))
            else:
                embed.title = "⚠️ Niepoprawny format koloru"
                embed.add_field(name=f"Format koloru:", value=f"`F5DF4D`", inline=False)

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_thumbnail(url="https://i.imgur.com/bceGHHc.png")
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /color set (len:{len(embed)})")

    @group.command(name="remove", description="Usuwanie koloru nazwy uzytkownika")
    @app_commands.guild_only()
    async def remove(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title=f"Kolorowy nick", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
            if role is not None:
                await interaction.user.remove_roles(role)
                await role.delete()
            embed.title = f"✨ Usunieto kolor"

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_thumbnail(url="https://i.imgur.com/bceGHHc.png")
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /color remove (len:{len(embed)})")

    @group.command(name="forceset", description="Usuwanie koloru wskazanego uzytkownika")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def forceset(self, interaction: discord.Interaction, user_name: discord.Member, color: str) -> None:
        embed: Embed = discord.Embed(title=f"Kolorowy nick", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            if re.match(r"^([0-9a-fA-F]{6})$", color.upper()):
                role = discord.utils.get(interaction.guild.roles, name=f"color-{user_name.id}")
                top_role = discord.utils.get(interaction.guild.roles, id=config_file['color_top-role_id'])
                if role is not None:
                    await role.edit(colour=discord.Colour(int(color, 16)))
                    await role.edit(position=top_role.position - 1)
                    await user_name.add_roles(role)
                else:
                    role = await interaction.guild.create_role(name=f"color-{user_name.id}")
                    await role.edit(colour=discord.Colour(int(color, 16)))
                    await role.edit(position=top_role.position - 1)
                    await user_name.add_roles(role)
                embed.title = f"✨ Ustawiono kolor {user_name.name} na __#{color}__"
                embed.color = discord.Colour(int(color, 16))
            else:
                embed.title = "⚠️ Niepoprawny format koloru"
                embed.add_field(name=f"Format koloru:", value=f"`F5DF4D`", inline=False)

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_thumbnail(url="https://i.imgur.com/bceGHHc.png")
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /color forceset (len:{len(embed)})")

    @group.command(name="forceremove", description="Usuwanie koloru wskazanego uzytkownika")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def forceremove(self, interaction: discord.Interaction, user_name: discord.Member) -> None:
        embed: Embed = discord.Embed(title=f"Kolorowy nick", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"color-{user_name.id}")
            if role is not None:
                await user_name.remove_roles(role)
                await role.delete()
                embed.title = f"✨ Usunieto kolor {user_name.name}"
            else:
                embed.title = f"⚠️ Uzytkownik o podanej nazwie nie miał ustawionego koloru"

        except Exception as e:
            embed.clear_fields()
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_thumbnail(url="https://i.imgur.com/bceGHHc.png")
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /color forceremove {user_name.name} (len:{len(embed)})")

    @group.command(name="toprole", description="Ustawianie top-roli dla kolorów")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(self, interaction: discord.Interaction, role_name: discord.Role) -> None:
        embed: Embed = discord.Embed(title=f"Kolorowy nick", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)

            role_ids = []
            pattern = re.compile(f"color-\\d{{18,19}}")
            top_role = discord.utils.get(interaction.guild.roles, id=role_name.id)

            for role in interaction.guild.roles:
                if pattern.match(role.name):
                    role_ids.append(role.id)
                    role = discord.utils.get(interaction.guild.roles, id=role.id)
                    await role.edit(position=top_role.position - 1)

            db = database.Database(url=f"sqlite:///databases/{interaction.guild_id}.db")
            db.connect()
            sb_query = db.select(model.scoreboard_class(f"scoreboard_{clean_name}"), {"name": user_name.id})

            embed.title = f"✨ Ustawiono top-role dla koloruów na {role_name.name}"

        except discord.app_commands.MissingPermissions as e:
            embed.add_field(name=f"{messages_file.get('exception')} "
                                 f"Brak odpowiednich uprawnień do wykonania tego polecenia",
                            value=f"```{repr(e)} ```", inline=False)
        except Exception as e:
            embed.clear_fields()
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_thumbnail(url="https://i.imgur.com/bceGHHc.png")
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user} {messages_file['logs_issued']}: /color toprole (len:{len(embed)})")

    @group.command(name="check", description="Inrormacje do kolorze (HEX, RGB, HSL, CMYK, Integer)")
    @app_commands.describe(color="Kod koloru (np. 9932f0 lub rgb(153, 50, 240))")
    async def check(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title=f"{bot.user.name}", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            output_color = color_format.color_converter(color)

            if "error" in output_color:
                raise ValueError
            # else:
            image = color_format.generate_image_from_rgb_float([float(val) for val in output_color['RGB']])

            embed: Embed = discord.Embed(title=f"Szczegóły dla koloru: **{output_color['Input']}**", description=f"",
                                         color=self.color, timestamp=datetime.datetime.now())

            embed.add_field(name=f"{messages_file['item_icon']} Hex:",
                            value=f"{output_color['Hex']}",
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
            embed.add_field(name=f"{messages_file['item_icon']} Integer:",
                            value=f"{output_color['Integer']}",
                            inline=False)

            image.save("output/color_fill.png")
            embed.color = int(output_color['Hex'].strip("#"), 16)
            file = discord.File("output/color_fill.png")
            embed.set_image(url="attachment://" + file.filename)
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed, file=file)

        except ValueError:
            embed.clear_fields()
            embed.title = f"{messages_file['exception']} Niepoprawny format koloru"
            embed.add_field(value=f"💡 Poprawne formaty:\n* 9932f0\n* rgb(153, 50, 240)\n* hsl(272.53, 86.36%, 56.86%)"
                                  f"\n* cmyk(36.25%, 79.17%, 0.00%, 5.88%)\n* 10040048", name="", inline=False)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed)

        finally:
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /color check {color} (len:{len(embed)})")

    @toprole.error
    @forceset.error
    @forceremove.error
    async def permission_error(self, interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title=messages_file.get('no_permissions', ''), description=f"",
                                         color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ColorCog(bot))
