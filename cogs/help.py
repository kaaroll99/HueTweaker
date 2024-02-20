import discord
from discord import app_commands, Embed
from discord.ext import commands
import datetime
import config
import logging
import yaml
from config import bot

messages_file = config.load_yml('messages.yml')
config_file = config.load_yml('config.yml')


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="Information about the bot and a list of available commands")
    async def help(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title=f"{bot.user.name}", description=f"",
                              color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        select = discord.ui.Select(placeholder='Choose a command from the list...', options=[
            discord.SelectOption(label="/help", value="help", emoji="✨"),
            discord.SelectOption(label="/color set", value="set", emoji="✨"),
            discord.SelectOption(label="/color remove", value="remove", emoji="✨"),
            discord.SelectOption(label="/color check", value="check", emoji="✨"),
            discord.SelectOption(label="/color forceset", value="forceset", emoji="✨"),
            discord.SelectOption(label="/color forceremove", value="forceremove", emoji="✨"),
            discord.SelectOption(label="/color toprole", value="toprole", emoji="✨"),
            discord.SelectOption(label="/embed", value="embed", emoji="✨")
        ])
        select.callback = self.__select_callback
        view = discord.ui.View()
        view.add_item(select)
        try:
            await interaction.response.defer(ephemeral=True)
            embed.description = f"""
                                                
                        Online on `{len(bot.guilds)}` servers.
                        
                        ⚠️ Remember to set top-role `/color toprole`. If the role is not indicated, color roles will be created at the bottom which may cause the color to be obscured by higher roles.
                        
                        💡 Select one of the available commands from the list to learn more.
                        """
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

    @app_commands.command(name="vote", description="Vote for the bot on top.gg")
    async def vote(self, interaction: discord.Interaction) -> None:
        embed = discord.Embed(title=f"{bot.user.name}", description=f"",
                              color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        try:
            await interaction.response.defer(ephemeral=True)
            embed.description = f"""
            
                            ✨ [VOTE ON TOP.GG](https://top.gg/bot/1209187999934578738/vote) ✨
                            
                            """
        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"", inline=False)
            logging.critical(f"{interaction.user} raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name} by kaaroll99", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /vote (len:{len(embed)})")

    @staticmethod
    async def __select_callback(interaction: discord.Interaction):
        try:
            with open('help_commands.yml', 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            selected_option = interaction.data['values'][0]
            embed = discord.Embed(title=f"✨ Command`/{data[selected_option]['name']}`",
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


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
