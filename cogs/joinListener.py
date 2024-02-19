import logging
import discord
from discord.ext import commands
from discord import app_commands, Embed
import config
import datetime
from config import bot

messages_file = config.load_yml('messages.yml')
config_file = config.load_yml('config.yml')


class JoinListenerCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member):
        channel = member.guild.get_channel(config_file['join_channel'])
        try:
            embed: Embed = discord.Embed(title=f"Witaj {member.name}", description=f"Próbuj szczęścia...",
                                  color=config_file['EMBED_COLOR'], timestamp=datetime.datetime.now())
        except Exception as e:
            embed.clear_fields()
            embed.add_field(name=f"{messages_file['exception']} Bot napotkał nieoczekiwany bład",
                            value=f"```{repr(e)} ```",
                            inline=False)
        finally:
            embed.set_footer(text=f"{bot.user.name}", icon_url=bot.user.avatar)
            embed.set_thumbnail(url="https://i.imgur.com/V7EchsH.gif")
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await channel.send(embed=embed)

    @commands.Cog.listener()
    async def on_member_remove(self, member):
        role = discord.utils.get(member.guild.roles, name=f"color-{member.id}")
        if role is not None:
            await role.delete()


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(JoinListenerCog(bot))
