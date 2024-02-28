import json
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
from database import database, model

messages_file = config.load_yml('messages.yml')
config_file = config.load_yml('config.yml')


class ColorCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.color = config_file['EMBED_COLOR']

    group = app_commands.Group(name="color", description="...")

    @group.command(name="set", description="Setting the color")
    @app_commands.describe(color="Color to set")
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            with open("css-color-names.json", "r", encoding="utf-8") as file:
                data = json.load(file)
            search_color = color.lower().replace(" ", "")
            if search_color in map(lambda x: x.lower(), data.keys()):
                color = data[search_color]
            if not re.match(r"^(#?[0-9a-fA-F]{6})$", color.upper()):
                raise ValueError("color")
            if color.startswith("#"):
                color = color.strip("#")
            db = database.Database(url=f"sqlite:///databases/guilds.db")
            db.connect()
            sb_query = db.select(model.guilds_class("guilds"), {"server": interaction.guild.id})
            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
            if role is None:
                role = await interaction.guild.create_role(name=f"color-{interaction.user.id}")
            if sb_query:
                top_role = discord.utils.get(interaction.guild.roles, id=sb_query[0].get("role", 0))
                if top_role is not None and not top_role.position == 0:
                    bot_member = interaction.guild.get_member(bot.user.id)
                    bot_top_role = 0

                    for role in bot_member.roles:
                        if role.position > bot_top_role:
                            bot_top_role = role.position

                    if top_role.position > bot_top_role:
                        raise ValueError("pos")

                    await role.edit(position=top_role.position - 1)
            await role.edit(colour=discord.Colour(int(color, 16)))
            await interaction.user.add_roles(role)
            embed.description = f"✨ **Color has been set for to __#{color}__**"
            embed.color = discord.Colour(int(color, 16))

        except ValueError as e:
            if str(e) == "color":
                embed.description = "⚠️ **Incorrect color format**"
                embed.add_field(name=f"Color format:",
                                value=f"`#F5DF4D` or name of [CSS color](https://www.w3schools.com/cssref/css_colors.php)",
                                inline=False)
            elif str(e) == "pos":
                embed.description = (
                    f"**{messages_file.get('exception')} The bot does not have the permissions to perform this operation.** "
                    f"This is probably due to an incorrect configuration of toprole - `/color toptole`. "
                    f"Notify the server administrator of the occurrence of this error.")

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /color set {color} (len:{len(embed)})")

    @group.command(name="remove", description="Removing the color")
    @app_commands.guild_only()
    async def remove(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
            if role is not None:
                await interaction.user.remove_roles(role)
                await role.delete()
            embed.description = f"✨ **Color has been removed**"

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /color remove (len:{len(embed)})")

    @group.command(name="forceset", description="Setting the color of the user")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(user_name="User name", color="Color to set")
    @app_commands.guild_only()
    async def forceset(self, interaction: discord.Interaction, user_name: discord.Member, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            with open("css-color-names.json", "r", encoding="utf-8") as file:
                data = json.load(file)
            search_color = color.lower().replace(" ", "")
            if search_color in map(lambda x: x.lower(), data.keys()):
                color = data[search_color]
            if not re.match(r"^(#?[0-9a-fA-F]{6})$", color.upper()):
                raise ValueError
            if color.startswith("#"):
                color = color.strip("#")
            db = database.Database(url=f"sqlite:///databases/guilds.db")
            db.connect()
            sb_query = db.select(model.guilds_class("guilds"), {"server": interaction.guild.id})
            role = discord.utils.get(interaction.guild.roles, name=f"color-{user_name.id}")
            if role is None:
                role = await interaction.guild.create_role(name=f"color-{user_name.id}")
            if sb_query:
                top_role = discord.utils.get(interaction.guild.roles, id=sb_query[0].get("role", 0))
                if top_role is not None and not top_role.position == 0:
                    bot_member = interaction.guild.get_member(bot.user.id)
                    bot_top_role = 0

                    for role in bot_member.roles:
                        if role.position > bot_top_role:
                            bot_top_role = role.position

                    if top_role.position > bot_top_role:
                        raise ValueError("pos")

                    await role.edit(position=top_role.position - 1)
            await role.edit(colour=discord.Colour(int(color, 16)))
            await user_name.add_roles(role)
            embed.description = f"✨ **Color has been set for {user_name.name} to __#{color}__**"
            embed.color = discord.Colour(int(color, 16))

        except ValueError as e:
            if str(e) == "color":
                embed.description = "⚠️ **Incorrect color format**"
                embed.add_field(name=f"Color format:",
                                value=f"`#F5DF4D` or name of [CSS color](https://www.w3schools.com/cssref/css_colors.php)",
                                inline=False)

            elif str(e) == "pos":
                embed.description = (
                    f"**{messages_file.get('exception')} The bot does not have the permissions to perform this operation.** "
                    f"This is probably due to an incorrect configuration of toprole - `/color toptole`. "
                    f"Notify the server administrator of the occurrence of this error.")

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user} {messages_file['logs_issued']}: /color forceset {color} (len:{len(embed)})")

    @group.command(name="forceremove", description="Removing the color of the user")
    @app_commands.describe(user_name="User name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def forceremove(self, interaction: discord.Interaction, user_name: discord.Member) -> None:
        embed: Embed = discord.Embed(title="", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            role = discord.utils.get(interaction.guild.roles, name=f"color-{user_name.id}")
            if role is not None:
                await user_name.remove_roles(role)
                await role.delete()
                embed.description = f"✨ **Color has been removed for {user_name.name}**"
            else:
                embed.description = f"⚠️ **The user with the given name did not have the color set**"

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user} {messages_file['logs_issued']}: /color forceremove {user_name.name} (len:{len(embed)})")

    @group.command(name="toprole", description="Set top role for color roles")
    @app_commands.describe(role_name="Role name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(self, interaction: discord.Interaction, role_name: discord.Role) -> None:
        embed: Embed = discord.Embed(title="", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)

            role_ids = []
            pattern = re.compile(f"color-\\d{{18,19}}")
            top_role = discord.utils.get(interaction.guild.roles, id=role_name.id)
            if top_role.position == 0:
                raise ValueError("You cannot set `@everyone` as top role. Check `/help` for more information.")

            bot_member = interaction.guild.get_member(bot.user.id)
            bot_top_role = 0

            for role in bot_member.roles:
                if role.position > bot_top_role:
                    bot_top_role = role.position

            if top_role.position > bot_top_role:
                raise ValueError(
                    "You cannot set a role which is above the highest bot role. Check `/help` for more information.")

            for role in interaction.guild.roles:

                if pattern.match(role.name):
                    role_ids.append(role.id)
                    role = discord.utils.get(interaction.guild.roles, id=role.id)
                    if not top_role.position == 0:
                        await role.edit(position=top_role.position - 1)

            db = database.Database(url=f"sqlite:///databases/guilds.db")
            db.connect()
            sb_query = db.select(model.guilds_class("guilds"), {"server": interaction.guild.id})
            if sb_query:
                db.update(model.guilds_class(f"guilds"), {"server": interaction.guild.id},
                          {"role": role_name.id})
            else:
                db.create(model.guilds_class(f"guilds"), {"server": interaction.guild.id, "role": role_name.id})

            embed.description = f"✨ **Top role has been set for __{role_name.name}__**"
        except ValueError as e:
            embed.description = f"**{messages_file.get('exception')} {e}**"
        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(
                f"{interaction.user} {messages_file['logs_issued']}: /color toprole (len:{len(embed)})")

    @group.command(name="check", description="Color information (HEX, RGB, HSL, CMYK, Integer)")
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    async def check(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"",
                                     color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            with open("css-color-names.json", "r", encoding="utf-8") as file:
                data = json.load(file)
            if color.lower().strip() in map(lambda x: x.lower(), data.keys()):
                color = data[color]

            output_color = color_format.color_converter(color)

            if "error" in output_color:
                raise ValueError

            image = color_format.generate_image_from_rgb_float([float(val) for val in output_color['RGB']])

            embed: Embed = discord.Embed(title=f"Details for color: **{output_color['Input']}**", description=f"",
                                         color=self.color, timestamp=datetime.datetime.now())

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
            embed.description = f"**{messages_file['exception']} Incorrect color format**"
            embed.add_field(value=f"💡 Correct formats:\n* 9932f0\n* rgb(153, 50, 240)\n* hsl(272.53, 86.36%, 56.86%)"
                                  f"\n* cmyk(36.25%, 79.17%, 0.00%, 5.88%)\n* 10040048", name="", inline=False)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.followup.send(embed=embed)

        except Exception as e:
            embed.clear_fields()
            embed.description = f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**"
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
            embed: Embed = discord.Embed(title="", description=messages_file.get('no_permissions', ''),
                                         color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(ColorCog(bot))
