import discord
from discord import app_commands, Embed
from discord.ext import commands
from datetime import datetime, timedelta
import json
import logging
from config import bot, load_yml

config_file = load_yml('config.yml')


class EmbedCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @app_commands.command(name="embed", description="Send discord embed using json format")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.describe(channel="The channel to which the message is to be sent", data="JSON data")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def embed(self, interaction: discord.Interaction, channel: discord.TextChannel, data: str) -> None:
        info_embed: Embed = discord.Embed(
            title="",
            description=f"",
            color=config_file['EMBED_COLOR'],
            timestamp=datetime.now()
        )
        try:
            await interaction.response.defer(ephemeral=True)
            data = json.loads(data)

            embed: Embed = discord.Embed(
                title=data.get("title", ""),
                description=data.get("description", ""),
                color=int(data.get("color", "000000"), 16),
                timestamp=datetime.now()
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

        except json.JSONDecodeError as e:
            info_embed.description = f"⚠️ Error while parsing JSON data: `{e}`. \n\n💡 Check JSON format using `/help` command"
        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50001:
                info_embed.description = (f"**{messages_file.get('exception')} The bot does not have the channel access"
                                          f" to perform this operation.**\n\n")
            else:
                info_embed.description = (f"**{messages_file.get('exception')} Bot could not perform this operation "
                                          f"due to HTTP discord error.**\n\n"
                                          f"{e.code} - {e.text}")
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise HTTP exception: {e.text}")
        except Exception as e:
            info_embed.description = e
            logging.critical(f"{interaction.user.name}[{interaction.user.id}] raise critical exception - {repr(e)}")
        finally:
            await interaction.followup.send(embed=info_embed)
            logging.info(
                f"{interaction.user.name}[{interaction.user.id}] issued bot command: /embed (len:{len(embed)})")

    @embed.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = f"⚠️ Please cool down. Retry <t:{int(retry_time.timestamp())}:R>"
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title="", description=messages_file.get('no_permissions', ''),
                                         color=config_file['EMBED_COLOR'], timestamp=datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(EmbedCog(bot))
