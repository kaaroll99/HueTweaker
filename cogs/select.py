import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from database import model
from utils.color_format import ColorUtils
from bot import db, cmd_messages
from io import BytesIO


class SelectCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="select", description="Choose one of the static colors on the server")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title=cmd_messages['available_colors'], description=f"", color=4539717)
        view = discord.ui.View()
        embed_file = None
        try:
            await interaction.response.defer(ephemeral=True)
            with db as db_session:
                query = db_session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            available_colors = []
            if not query and available_colors == []:
                embed.add_field(name=f"", value=cmd_messages['select_no_colors'], inline=False)
            else: 
                if query and len(query) > 0:
                    colors_data = query[0]

                    for i in range(1, 11):
                        color_key = f"hex_{i}"
                        color_value = colors_data.get(color_key)

                        if color_value is not None:
                            available_colors.append((i, color_value))
                options = []
                for i, (index, color) in enumerate(available_colors, start=1):
                    options.append(
                        discord.SelectOption(
                            label=f"Color {i}", 
                            value=str(index),
                            description=f"#{color}"
                        )
                    )
                
                if options:
                    color_select = discord.ui.Select(
                        placeholder="Select a color...",
                        options=options,
                        custom_id="color_select"
                    )
                    
                    async def color_select_callback(interaction: discord.Interaction):
                        selected_value = interaction.data["values"][0]
                        for idx, color in available_colors:
                            if str(idx) == selected_value:
                                with db as db_session:
                                    query = db_session.select(model.guilds_class("guilds"), {"server": interaction.guild.id})

                                role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
                                role_position = 1
                                if role is None:
                                    role = await interaction.guild.create_role(name=f"color-{interaction.user.id}")
                                if query:
                                    top_role = discord.utils.get(interaction.guild.roles, id=query[-1].get("role", None))
                                    if top_role:
                                        role_position = max(1, top_role.position - 1)
                                await role.edit(colour=discord.Colour(int(color, 16)), position=role_position)
                                break
                        await interaction.response.defer()

                    color_select.callback = color_select_callback
                    view.add_item(color_select)
                    
                
                color_values = [color for _, color in available_colors]
                image = ColorUtils.generate_colored_text_grid(interaction.user.name, color_values)
                image_bytes = BytesIO()
                image.save(image_bytes, format='PNG')
                image_bytes.seek(0)
                embed_file = discord.File(fp=image_bytes, filename="color_select.png")
                embed.set_image(url="attachment://" + embed_file.filename)
            
        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = cmd_messages['err_50013']
            if e.code == 10062:
                pass
            else:
                embed.description = cmd_messages['err_http'].format(e.code, e.text)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")

        except Exception as e:
            embed.clear_fields()
            embed.description = cmd_messages['exception']
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            if embed_file:
                await interaction.followup.send(embed=embed, file=embed_file)
            else:
                await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user.name}[{interaction.locale}] issued bot command: /select")


    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = cmd_messages["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SelectCog(bot))
