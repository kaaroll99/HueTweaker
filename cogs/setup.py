import logging

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from database import model
from utils.role_manager import (
    TOPROLE_MODE_AUTO,
    TOPROLE_MODE_CUSTOM,
    TOPROLE_MODE_OFF,
    place_color_roles,
)
from views.global_view import GlobalLayout
from views.setup_select import SetupView

logger = logging.getLogger(__name__)

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
        docs_page = "commands/setup-select"
        try:
            await interaction.response.defer(ephemeral=True)
            select_obj = await self.db.select_one(model.Select, {"server_id": interaction.guild.id})

            view = SetupView(select_obj or {}, interaction.guild.id, self.bot)
            await interaction.followup.send(view=view, ephemeral=True)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "setup select", e)

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
        docs_page = "commands/setup-toprole"
        try:
            await interaction.response.defer(ephemeral=True)

            selected_mode = mode.value
            if selected_mode == TOPROLE_MODE_CUSTOM and (role_name is None or role_name.is_default()):
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['toprole_custom_missing'], docs_page))
                return

            values = {
                "mode": selected_mode,
                "role": role_name.id if selected_mode == TOPROLE_MODE_CUSTOM else 0,
            }
            # Raises DatabaseError when the write fails, so the user never sees a false success.
            await self.db.upsert(model.Guilds, {"server": interaction.guild.id}, values)

            if selected_mode == TOPROLE_MODE_AUTO:
                description = self.msg['toprole_auto']
            elif selected_mode == TOPROLE_MODE_OFF:
                description = self.msg['toprole_off']
            else:
                description = self.msg['toprole_custom'].format(role_name.name)

            await place_color_roles(self.db, interaction.guild, interaction.client.user.id)

            await self.respond(interaction, GlobalLayout(self.msg, description, docs_page))

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, "setup toprole", e)

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
