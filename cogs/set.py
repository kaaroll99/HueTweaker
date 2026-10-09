import logging
import random
import time
from typing import Optional

import discord
from discord import app_commands
from discord.ext import commands

from analytics.recorder import recorder
from cogs._base import BaseCog, preset_choices
from constants import FREE_SET_USES, FREE_SET_WINDOW
from utils.color_format import ColorUtils, format_colors_label
from utils.color_parse import parse_color_pair
from utils.history_manager import update_history
from utils.role_manager import apply_color_role
from utils.vote_manager import UsageQuota, in_grace_period
from views.global_view import GlobalLayout, VoteLayout, gradient_gate
from views.set import Layout, ConfirmationView, hiding_role

logger = logging.getLogger(__name__)

TIP_COMMANDS = ("set", "gradient", "holographic", "match", "favorites add", "history", "colors", "check")


class SetCog(BaseCog):
    def __init__(self, bot: commands.Bot) -> None:
        super().__init__(bot)
        self.set_quota = UsageQuota(FREE_SET_USES, FREE_SET_WINDOW)

    @app_commands.command(name="set", description="Set your username color")
    @app_commands.describe(
        color="HEX (#9932f0), CSS name (royalblue), rgb/hsl/cmyk, random, @user or a preset (sunset)"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def set(self, interaction: discord.Interaction, color: str) -> None:
        await self._apply_color(interaction, "set", color, None)

    @app_commands.command(name="gradient", description="Set a two-color gradient or a gradient preset")
    @app_commands.describe(
        color="First color, or a preset name (e.g. sunset) on its own",
        secondary_color="Second color (leave empty for a preset or @user)"
    )
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def gradient(self, interaction: discord.Interaction, color: str, secondary_color: Optional[str] = None) -> None:
        await self._apply_color(interaction, "gradient", color, secondary_color)

    @gradient.autocomplete("color")
    async def gradient_color_autocomplete(self, interaction: discord.Interaction, current: str) -> list[app_commands.Choice[str]]:
        return preset_choices(current)

    @app_commands.command(name="holographic", description="Set Discord's holographic username style")
    @app_commands.checks.cooldown(1, 10.0, key=lambda i: (i.guild_id, i.user.id))
    @app_commands.guild_only()
    async def holographic(self, interaction: discord.Interaction) -> None:
        await self._apply_color(interaction, "holographic", "holographic", None)

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

            colors, is_black = await parse_color_pair(interaction, self.db, color, secondary_color)
            primary_val, secondary_val, tertiary_val = colors
            label = format_colors_label(*colors)

            if command_name == "gradient" and secondary_val is None:
                await self.respond(interaction, GlobalLayout(self.msg, self.msg['gradient_needs_two'], docs_page))
                return

            blocked = await self._access_gate(interaction, command_name, secondary_val, docs_page)
            if blocked is not None:
                await self.respond(interaction, blocked)
                logger.info("%s[%s] issued bot command: /%s (blocked: gradients unavailable or vote required)", interaction.user.name, interaction.user.id, command_name)
                return

            image = ColorUtils.generate_preview_image(member.display_name, *colors)
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

            if secondary_val is None and not in_grace_period(guild):
                self.set_quota.consume(member.id)

            result = await apply_color_role(guild, member, primary_val, secondary_val, self.db, bot_user.id,
                                            tertiary_val=tertiary_val)

            if not result.changed:
                description = self.msg['color_same']
            else:
                template = self.msg['color_set_black'] if is_black else self.msg['color_set']
                description = template.format(label)
                # A hidden color gets a warning from Layout instead of a tip.
                if hiding_role(member, result.role) is None:
                    description += await self._tip(interaction, command_name, colors)
                await update_history(self.db, member.id, guild.id, *colors)
                recorder.color(interaction, command_name, colors)

            view = Layout.from_result(self.msg, result, primary_val, member.id, description, member)
            await self.respond(interaction, view)

        except ValueError:
            await self.respond(interaction, GlobalLayout(self.msg, self.msg['color_format'], docs_page))
            logger.info("%s[%s] issued bot command: /%s (invalid format)", interaction.user.name, interaction.user.id, command_name)

        except Exception as e:
            await self.respond(interaction, GlobalLayout(self.msg, self.describe_error(e), docs_page))
            self.log_command_error(interaction, command_name, e)

        finally:
            logger.info("%s[%s] issued bot command: /%s %s", interaction.user.name, interaction.locale, command_name, log_color)

    async def _access_gate(
        self, interaction: discord.Interaction, source: str, secondary_val: Optional[int], docs_page: str
    ) -> Optional[discord.ui.LayoutView]:
        """The view to show instead of applying the color, or ``None`` when the user may proceed.
        A gradient needs server support first, then a vote. A solid color is free for
        ``FREE_SET_USES`` changes per window, then needs a vote, except on a newly joined server."""
        if secondary_val is not None:
            return await gradient_gate(self.msg, self.votes, interaction, source, docs_page)
        if in_grace_period(interaction.guild):
            return None

        user_id = interaction.user.id
        retry_after = self.set_quota.retry_after(user_id)
        if retry_after > 0 and not await self.votes.has_voted(user_id):
            recorder.blocked(interaction, source, "set_limit")
            retry_at = f"<t:{int(time.time() + retry_after)}:R>"
            return VoteLayout(self.msg, self.msg['vote_set_limit'].format(FREE_SET_USES, retry_at), docs_page)
        return None

    async def _tip(self, interaction: discord.Interaction, command_name: str, colors) -> str:
        _, secondary_val, tertiary_val = colors
        mentions = {name.replace(" ", "_"): await self.mention(name) for name in TIP_COMMANDS}

        if secondary_val is None and not in_grace_period(interaction.guild):
            retry_after = self.set_quota.retry_after(interaction.user.id)
            if retry_after > 0 and not await self.votes.has_voted(interaction.user.id):
                return self.msg['tip_set_limit'].format(time=f"<t:{int(time.time() + retry_after)}:R>", **mentions)

        # match, favorites and gradient twice: the features most /set users don't know about yet.
        tips = ["match", "match", "favorites", "favorites", "history", "colors", "check"]
        if command_name == "set":
            tips.append("random")
        if "ENHANCED_ROLE_COLORS" in interaction.guild.features:
            if secondary_val is None:
                tips += ["gradient", "gradient"]
            if tertiary_val is None:
                tips.append("holographic")
        return self.msg['tip_' + random.choice(tips)].format(**mentions)

    @set.error
    async def set_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)

    @gradient.error
    async def gradient_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)

    @holographic.error
    async def holographic_error(self, interaction: discord.Interaction, error: app_commands.AppCommandError):
        if isinstance(error, app_commands.CommandOnCooldown):
            await self.handle_cooldown_error(interaction, error)


async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(SetCog(bot))
