import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from database import model

from bot import db, cmd_messages


class SelectCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="select", description="Choose one of the static colors on the server")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        view = discord.ui.View()
        try:
            await interaction.response.defer(ephemeral=True)

            embed.add_field(name=cmd_messages['available_colors'], value=f"", inline=False)
            with db as db_session:
                query = db_session.select(model.select_class("select"), {"server_id": interaction.guild.id})
            available_colors = []

            if query and len(query) > 0:
                colors_data = query[0]

                for i in range(1, 11):
                    color_key = f"hex_{i}"
                    color_value = colors_data.get(color_key)

                    if color_value is not None:
                        available_colors.append(color_value)
            print(available_colors)
            
            for i, color in enumerate(available_colors, start=1):
                embed.add_field(name=f"", value=f"**{i}.** #{color}", inline=False)
  

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
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view)
            logging.info(f"{interaction.user.name}[{interaction.locale}] issued bot command: /select")

    @staticmethod
    async def __select_callback(interaction: discord.Interaction):
        edited_view = discord.ui.View()
        embed: Embed = discord.Embed(title=f"", description="", color=4539717)
        try:
            for number in range(1, 10):
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{number}")
                if role:
                    await interaction.user.remove_roles(role)
                embed: Embed = discord.Embed(title=f"", description=cmd_messages['select_remove'], color=4539717)
            if interaction.data['custom_id'] != "delete":
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{interaction.data['custom_id']}")
                embed: Embed = discord.Embed(title=f"", description=cmd_messages['select_set'].format(role.mention),
                                             color=4539717)
                if role:
                    await interaction.user.add_roles(role)

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=cmd_messages['exception'], value=f"", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed, view=edited_view)

    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = cmd_messages["cool_down"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SelectCog(bot))
