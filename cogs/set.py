import logging
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.color_format import ColorUtils, format_colors_label
from utils.color_parse import parse_color_pair
from utils.history_manager import update_history
from utils.role_manager import apply_color_role
from views.global_view import GlobalLayout
from views.set import Layout, ConfirmationView

logger = logging.getLogger(__name__)


class SetCog(BaseCog):

    @app_commands.command(name="set", description="Set color using HEX code or CSS color name")
    @app_commands.describe(
        color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
        await self._apply_color(interaction, "set", color, None)

    @app_commands.command(name="gradient", description="Set a gradient using two HEX codes or CSS color names")
    @app_commands.describe(
        color="Primary color code (e.g. #9932f0) or CSS color name (e.g royalblue)",
        secondary_color="Secondary color code (e.g. #1abc9c) or CSS color name"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def gradient(self, interaction: discord.Interaction, color: str, secondary_color: str) -> None:
        await self._apply_color(interaction, "gradient", color, secondary_color)

    async def _apply_color(
        self,
        interaction: discord.Interaction,
        command_name: str,
        color: str,
        secondary_color: Optional[str],
    ) -> None:
        docs_page = f"commands/{command_name}"
        log_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")

        try:
            guild = interaction.guild
            member = interaction.user if isinstance(interaction.user, discord.Member) else None
            bot_user = interaction.client.user
            if guild is None or member is None or bot_user is None:
                raise RuntimeError("Guild interaction context is unavailable")

            await interaction.response.defer(ephemeral=True)

            primary_val, secondary_val, is_black = parse_color_pair(interaction, color, secondary_color)
            label = format_colors_label(primary_val, secondary_val)

            image = ColorUtils.generate_preview_image(member.display_name, primary_val, secondary_val)
            file = discord.File(fp=ColorUtils.to_bytes(image), filename="color_preview.png")

            confirmation = ConfirmationView(
                member.id,
                self.msg['confirm_color'],
                discord.Color(primary_val),
                "attachment://" + file.filename,
            )
            await interaction.edit_original_response(content=None, attachments=[file], view=confirmation)
            await confirmation.wait()

            if confirmation.value is None:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['timeout'], docs_page))
                return
            if confirmation.value is False:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['cancelled'], docs_page))
                return

            result = await apply_color_role(guild, member, primary_val, secondary_val, self.db, bot_user.id)

            if not result.changed:
                description = self.msg['color_same']
            else:
                template = self.msg['color_set_black'] if is_black else self.msg['color_set']
                description = template.format(label)
                await update_history(self.db, member.id, guild.id, primary_val, secondary_val)

            view = Layout.from_result(self.msg, result, primary_val, member.id, description)
            await self.respond(interaction, view)

        except ValueError:
            await self.respond(interaction, GlobalLayout(self.msg, self.msg['color_format'], docs_page))
            logger.info("%s[%s] issued bot command: /%s (invalid format)", interaction.user.name, interaction.user.id, command_name)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, command_name, e)

        finally:
            logger.info("%s[%s] issued bot command: /%s %s", interaction.user.name, interaction.locale, command_name, log_color)

    @set.error
    async def set_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)

    @gradient.error
    async def gradient_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
