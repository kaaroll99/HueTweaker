import logging
from typing import Tuple, Optional

import discord
from discord import app_commands
from discord.ext import commands

from cogs._base import BaseCog
from utils.color_parse import fetch_color_representation, color_parser, check_black
from utils.color_format import ColorUtils
from utils.cooldown_check import is_user_on_cooldown
from utils.history_manager import update_history
from utils.role_manager import create_or_update_color_role, assign_role_if_missing
from views.global_view import GlobalLayout
from views.set import Layout, ConfirmationView

logger = logging.getLogger(__name__)


async def dynamic_cooldown(interaction: discord.Interaction):
    return await is_user_on_cooldown(interaction)


class SetCog(BaseCog):

    @app_commands.command(name="set", description="Set color using HEX code or CSS color name")
    @app_commands.describe(
        color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)",
        secondary_color="Secondary color for gradient (optional)"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str, secondary_color: str = None) -> None:
        description = ""
        undo_lock = False
        prev_colors: Optional[Tuple[Optional[int], Optional[int]]] = None

        try:
            await interaction.response.defer(ephemeral=True)

            primary_hex = color_parser(fetch_color_representation(interaction, color))
            secondary_hex = color_parser(fetch_color_representation(interaction, secondary_color)) if secondary_color else None

            primary_hex, secondary_hex, is_black = check_black(primary_hex, secondary_hex)

            if primary_hex is None or (secondary_hex is None and secondary_color):
                raise ValueError

            primary_val = int(primary_hex, 16)
            secondary_val = int(secondary_hex, 16) if secondary_hex else None
            new_colors_val: Tuple[int, Optional[int]] = (primary_val, secondary_val)

            image = ColorUtils.generate_preview_image(interaction.user.display_name, primary_val, secondary_val)
            file = discord.File(fp=ColorUtils.to_bytes(image), filename="color_preview.png")
            image_url = "attachment://" + file.filename

            view = ConfirmationView(
                interaction.user.id,
                self.msg.get('confirm_color'),
                discord.Color(new_colors_val[0]),
                image_url)
            await interaction.edit_original_response(content=None, attachments=[file], view=view)

            await view.wait()

            if view.value is None:
                timeout_view = GlobalLayout(self.msg, self.msg.get('timeout', "Timed out."), "commands/set")
                await interaction.edit_original_response(content=None, view=timeout_view, attachments=[])
                return
            elif view.value is False:
                cancel_view = GlobalLayout(self.msg, self.msg.get('cancelled', "Cancelled."), "commands/set")
                await interaction.edit_original_response(content=None, view=cancel_view, attachments=[])
                return

            role, role_updated, prev_colors = await create_or_update_color_role(
                interaction.guild, interaction.user.id, primary_val, secondary_val, self.db
            )

            if not role_updated:
                description = self.msg['color_same']
                undo_lock = True
            else:
                display_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
                if is_black:
                    description = self.msg['color_set_black'].format(display_color)
                else:
                    description = self.msg['color_set'].format(display_color)
                await update_history(self.db, interaction.user.id, interaction.guild.id, primary_val)

            await assign_role_if_missing(interaction.user, role)

            view = Layout(
                messages=self.msg,
                color=discord.Color(new_colors_val[0]),
                display_color=f"{color}" + (f", {secondary_color}" if secondary_color else ""),
                prev_colors=prev_colors,
                role_id=role.id if role else None,
                author_id=interaction.user.id,
                description=description,
                undo_lock=undo_lock
            )

            await interaction.edit_original_response(content=None, view=view, attachments=[])

        except ValueError:
            view = GlobalLayout(messages=self.msg, description=self.msg['color_format'], docs_page="commands/set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] issued bot command: /set (invalid format)", interaction.user.name, interaction.user.id)

        except discord.HTTPException as e:
            err_description = self.get_http_error_description(e)
            view = GlobalLayout(messages=self.msg, description=err_description, docs_page="commands/set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.warning("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=self.msg['exception'], docs_page="commands/set")
            await interaction.followup.send(view=view, ephemeral=True)
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            log_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
            logger.info("%s[%s] issued bot command: /set %s", interaction.user.name, interaction.locale, log_color)

    @set.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
