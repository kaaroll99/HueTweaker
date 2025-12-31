import logging
from datetime import datetime, timedelta
from typing import Tuple, Optional
from io import BytesIO

import discord
from discord import app_commands
from discord.ext import commands

from database import model
from utils.color_parse import fetch_color_representation, color_parser, check_black
from utils.color_format import ColorUtils
from utils.cooldown_check import is_user_on_cooldown
from utils.history_manager import update_history
from views.cooldown import CooldownLayout
from views.global_view import GlobalLayout
from views.set import Layout, ConfirmationView

logger = logging.getLogger(__name__)


async def dynamic_cooldown(interaction: discord.Interaction):
    return await is_user_on_cooldown(interaction)


class SetCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    @app_commands.command(name="set", description="Set color using HEX code or CSS color name")
    @app_commands.describe(
        color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)",
        secondary_color="Secondary color for gradient (optional)"
    )
    @app_commands.checks.dynamic_cooldown(dynamic_cooldown, key=lambda i: (i.guild_id, i.user.id))
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
            image_bytes = BytesIO()
            image.save(image_bytes, format='PNG')
            image_bytes.seek(0)
            file = discord.File(fp=image_bytes, filename="color_preview.png")
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

            role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")

            role_position = 1
            guild_obj = await self.db.select_one(model.Guilds, {"server": interaction.guild.id})
            if guild_obj:
                top_role = discord.utils.get(interaction.guild.roles, id=guild_obj["role"])
                if top_role:
                    role_position = max(1, top_role.position - 1)

            role_updated = False
            if role is None:
                role = await interaction.guild.create_role(
                    name=f"color-{interaction.user.id}",
                    color=discord.Color(new_colors_val[0]),
                    secondary_color=discord.Color(new_colors_val[1]) if new_colors_val[1] is not None else None
                )
                if role_position > 1:
                    await role.edit(position=role_position)
                role_updated = True

            else:
                current_colors_val = (
                    role.color.value if role.color else None,
                    role.secondary_color.value if role.secondary_color else None
                )

                if current_colors_val != new_colors_val:
                    prev_colors = current_colors_val
                    await role.edit(
                        color=discord.Color(new_colors_val[0]),
                        secondary_color=discord.Color(new_colors_val[1]) if new_colors_val[1] is not None else None,
                        position=role_position
                    )
                    role_updated = True
                else:
                    description = self.msg['color_same']
                    undo_lock = True

            if role_updated:
                display_color = f"{color}" + (f", {secondary_color}" if secondary_color else "")
                if is_black:
                    description = self.msg['color_set_black'].format(display_color)
                else:
                    description = self.msg['color_set'].format(display_color)
                await update_history(self.db, interaction.user.id, interaction.guild.id, primary_val)

            if role and role not in interaction.user.roles:
                await interaction.user.add_roles(role)

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
            if e.code == 50013:
                err_description = self.msg['err_50013']
            elif e.code == 670006:
                err_description = self.msg['err_670006']
            else:
                err_description = self.msg['err_http'].format(e.code, e.text)
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
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down"].format(int(retry_time.timestamp()))
            view = CooldownLayout(messages=self.msg, description=response)
            await interaction.response.send_message(view=view, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
