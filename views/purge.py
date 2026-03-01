import logging
import re

import discord

from constants import ACCENT_COLOR, COLOR_ROLE_PATTERN
from database import model
from views.global_view import GlobalLayout

logger = logging.getLogger(__name__)

_color_role_re = re.compile(COLOR_ROLE_PATTERN)


class PurgeView(discord.ui.LayoutView):
    def __init__(self, messages: dict, author_id: int, db, description: str):
        super().__init__()
        self.msg = messages
        self.author_id = author_id
        self.db = db
        self.description = description

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(self.description))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))

        ind_btn = discord.ui.Button(
            label=self.msg['bttn_ind'],
            style=discord.ButtonStyle.green,
            custom_id="individual_roles"
        )
        ind_btn.callback = self._on_confirm
        container.add_item(discord.ui.ActionRow(ind_btn))
        self.add_item(container)

    async def _on_confirm(self, interaction: discord.Interaction):
        if interaction.user.id != self.author_id:
            await interaction.response.send_message(
                self.msg.get("not_author", "You can't confirm this action."),
                ephemeral=True
            )
            return

        async def del_static_roles():
            await self.db.delete(model.Guilds, {"server": interaction.guild.id})
            await self.db.delete(model.Select, {"server_id": interaction.guild.id})


        async def del_individual_roles():
            for role in interaction.guild.roles:
                if _color_role_re.match(role.name):
                    await role.delete()

        try:
            if interaction.data['custom_id'] == 'individual_roles':
                await del_individual_roles()
            elif interaction.data['custom_id'] == 'static_roles':
                await del_static_roles()
            elif interaction.data['custom_id'] == 'both':
                await del_individual_roles()
                await del_static_roles()

            new_view = PurgeView(self.msg, self.author_id, self.db, description=self.msg['purge_ok'])
            await interaction.response.edit_message(view=new_view)

        except Exception as e:
            description = self.msg['exception']
            view = GlobalLayout(messages=self.msg, description=description, docs_page="commands/force-purge")
            logger.critical("%s[%s] raise critical exception - %r", interaction.user.name, interaction.user.id, e)
            await interaction.response.edit_message(view=view)
