import discord
from discord import app_commands, Embed
from discord.ext import commands
import datetime
import config
import logging
from config import bot


messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


class DevCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="dev", description="Developer command. It won't work.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def dev(self, interaction: discord.Interaction) -> None:
        # print(interaction.guild.preferred_locale)
        # print(interaction.locale)
        embed: Embed = discord.Embed(title=f"{bot.user.name}", description=f"",
                              color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        file = None
        try:
            if interaction.guild_id == 1209531775412604968:
                await interaction.response.defer(ephemeral=True)

                import csv

                csv_file = 'guilds_info.csv'
                fields = ['Guild Name', 'Guild ID', 'Owner Name', 'Owner ID', 'Member Count', 'Preferred Locale']

                with open(csv_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=fields)
                    writer.writeheader()

                    for guild in self.bot.guilds:
                        owner_name = guild.owner.name if guild.owner else "-"
                        owner_id = guild.owner.id if guild.owner else 0
                        writer.writerow({
                            'Guild Name': guild.name,
                            'Guild ID': guild.id,
                            'Owner Name': owner_name,
                            'Owner ID': owner_id,
                            'Member Count': guild.member_count,
                            'Preferred Locale': guild.preferred_locale
                        })

                embed.description = f"Dane zapisano do pliku CSV: {csv_file}"
                file = discord.File(csv_file)

            else:
                embed.description = f"Command for bot developers only."
        except discord.HTTPException as e:
            embed.clear_fields()
            embed.description = (f"**{messages_file.get('exception')}")
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")
        except Exception as e:
            embed.clear_fields()
            embed.description = f""
            embed.add_field(name=f"{messages_file.get('exception')} {messages_file.get('exception_message', '')}",
                            value=f"", inline=False)
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            embed.set_footer(text=f"{bot.user.name} by kaaroll99", icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed, file=file)
            logging.info(f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /vote")

    @dev.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        embed: Embed = discord.Embed(title="",
                                     description=f"This command is only available to the developers of this bot and is used for testing.",
                                     color=config_file['EMBED_COLOR'])
        embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
        embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
        await interaction.response.send_message(embed=embed, ephemeral=True)

async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DevCog(bot))
