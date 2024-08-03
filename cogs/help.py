import discord
from discord import app_commands, Embed
from discord.ext import commands
import logging
import yaml
from config import bot, load_yml

config_file = load_yml('config.yml')
lang = load_yml('lang/en.yml')


class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="help", description="View information about the bot and a list of available commands")
    async def help(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title=f"{bot.user.name}", description=f"", color=config_file['EMBED_COLOR'])
        select = discord.ui.Select(placeholder=lang['help_choose'], options=[
            discord.SelectOption(label="/help", value="help", emoji="ℹ️"),
            discord.SelectOption(label="/set", value="set", emoji="🌈"),
            discord.SelectOption(label="/remove", value="remove", emoji="🗑️"),
            discord.SelectOption(label="/select", value="select", emoji="⭐"),
            discord.SelectOption(label="/check", value="check", emoji="🔍"),
            discord.SelectOption(label="/force set", value="forceset", emoji="⚙️"),
            discord.SelectOption(label="/force remove", value="forceremove", emoji="🔄"),
            discord.SelectOption(label="/force purge", value="forcepurge", emoji="💥"),
            discord.SelectOption(label="/setup toprole", value="toprole", emoji="💫"),
            discord.SelectOption(label="/setup select", value="setupselect", emoji="💫"),
            discord.SelectOption(label="/embed", value="embed", emoji="📋"),
            discord.SelectOption(label="/vote", value="vote", emoji="🗳️")
        ])
        invite_button = discord.ui.Button(label="Invite bot", style=discord.ButtonStyle.url,
                                    url="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot")
        support_button = discord.ui.Button(label="Join support server", style=discord.ButtonStyle.url,
                                    url="https://discord.gg/tYdK4pD6ks")
        privacy_button = discord.ui.Button(label="Privacy Policy", style=discord.ButtonStyle.url,
                                           url="https://huetweaker.gitbook.io/docs/main/privacy-policy")
        terms_button = discord.ui.Button(label="Terms of Service", style=discord.ButtonStyle.url,
                                         url="https://huetweaker.gitbook.io/docs/main/terms-of-service")

        select.callback = self.__select_callback
        view = discord.ui.View()
        view.add_item(select)
        view.add_item(invite_button)
        view.add_item(support_button)
        view.add_item(privacy_button)
        view.add_item(terms_button)

        try:
            await interaction.response.defer(ephemeral=True)
            total_users = sum(guild.member_count for guild in bot.guilds)
            embed.description = lang['help_desc'].format(len(bot.guilds), total_users)

        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=lang['exception'], value=f"", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=lang['footer_message'], icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, view=view)
            logging.info(f"{interaction.user.name}[{interaction.user.id}] issued bot command: /help")

    @staticmethod
    async def __select_callback(interaction: discord.Interaction):
        try:
            with open('assets/help_commands.yml', 'r', encoding='utf-8') as f:
                data = yaml.safe_load(f)
            selected_option = interaction.data['values'][0]
            embed: Embed = discord.Embed(title=f"<:star:1269273735358058496> Command `{data[selected_option]['name']}`",
                                  description=f"{data[selected_option]['desc']}", color=config_file['EMBED_COLOR'])

            embed.add_field(name=lang['com_syntax'], value=f"> {data[selected_option]['usage']}", inline=False)
            embed.add_field(name=lang['com_syntax'], value=f"> {data[selected_option]['example']}", inline=False)
            embed.add_field(name=f"Docs:", value=lang['com_syntax'].format(data[selected_option]['docs']), inline=False)
        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=lang['exception'], value=f"", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=lang['footer_message'], icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(HelpCog(bot))
