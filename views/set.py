import logging
from typing import Optional

import discord

from analytics.recorder import recorder
from core.database import model
from utils.color_format import Colors, format_colors_label
from utils.history_manager import update_history
from utils.role_manager import (TOPROLE_MODE_AUTO, ApplyResult, ColorChangedSince, apply_color_role,
                                colored_roles_above, get_toprole_mode, revert_color_role)
from views.global_view import error_description, gradient_gate, make_invite_button, safe_defer

logger = logging.getLogger(__name__)


def hiding_role(member: discord.Member, role: discord.Role) -> discord.Role | None:
    """Return the member's highest colored role above ``role``, whose color shows instead, or None."""
    # The cached role is the fresh one: placing the block replaces the guild's roles in the cache.
    above = colored_roles_above(member.roles, member.guild.get_role(role.id) or role)
    return max(above) if above else None


async def hidden_warning(db, messages: dict, member: discord.Member, result: ApplyResult) -> str:
    """Return a warning when a higher colored role hides the changed color, else an empty string.

    The warning names the fix that works here: ``/setup toprole auto`` when the bot's role is
    above the hiding role, otherwise moving the bot's role.
    """
    hidden = hiding_role(member, result.role) if result.changed else None
    if hidden is None:
        return ""
    me = member.guild.me
    try:
        mode = get_toprole_mode(await db.select_one(model.Guilds, {"server": member.guild.id}))
    except Exception as e:
        logger.warning("Could not read the placement mode of guild %s: %r", member.guild.id, e)
        mode = None
    # auto places the block right below the bot's role, so it helps only when the bot is above the hiding role
    # (already in auto, running it again re-places a block that could not be moved before).
    if me is not None and hidden < me.top_role:
        fix = "color_hidden_fix_mode"
    else:
        fix = "color_hidden_fix_bot_role" if mode == TOPROLE_MODE_AUTO else "color_hidden_fix_both"
    return messages['color_hidden'].format(role=hidden.mention, fix=messages[fix].format(role=hidden.mention))


class Layout(discord.ui.LayoutView):
    """Result of a color change with an "Undo to previous color" button.

    ``prev_colors=None`` means the role did not exist before the change, so undo deletes it.
    ``set_colors`` are the colors this change set; undo refuses once the role has others.
    ``undo_lock=True`` disables the button (nothing changed).
    """

    def __init__(
        self,
        messages: dict,
        set_colors: Colors,
        prev_colors: Optional[Colors] = None,
        role_id: Optional[int] = None,
        author_id: Optional[int] = None,
        description: str = "",
        undo_lock: bool = False,
    ):
        super().__init__()
        self.msg = messages
        self.color = discord.Color(set_colors[0])
        self.set_colors = set_colors
        self.prev_colors = prev_colors
        self.role_id = role_id
        self.author_id = author_id
        self.description = description
        self.undo_lock = undo_lock

        container = discord.ui.Container(accent_colour=self.color)
        self.text_display = discord.ui.TextDisplay(self.description)
        container.add_item(self.text_display)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        self.revert_btn = discord.ui.Button(
            label=self.msg['revert_button'],
            style=discord.ButtonStyle.secondary,
            emoji="<:back:1408056926121627679>",
            disabled=self.undo_lock,
        )
        self.revert_btn.callback = self._on_revert
        container.add_item(discord.ui.ActionRow(self.revert_btn, make_invite_button()))

        self.add_item(container)

    @classmethod
    def from_result(
        cls,
        messages: dict,
        result: ApplyResult,
        author_id: int,
        description: str,
    ) -> "Layout":
        """Build the result view from an ``ApplyResult``; Undo is disabled when nothing changed."""
        return cls(
            messages=messages,
            set_colors=result.colors,
            prev_colors=result.prev_colors,
            role_id=result.role.id,
            author_id=author_id,
            description=description,
            undo_lock=not result.changed,
        )

    def _set_description(self, description: str) -> None:
        self.description = description
        self.text_display.content = description

    async def _on_revert(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            try:
                await interaction.response.send_message(
                    self.msg["revert_not_author"], ephemeral=True
                )
            except discord.HTTPException:
                pass
            return

        if not await safe_defer(interaction):
            return

        guild = interaction.guild
        self.revert_btn.disabled = True

        try:
            if guild is None or self.role_id is None or guild.get_role(self.role_id) is None:
                self._set_description(self.msg['revert_not_found'])
                await interaction.edit_original_response(view=self)
                return

            try:
                await revert_color_role(guild, self.role_id, self.prev_colors, self.set_colors)
            except ColorChangedSince:
                self._set_description(self.msg['revert_changed'])
                await interaction.edit_original_response(view=self)
                return

            if self.prev_colors is None:
                self._set_description(self.msg['revert_removed'])
                label = "none"
            else:
                label = format_colors_label(*self.prev_colors)
                self._set_description(self.msg['color_reverted'].format(label))
            await interaction.edit_original_response(view=self)
            logger.info("%s[%s] reverted color of role %s to %s", interaction.user.name, interaction.locale, self.role_id, label)
        except Exception as e:
            logger.warning("%s[%s] failed to revert color: %r", interaction.user.name, interaction.locale, e)
            try:
                await interaction.followup.send(error_description(self.msg, e), ephemeral=True)
            except discord.HTTPException:
                pass


async def apply_from_button(
    view: discord.ui.LayoutView,
    interaction: discord.Interaction,
    colors: Colors,
    source: str,
    success_key: str,
    require_vote: bool = True,
) -> None:
    """Apply a color picked with a button or menu (palette, favorites, history, ``/match``).

    ``view`` provides ``msg``, ``bot``, ``author_id`` and ``docs_page``. A gradient goes through
    ``gradient_gate``; the result is sent as a ``Layout`` with Undo.
    """
    msg = view.msg
    if view.author_id is not None and interaction.user.id != view.author_id:
        await interaction.response.send_message(msg['revert_not_author'], ephemeral=True)
        return
    if not await safe_defer(interaction, ephemeral=True, thinking=True):
        return

    primary, secondary, tertiary = colors
    label = format_colors_label(*colors)
    db = view.bot.db
    try:
        if secondary is not None:
            blocked = await gradient_gate(msg, view.bot.votes, interaction, source, view.docs_page,
                                          require_vote=require_vote)
            if blocked is not None:
                await interaction.followup.send(view=blocked, ephemeral=True)
                return

        result = await apply_color_role(interaction.guild, interaction.user, primary, secondary, db,
                                        view.bot.user.id, tertiary_val=tertiary)
        if result.changed:
            description = msg[success_key].format(label)
            await update_history(db, interaction.user.id, interaction.guild.id, *colors)
            recorder.color(interaction, source, colors)
        else:
            description = msg['color_same']

        description += await hidden_warning(db, msg, interaction.user, result)
        await interaction.followup.send(view=Layout.from_result(msg, result, interaction.user.id, description),
                                        ephemeral=True)
        logger.info("%s[%s] applied %s color %s", interaction.user.name, interaction.locale, source, label)
    except Exception as e:
        logger.warning("%s[%s] failed to apply %s color: %r", interaction.user.name, interaction.locale, source, e)
        try:
            await interaction.followup.send(error_description(msg, e), ephemeral=True)
        except discord.HTTPException:
            pass


class ConfirmationView(discord.ui.LayoutView):
    """Accept/Cancel prompt; after ``wait()``, ``value`` is True, False, or None on timeout."""

    def __init__(self, author_id, text, color=discord.Color.default(), image_url=None):
        super().__init__(timeout=60)
        self.author_id = author_id
        self.value = None

        container = discord.ui.Container(accent_colour=color)
        container.add_item(discord.ui.TextDisplay(text))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        if image_url:
            gallery = discord.ui.MediaGallery()
            gallery.add_item(media=image_url)
            container.add_item(gallery)

        confirm_btn = discord.ui.Button(
            label="Accept",
            emoji="<:ok:1362879418640498748>",
            style=discord.ButtonStyle.green,
        )
        cancel_btn = discord.ui.Button(
            label="Cancel",
            emoji="<:back:1408056926121627679>",
            style=discord.ButtonStyle.red,
        )
        confirm_btn.callback = self._on_confirm
        cancel_btn.callback = self._on_cancel

        container.add_item(discord.ui.ActionRow(confirm_btn, cancel_btn, make_invite_button()))
        self.add_item(container)

    async def _on_confirm(self, interaction: discord.Interaction):
        await self._resolve(interaction, True)

    async def _on_cancel(self, interaction: discord.Interaction):
        await self._resolve(interaction, False)

    async def _resolve(self, interaction: discord.Interaction, value: bool):
        if interaction.user.id != self.author_id:
            try:
                await interaction.response.send_message("This is not your confirmation.", ephemeral=True)
            except discord.HTTPException:
                pass
            return

        if self.value is not None:
            return

        self.value = value
        self.stop()

        try:
            await interaction.response.defer()
        except (discord.NotFound, discord.InteractionResponded):
            pass
        except discord.HTTPException as e:
            logger.warning("%s[%s] failed to acknowledge confirmation: %s", interaction.user.name, interaction.user.id, e)

    async def on_error(self, interaction: discord.Interaction, error: Exception, item: discord.ui.Item) -> None:
        logger.error("%s[%s] error in ConfirmationView: %r", interaction.user.name, interaction.user.id, error, exc_info=error)
