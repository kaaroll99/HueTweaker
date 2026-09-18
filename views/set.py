import logging
from typing import Optional, Tuple

import discord

from utils.color_format import format_colors_label
from utils.role_manager import ApplyResult, revert_color_role
from views.global_view import error_description, make_invite_button, safe_defer

logger = logging.getLogger(__name__)


class Layout(discord.ui.LayoutView):
    """Result of a color change with an "Undo to previous color" button.

    ``prev_colors=None`` means the role did not exist before the change, so undo deletes it.
    ``undo_lock=True`` disables the button (nothing changed)."""

    def __init__(
        self,
        messages: dict,
        color: discord.Color,
        prev_colors: Optional[Tuple[int, Optional[int]]] = None,
        role_id: Optional[int] = None,
        author_id: Optional[int] = None,
        description: str = "",
        undo_lock: bool = False,
    ):
        super().__init__()
        self.msg = messages
        self.color = color
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
        primary_val: int,
        author_id: int,
        description: str,
    ) -> "Layout":
        return cls(
            messages=messages,
            color=discord.Color(primary_val),
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

            await revert_color_role(guild, self.role_id, self.prev_colors)

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


class ConfirmationView(discord.ui.LayoutView):
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
