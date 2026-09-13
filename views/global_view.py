import logging

import discord

from constants import ACCENT_COLOR, DOCS_BASE_URL, INVITE_URL

logger = logging.getLogger(__name__)


async def safe_defer(interaction: discord.Interaction, **kwargs) -> bool:
    """Acknowledge a component interaction. Returns False if it can no longer be answered."""
    try:
        await interaction.response.defer(**kwargs)
        return True
    except discord.InteractionResponded:
        return True
    except discord.HTTPException as e:
        logger.warning("%s[%s] failed to acknowledge interaction: %s", interaction.user.name, interaction.user.id, e)
        return False


def make_invite_button() -> discord.ui.Button:
    return discord.ui.Button(
        label="Add HueTweaker to your server",
        style=discord.ButtonStyle.link,
        emoji="<:star:1362879443625971783>",
        url=INVITE_URL,
    )


def make_docs_button(page: str = "", label: str = "See documentation") -> discord.ui.Button:
    return discord.ui.Button(
        label=label,
        style=discord.ButtonStyle.link,
        emoji="<:docs:1362879505613586643>",
        url=f"{DOCS_BASE_URL}/{page}",
    )


class GlobalLayout(discord.ui.LayoutView):
    def __init__(
        self,
        messages: dict,
        description: str = "",
        docs_page: str = "",
    ):
        super().__init__()
        self.msg = messages
        self.description = description
        self.docs_page = docs_page

        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(self.description))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
        container.add_item(
            discord.ui.ActionRow(make_docs_button(self.docs_page), make_invite_button())
        )
        self.add_item(container)
