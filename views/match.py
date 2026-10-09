import logging

import discord

from analytics.recorder import recorder
from constants import ACCENT_COLOR
from utils.color_format import format_colors_label
from utils.history_manager import update_history
from utils.role_manager import apply_color_role
from views.global_view import error_description, gradient_gate, make_docs_button, safe_defer
from views.set import Layout, hidden_warning

logger = logging.getLogger(__name__)


class MatchView(discord.ui.LayoutView):
    def __init__(self, messages, description, bot, file, colors: list[int], author_id: int,
                 docs_page: str = "commands/match"):
        super().__init__()
        self.msg = messages
        self.bot = bot
        self.file = file
        self.author_id = author_id
        self.docs_page = docs_page

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(description))

        gallery = discord.ui.MediaGallery()
        gallery.add_item(media="attachment://" + file.filename)
        container.add_item(gallery)
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.small))

        buttons = []
        for i, color in enumerate(colors, start=1):
            button = discord.ui.Button(label=str(i), style=discord.ButtonStyle.secondary)
            button.callback = self._make_callback(color, None)
            buttons.append(button)
        if len(colors) >= 2:
            gradient_button = discord.ui.Button(label=str(len(colors) + 1), emoji="🌈", style=discord.ButtonStyle.primary)
            gradient_button.callback = self._make_callback(colors[0], colors[1])
            buttons.append(gradient_button)
        container.add_item(discord.ui.ActionRow(*buttons))
        container.add_item(discord.ui.ActionRow(make_docs_button(self.docs_page)))

        self.add_item(container)

    def _make_callback(self, primary: int, secondary: int | None):
        async def _callback(interaction: discord.Interaction):
            await self._apply(interaction, primary, secondary)
        return _callback

    async def _apply(self, interaction: discord.Interaction, primary: int, secondary: int | None) -> None:
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(self.msg['revert_not_author'], ephemeral=True)
            return

        if not await safe_defer(interaction, ephemeral=True, thinking=True):
            return

        label = format_colors_label(primary, secondary)
        try:
            if secondary is not None:
                blocked = await gradient_gate(self.msg, self.bot.votes, interaction, "match", self.docs_page)
                if blocked is not None:
                    await interaction.followup.send(view=blocked, ephemeral=True)
                    return

            result = await apply_color_role(
                interaction.guild, interaction.user, primary, secondary, self.bot.db, self.bot.user.id
            )
            if result.changed:
                description = self.msg['color_set'].format(label)
                await update_history(self.bot.db, interaction.user.id, interaction.guild.id, primary, secondary)
                recorder.color(interaction, "match", (primary, secondary, None))
            else:
                description = self.msg['color_same']

            description += await hidden_warning(self.bot.db, self.msg, interaction.user, result)
            view = Layout.from_result(self.msg, result, primary, interaction.user.id, description)
            await interaction.followup.send(view=view, ephemeral=True)
            logger.info("%s[%s] applied color %s from /match", interaction.user.name, interaction.locale, label)
        except Exception as e:
            logger.warning("%s[%s] failed to apply color from /match: %r", interaction.user.name, interaction.locale, e)
            try:
                await interaction.followup.send(error_description(self.msg, e), ephemeral=True)
            except discord.HTTPException:
                pass
