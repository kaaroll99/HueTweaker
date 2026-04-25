import logging
import re

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from constants import COLOR_ROLE_PATTERN
from database import model
from utils.role_manager import (
    TOPROLE_MODE_AUTO,
    TOPROLE_MODE_CUSTOM,
    TOPROLE_MODE_OFF,
    get_role_position,
)
from views.global_view import GlobalLayout
from views.setup_select import SetupView

logger = logging.getLogger(__name__)

_color_role_re = re.compile(COLOR_ROLE_PATTERN)
_toprole_mode_choices = [
    app_commands.Choice(name="auto", value=TOPROLE_MODE_AUTO),
    app_commands.Choice(name="custom", value=TOPROLE_MODE_CUSTOM),
    app_commands.Choice(name="off", value=TOPROLE_MODE_OFF),
]


class SetupCog(BaseCog):

    group = app_commands.Group(name="setup", description="Setup bot on your server")

    @group.command(name="select", description="Setup static colors on server")
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def select(self, interaction: discord.Interaction) -> None:
        try:
            await interaction.response.defer(ephemeral=True)
            select_obj = await self.db.select_one(model.Select, {"server_id": interaction.guild.id})

            colors_data = select_obj if select_obj else {}

            view = SetupView(colors_data, interaction.guild.id, self.bot)
            await interaction.followup.send(view=view, ephemeral=True)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/setup-select")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            logger.info("%s[%s] issued bot command: /setup select", interaction.user.name, interaction.locale)

    @group.command(name="toprole", description="Configure color role placement for HueTweaker")
    @app_commands.describe(
        mode="Role placement mode: auto, custom, or off",
        role_name="Reference role used only in custom mode",
    )
    @app_commands.choices(mode=_toprole_mode_choices)
    @app_commands.checks.has_permissions(administrator=True)
    @app_commands.guild_only()
    async def toprole(
        self,
        interaction: discord.Interaction,
        mode: app_commands.Choice[str],
        role_name: discord.Role | None = None,
    ) -> None:
        try:
            await interaction.response.defer(ephemeral=True)

            selected_mode = mode.value
            if selected_mode == TOPROLE_MODE_CUSTOM and role_name is None:
                view = GlobalLayout(
                    messages=self.msg,
                    description=self.msg['toprole_custom_missing'],
                    docs_page="commands/setup-toprole"
                )
                await interaction.followup.send(view=view, ephemeral=True)
                return

            if role_name is not None and role_name.is_default():
                selected_mode = TOPROLE_MODE_OFF
                role_name = None

            guild_obj = await self.db.select_one(model.Guilds, {"server": interaction.guild.id})

            values = {
                "mode": selected_mode,
                "role": role_name.id if selected_mode == TOPROLE_MODE_CUSTOM and role_name is not None else 0,
            }

            if guild_obj:
                await self.db.update(model.Guilds, {"server": interaction.guild.id}, values)
            else:
                await self.db.create(model.Guilds, {"server": interaction.guild.id, **values})

            if selected_mode == TOPROLE_MODE_AUTO:
                description = self.msg['toprole_auto']
            elif selected_mode == TOPROLE_MODE_OFF:
                description = self.msg['toprole_off']
            else:
                description = self.msg['toprole_custom'].format(role_name.name)

            role_position = await get_role_position(self.db, interaction.guild)

            for role in interaction.guild.roles:
                if _color_role_re.match(role.name) and role.position != role_position:
                    await role.edit(position=role_position)

            view = GlobalLayout(messages=self.msg, description=description, docs_page="commands/setup-toprole")
            await interaction.followup.send(view=view)

        except discord.HTTPException as e:
            if e.code == 50013:
                err_description = self.msg['err_50013']
            else:
                err_description = self.msg['err_http'].format(e.code, e.text)
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/setup-toprole")
            await interaction.followup.send(view=view, ephemeral=True)
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
            await self.handle_cooldown_error(interaction, error)
        elif isinstance(error, app_commands.MissingPermissions):
            await self.handle_permission_error(interaction)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetupCog(bot))
