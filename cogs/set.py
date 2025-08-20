import logging
from datetime import datetime, timedelta

import discord
from discord import app_commands, Embed
from discord.ext import commands

from database import model
from utils.color_parse import fetch_color_representation, color_parser
from utils.cooldown_check import is_user_on_cooldown

logger = logging.getLogger(__name__)


class RevertColorView(discord.ui.View):
    def __init__(self, prev_color_val: int | None, role_id: int, author_id: int, button_label: str | None = None, revert_message: str | None = None, timeout: float = 300):
        super().__init__(timeout=timeout)
        self.prev_color_val = prev_color_val
        self.role_id = role_id
        self.author_id = author_id
        self.button_label = button_label
        self.revert_message = revert_message

        btn = discord.ui.Button(label=self.button_label, style=discord.ButtonStyle.secondary)
        async def _btn_callback(interaction: discord.Interaction):
            await self._on_revert(interaction, btn)
        btn.callback = _btn_callback
        self.add_item(btn)

    async def _on_revert(self, interaction: discord.Interaction, button: discord.ui.Button):
        guild = interaction.guild
        role = discord.utils.get(guild.roles, id=self.role_id)
        if role is None:
            await interaction.response.send_message("User role not found.", ephemeral=True)
            return

        try:
            if self.prev_color_val is None:
                await role.edit(colour=discord.Colour.default())
                hex_str = "default"
            else:
                await role.edit(colour=discord.Colour(self.prev_color_val))
                hex_str = f"#{self.prev_color_val:06X}".lower()

            button.disabled = True
            embed = discord.Embed(description=self.revert_message.format(hex_str))
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            await interaction.response.edit_message(embed=embed, view=self)
            logger.info("%s[%s] reverted color for role to %s", interaction.user.name, interaction.locale, hex_str)
        except discord.HTTPException as e:
            await interaction.response.send_message("Failed to revert color.", ephemeral=True)
            logger.critical("%s[%s] HTTP exception while reverting color: %s", interaction.user.name, interaction.locale, e)


async def dynamic_cooldown(interaction: discord.Interaction):
    return await is_user_on_cooldown(interaction)


class SetCog(commands.Cog):
    def __init__(self, bot: commands.Bot) -> None:
        self.bot = bot
        self.db = bot.db
        self.msg = bot.messages

    @app_commands.command(name="set", description="Set color using HEX code or CSS color name")
    @app_commands.describe(color="Color code (e.g. #9932f0) or CSS color name (e.g royalblue)")
    @app_commands.checks.dynamic_cooldown(dynamic_cooldown, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
        embed: Embed = discord.Embed(title="", description=f"", color=4539717)
        try:
            await interaction.response.defer(ephemeral=True)

            color = fetch_color_representation(interaction, color)
            color_match = color_parser(color)
            if color_match is None:
                embed.description = self.msg['color_format']
                logger.info("%s[%s] issued bot command: /set (invalid format)", interaction.user.name, interaction.user.id)
            else:
                role = discord.utils.get(interaction.guild.roles, name=f"color-{interaction.user.id}")
                new_color_val = int(color_match, 16)

                if role is None:
                    role_position = 1
                    with self.db as db_session:
                        guild_row = db_session.select_one(model.guilds_class("guilds"), {"server": interaction.guild.id})
                        
                    if guild_row:
                        top_role = discord.utils.get(interaction.guild.roles, id=guild_row.get("role", None))
                        if top_role:
                            role_position = max(1, top_role.position - 1)
                    role = await interaction.guild.create_role(
                        name=f"color-{interaction.user.id}",
                        colour=discord.Colour(new_color_val)
                    )
                    if role_position > 1:
                        await role.edit(position=role_position)
                    embed.description = self.msg['color_set'].format(color)
                else:
                    if not role.colour or role.colour.value != new_color_val:
                        prev_color_val = role.colour.value if getattr(role, "colour", None) and getattr(role.colour, "value", 0) else None

                        await role.edit(colour=discord.Colour(new_color_val))
                        embed.description = self.msg['color_set'].format(color)
                    else:
                        embed.description = self.msg['color_same'].format(color)

                if role not in interaction.user.roles:
                    await interaction.user.add_roles(role)

                embed.color = discord.Colour(new_color_val)

        except ValueError:
            embed.description = self.msg['color_format']

        except discord.HTTPException as e:
            embed.clear_fields()
            if e.code == 50013:
                embed.description = self.msg['err_50013']
            else:
                embed.description = self.msg['err_http'].format(e.code, e.text)
            logger.critical("%s[%s] raise HTTP exception: %s", interaction.user.name, interaction.user.id, e.text)

        except Exception as e:
            embed.clear_fields()
            embed.description = self.msg['exception']
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)

        finally:
            embed.set_image(url="https://i.imgur.com/rXe4MHa.png")
            # spróbuj wysłać view z przyciskiem przywracania poprzedniego koloru
            try:
                btn_label = self.msg.get('revert_button') if hasattr(self, 'msg') else None
                revert_msg = self.msg.get('color_reverted') if hasattr(self, 'msg') else None
                view = RevertColorView(prev_color_val if 'prev_color_val' in locals() else None, role.id if role is not None else 0, interaction.user.id, button_label=btn_label, revert_message=revert_msg)
                await interaction.followup.send(embed=embed, view=view)
            except Exception:
                await interaction.followup.send(embed=embed)
            logger.info("%s[%s] issued bot command: /set %s", interaction.user.name, interaction.locale, color)

    @set.error
    async def command_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            retry_time = datetime.now() + timedelta(seconds=error.retry_after)
            response = self.msg["cool_down_with_api"].format(int(retry_time.timestamp()))
            await interaction.response.send_message(response, ephemeral=True, delete_after=error.retry_after)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
