import datetime
import logging

import discord
from discord import app_commands, Embed
from discord.ext import commands

from utils.data_loader import load_yml

logger = logging.getLogger(__name__)


class DevCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.msg = bot.messages

    @app_commands.command(name="dev", description="Developer command. It won't work.")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def dev(self, interaction: discord.Interaction, action: str) -> None:
        embed: Embed = discord.Embed(title=f"{self.bot.user.name}", description=f"",
                                     color=4539717, timestamp=datetime.datetime.now())
        await interaction.response.defer(ephemeral=True)
        file = None
        try:
            if interaction.guild_id == 1135688599917056160:
                if action == "report":
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
                elif action == "tree":
                    await self.bot.tree.sync()
                    embed.description = f"Command tree synchronization completed."
                else:
                    embed.description = f"Command not found."
            else:
                embed.description = f"Command for bot developers only."
        except discord.HTTPException as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)
        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
        finally:
            embed.set_footer(text=f"{self.bot.user.name} by kaaroll99", icon_url=self.bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            
            if file:
                await interaction.followup.send(embed=embed, file=file)
            else:
                await interaction.followup.send(embed=embed)
                
            logger.warning("%s[%s] issued bot command: /dev %s", interaction.user.name, interaction.locale, action)

    # @dev.error
    # async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
    #     embed: Embed = discord.Embed(title="",
    #                                  description=f"This command is only available to the developers of this bot and is used for testing.",
    #                                  color=4539717)
    #     embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
    #     await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(DevCog(bot))
