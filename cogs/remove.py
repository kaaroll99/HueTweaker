import discord
from discord import app_commands, Embed
from discord.ext import commands
from datetime import datetime, timedelta
import config
from config import bot
import logging


messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')
token_file = config.load_yml('token.yml')


class RemoveCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="remove", description="Remove the color")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def remove(self, interaction: discord.Interaction) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=config_file['EMBED_COLOR'])
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
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")

        finally:
            embed.set_footer(text=messages_file.get('footer_message'), icon_url=bot.user.avatar)
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.followup.send(embed=embed)
            logging.info(f"{interaction.user.name}[{interaction.user.id}] {messages_file['logs_issued']}: /remove")

    @remove.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = f"⚠️ Please cool down. Retry <t:{int(retry_time.timestamp())}:R>"
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(RemoveCog(bot))
