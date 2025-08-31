import logging
from typing import Optional, Tuple

import discord

logger = logging.getLogger(__name__)


class Layout(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        color: discord.Color,
        display_color: str,
        prev_colors: Optional[Tuple[Optional[int], Optional[int]]] = None,
        role_id: Optional[int] = None,
        author_id: Optional[int] = None,
        description: str = "",
        undo_lock: bool = False
    ):
        super().__init__()
        self.msg = messages
        self.color = color
        self.display_color = display_color
        self.prev_colors = prev_colors
        self.role_id = role_id
        self.author_id = author_id
        self.description = description
        self.undo_lock = undo_lock

        container = discord.ui.Container(accent_colour=self.color)
        container.add_item(
            discord.ui.TextDisplay(self.description)
        )
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        revert_btn = discord.ui.Button(
            label=self.msg.get('revert_button', 'Revert'),
            style=discord.ButtonStyle.secondary,
            emoji="<:back:1408056926121627679>",
            disabled=self.undo_lock
        )
        revert_btn.callback = self._on_revert
        invite_button = discord.ui.Button(
            label='Add HueTweaker to your server',
            style=discord.ButtonStyle.link,
            emoji="<:star:1362879443625971783>",
            url="https://discord.com/api/oauth2/authorize?client_id=1209187999934578738&permissions=1099981745184&scope=bot"
        )
        container.add_item(discord.ui.ActionRow(revert_btn, invite_button))

        self.add_item(container)

    async def _on_revert(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg.get('revert_not_author', "You can't revert this color."), ephemeral=True
            )
            return

        guild = interaction.guild
        role = discord.utils.get(guild.roles, id=self.role_id)
        if role is None:
            self.description = self.msg.get('revert_not_found')
            await interaction.response.edit_message(view=self)
            return

        try:
            if self.prev_colors is None:
                primary_color, secondary_color = discord.Color.default(), None
                hex_str = "default"
            else:
                primary_val, secondary_val = self.prev_colors
                primary_color = discord.Color(primary_val) if primary_val is not None else discord.Color.default()
                secondary_color = discord.Color(secondary_val) if secondary_val is not None else None
                hex_str = f"#{primary_val:06X}".lower() if primary_val is not None else "default"

            await role.edit(color=primary_color, secondary_color=secondary_color)

            for item in self.children:
                if isinstance(item, discord.ui.Container):
                    for subitem in item.children:
                        if isinstance(subitem, discord.ui.ActionRow):
                            for btn in subitem.children:
                                if isinstance(btn, discord.ui.Button) and btn.label == self.msg.get('revert_button', 'Revert'):
                                    btn.disabled = True

            self.description = self.msg.get('color_reverted').format(hex_str)
            await interaction.response.edit_message(view=self)
            logger.info("%s[%s] reverted color for role to %s", interaction.user.name, interaction.locale, hex_str)
        except discord.HTTPException as e:
            await interaction.response.send_message("Failed to revert color.", ephemeral=True)
            logger.critical("%s[%s] HTTP exception while reverting color: %s", interaction.user.name, interaction.locale, e)
