import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from bot_init import bot, cmd_messages


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

            role_count = 0
            embed.add_field(name=cmd_messages['available_colors'], value=f"", inline=False)
            for number in range(1, 10):
                role = discord.utils.get(interaction.guild.roles, name=f"color-static-{number}")
                if role:
                    role_count += 1
                    embed.add_field(name=f"", value=f"**{role.mention}**", inline=False)

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
                embed.add_field(name=f"", value=cmd_messages['select_no_colors'], inline=False)
            else:
                button_delete = discord.ui.Button(label="❌", style=discord.ButtonStyle.danger, custom_id="delete")
                button_delete.callback = self.__select_callback
                view.add_item(button_delete)

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
            embed.set_footer(text=cmd_messages['footer_message'], icon_url=bot.user.avatar)
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
            embed.set_footer(text=cmd_messages['footer_message'], icon_url=bot.user.avatar)
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
