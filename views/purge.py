import logging

import discord

from constants import ACCENT_COLOR
from utils.role_manager import purge_color_roles
from views.global_view import GlobalLayout, error_description, safe_defer

logger = logging.getLogger(__name__)


class PurgeView(discord.ui.LayoutView):
    def __init__(self, messages: dict, author_id: int, description: str, confirm: bool = True):
        super().__init__()
        self.msg = messages
        self.author_id = author_id
        self.description = description

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(self.description))

        if confirm:
            container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
            confirm_btn = discord.ui.Button(label=self.msg['bttn_ind'], style=discord.ButtonStyle.danger)
            confirm_btn.callback = self._on_confirm
            container.add_item(discord.ui.ActionRow(confirm_btn))
        self.add_item(container)

    async def _on_confirm(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg['not_author'],
                ephemeral=True
            )
            return

        # Deleting roles can take far longer than the 3 s an interaction stays valid: ack first.
        if not await safe_defer(interaction):
            return
        self.stop()

        try:
            result = await purge_color_roles(interaction.guild)
            if result.failed:
                description = self.msg['purge_partial'].format(result.deleted, result.failed)
            else:
                description = self.msg['purge_ok'].format(result.deleted)
            new_view = PurgeView(self.msg, self.author_id, description=description, confirm=False)
            await interaction.edit_original_response(view=new_view)
            logger.info("%s[%s] purged color roles in guild %s: %s", interaction.user.name, interaction.locale,
                        interaction.guild_id, result)

        except Exception as e:
            view = GlobalLayout(messages=self.msg, description=error_description(self.msg, e), docs_page="commands/force-purge")
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
            try:
                await interaction.edit_original_response(view=view)
            except discord.HTTPException:
                pass
