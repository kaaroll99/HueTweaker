import logging
import re
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from database import model
from views.cooldown import CooldownLayout
from views.global_view import GlobalLayout
from views.setup_select import SetupView

logger = logging.getLogger(__name__)

class SetupCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    group = app_commands.Group(name="setup", description="Setup bot on your server")

    @group.command(name="select", description="Setup static colors on server")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            select_obj = self.db.select_one(model.Select, {"server_id": interaction.guild.id})

            colors_data = select_obj if select_obj else {}

            view = SetupView(colors_data, interaction.guild.id, self.bot)
            await interaction.followup.send(view=view, ephemeral=True)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/setup-select")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /setup select", interaction.user.name, interaction.locale)

    @group.command(name="toprole", description="Setup top role for color roles")
    @app_commands.describe(role_name="Role name")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(self, interaction: discord.Interaction, role_name: discord.Role) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            pattern = re.compile(r"color-\\d{18,19}")
            top_role = discord.utils.get(interaction.guild.roles, id=role_name.id)

            guild_obj = self.db.select_one(model.Guilds, {"server": interaction.guild.id})
            if top_role.position == 0:
                if guild_obj:
                    self.db.delete(model.Guilds, {"server": interaction.guild.id})
                description = self.msg['toprole_reset']
            else:
                if guild_obj:
                    self.db.update(model.Guilds, {"server": interaction.guild.id}, {"role": role_name.id})
                else:
                    self.db.create(model.Guilds, {"server": interaction.guild.id, "role": role_name.id})

                description = self.msg['toprole_set'].format(role_name.name)

                for role in interaction.guild.roles:
                    if pattern.match(role.name):
                        role = discord.utils.get(interaction.guild.roles, id=role.id)
                        await role.edit(position=max(1, top_role.position - 1))

            view = GlobalLayout(messages=self.msg, description=description, docs_page="commands/setup-toprole")
            await interaction.followup.send(view=view)

        except discord.HTTPException as e:
            if e.code == 50013:
                err_description = self.msg['err_50013']
            else:
                err_description = self.msg['err_http'].format(e.code, e.text)
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/setup-toprole")
            logger.critical("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/setup-toprole")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /setup toprole", interaction.user.name, interaction.locale)

    @toprole.error
    @select.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            view = CooldownLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)

        elif isinstance(error, discord.app_commands.errors.MissingPermissions):
            embed: Embed = discord.Embed(title="", description=self.msg['no_permissions'],
                                         color=4539717, timestamp=datetime.now())
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.send_message(embed=embed, ephemeral=True)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
