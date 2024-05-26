import json
import discord
from discord import app_commands, Embed
from discord.ext import commands
from datetime import datetime, timedelta
import config
from config import bot, db, hex_regex
import logging
import re
from database import database, model

messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


class SelectCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="select", description="Choose one of the static colors on the server")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
        try:
            await interaction.response.defer(ephemeral=True)
            view = discord.ui.View()

            role_count = 0
            for number in range(1, 10):
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{number}")
                if role:
                    role_count += 1
                    embed.add_field(name=f"", value=f"**{role.mention}**", inline=False)

            embed.add_field(name=f"Available colors:", value=f"", inline=False)
            role1 = discord.utils.get(interaction.guild.roles, name=f"color-static-1")
            if role1:
                button1 = discord.ui.Button(label="1", style=discord.ButtonStyle.primary, custom_id="1")
                button1.callback = self.__select_callback
                view.add_item(button1)

            role2 = discord.utils.get(interaction.guild.roles, name=f"color-static-2")
            if role2:
                button2 = discord.ui.Button(label="2", style=discord.ButtonStyle.primary, custom_id="2")
                button2.callback = self.__select_callback
                view.add_item(button2)

            role3 = discord.utils.get(interaction.guild.roles, name=f"color-static-3")
            if role3:
                button3 = discord.ui.Button(label="3", style=discord.ButtonStyle.primary, custom_id="3")
                button3.callback = self.__select_callback
                view.add_item(button3)

            role4 = discord.utils.get(interaction.guild.roles, name=f"color-static-4")
            if role4:
                button4 = discord.ui.Button(label="4", style=discord.ButtonStyle.primary, custom_id="4")
                button4.callback = self.__select_callback
                view.add_item(button4)

            role5 = discord.utils.get(interaction.guild.roles, name=f"color-static-5")
            if role5:
                button5 = discord.ui.Button(label="5", style=discord.ButtonStyle.primary, custom_id="5")
                button5.callback = self.__select_callback
                view.add_item(button5)

            if role_count == 0:
                embed.clear_fields()
                embed.add_field(name=f"", value=f"⚠️ **There are no static colors configured on this server.**", inline=False)
            else:
                button_delete = discord.ui.Button(label="❌", style=discord.ButtonStyle.danger, custom_id="delete")
                button_delete.callback = self.__select_callback
                view.add_item(button_delete)

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = (
                    f"**{messages_file.get('exception')} The bot does not have permissions to perform this operation.**"
                    f" Error may have been caused by misconfiguration of top-role bot (`/toprole`). "
                    f"Notify the server administrator of the occurrence of this error.\n\n"
                    f"💡 Use the `/help` command to learn how to properly configure top role")
            if e.code == 10062:
                pass
            else:
                info_embed.description = (f"**{messages_file.get('exception')} Bot could not perform this operation "
                                          f"due to HTTP discord error.**\n\n"
                                          f"{e.code} - {e.text}")
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")

        except Exception as e:
            embed.clear_fields()
            embed.description = (f"**{messages_file.get('exception')} {messages_file.get('exception_message', '')}**")
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view)
            logging.info(f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /select")

    @staticmethod
    async def __select_callback(interaction: discord.Interaction):
        edited_view = discord.ui.View()
        try:
            for number in range(1, 10):
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{number}")
                if role:
                    await interaction.user.remove_roles(role)
                embed: Embed = discord.Embed(title=f"", description=f"✨ **Static color has been removed**", color=config_file['EMBED_COLOR'])
            if interaction.data['custom_id'] != "delete":
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{interaction.data['custom_id']}")
                embed: Embed = discord.Embed(title=f"", description=f"✨ **Color has been set to {role.mention}**",
                                             color=config_file['EMBED_COLOR'])
                if role:
                    await interaction.user.add_roles(role)

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file['exception']} {messages_file['exception_description']}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed, view=edited_view)

    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = f"⚠️ Please cool down. Retry <t:{int(retry_time.timestamp())}:R>"
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SelectCog(bot))
