import discord
from discord import app_commands, Embed
from discord.ext import commands
import datetime
import config
import json
import logging
from config import bot

messages_file = config.load_yml('assets/messages.yml')
config_file = config.load_yml('config.yml')


class EmbedCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="embed", description="JSON to discord embed conversion")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def embed(self, interaction: discord.Interaction, channel: discord.TextChannel, data: str) -> None:
        info_embed: Embed = discord.Embed(
            title="",
            description=f"",
            color=config_file['EMBED_COLOR'],
            timestamp=datetime.datetime.now()
        )
        try:
            await interaction.response.defer(ephemeral=True)
            data = json.loads(data)

            embed: Embed = discord.Embed(
                title=data.get("title", ""),
                description=data.get("description", ""),
                color=int(data.get("color", "000000"), 16),
                timestamp=datetime.datetime.now()
            )

            for field_data in data.get("fields", []):
                title = field_data.get("title", "")
                value = field_data.get("value", "")
                inline = field_data.get("inline", False)
                embed.add_field(name=title, value=value, inline=inline)

            embed.set_footer(text=data.get("footer_text", ""), icon_url=data.get("footer_icon", ""))
            embed.set_thumbnail(url=data.get("thumbnail", ""))
            embed.set_image(url=data.get("image", ""))
            embed.set_author(name=data.get("author_name", ""), url=data.get("author_url", ""),
                             icon_url=data.get("author_icon_url", ""))

            await channel.send(embed=embed)
            info_embed.description = f"Embed sent to: <#{channel.id}>"

            logging.info(f"{interaction.user} {messages_file['logs_issued']}: /embed (len:{len(embed)})")

        except json.JSONDecodeError as e:
            info_embed.description = f"⚠️ Error when parsing JSON data: `{e}`. \n\n💡 Check JSON format using `/help` and choosing `/embed` from the list."
        except Exception as e:
            info_embed.description = e
        finally:
            await interaction.followup.send(embed=info_embed)

    @embed.error
    async def permission_error(self, interaction: discord.Interaction, error):
        if isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title=messages_file.get('no_permissions', ''), description=f"",
                                         color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EmbedCog(bot))
