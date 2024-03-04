import discord
from discord import app_commands, Embed
from discord.ext import commands
import datetime
import config
import logging
import yaml
from config import bot

from database import database, model

messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Information about the bot and a list of available commands")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title=f"{bot.user.name}", description=f"",
                              color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        select = discord.ui.Select(placeholder='Choose a command from the list...', options=[
            discord.SelectOption(label="/help", value="help", emoji="ℹ️"),
            discord.SelectOption(label="/color set", value="set", emoji="🌈"),
            discord.SelectOption(label="/color remove", value="remove", emoji="🗑️"),
            discord.SelectOption(label="/color check", value="check", emoji="🔍"),
            discord.SelectOption(label="/color forceset", value="forceset", emoji="⚙️"),
            discord.SelectOption(label="/color forceremove", value="forceremove", emoji="🔄"),
            discord.SelectOption(label="/color toprole", value="toprole", emoji="💫"),
            discord.SelectOption(label="/embed", value="embed", emoji="📋")
        ])
        invite_button = discord.ui.Button(label="Invite bot", style=discord.ButtonStyle.url,
                                    url="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot")
        support_button = discord.ui.Button(label="Join support server", style=discord.ButtonStyle.url,
                                    url="https://discord.gg/tYdK4pD6ks")
        privacy_button = discord.ui.Button(label="Privacy Policy", style=discord.ButtonStyle.secondary)

        select.callback = self.__select_callback
        privacy_button.callback = self.__privacy_message
        view = discord.ui.View()
        view.add_item(select)
        view.add_item(invite_button)
        view.add_item(support_button)
        view.add_item(privacy_button)

        try:
            await interaction.response.defer(ephemeral=True)
            total_users = sum(guild.member_count for guild in bot.guilds)
            embed.description = (f"- Online on `{len(bot.guilds)}` servers.\n"
                                 f"- Used by `{total_users}` people.\n\n"
                                 f"**Select one of the available commands from the list to learn more.**\n\n"
                                 f"*⚠️ Remember to set the top role using /color toprole. If no role is indicated, color"
                                 f" roles will be created at the bottom, potentially getting obscured by higher roles.*")

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name} by kaaroll99", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /help (len:{len(embed)})")

    @staticmethod
    async def __select_callback(interaction: discord.Interaction):
        try:
            with open('assets/help_commands.yml', 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            selected_option = interaction.data['values'][0]
            embed = discord.Embed(title=f"✨ Command `{data[selected_option]['name']}`",
                                  description=f"{data[selected_option]['desc']}",
                                  color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())

            embed.add_field(name=f"Command syntax:", value=f"> {data[selected_option]['usage']}",
                            inline=False)
            embed.add_field(name=f"Command example:", value=f"> {data[selected_option]['example']}",
                            inline=False)
        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file['exception']} {messages_file['exception_description']}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name} by kaaroll99", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed)

    @staticmethod
    async def __privacy_message(interaction: discord.Interaction):
        try:
            with open('assets/privacy_policy.md', 'r', encoding='utf-8') as f:
                data = f.read()
            embed = discord.Embed(title=f"", description=f"Privacy policy information has been sent in a private message.",
                                  color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
            terms = discord.Embed(title=f"", description=data, color=config_file['EMBED_COLOR'])
        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file['exception']} {messages_file['exception_description']}",
                            value=f"```{repr(e)} ```", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name} by kaaroll99", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed)
            user = await bot.fetch_user(interaction.user.id)
            await user.send(embed=terms)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
