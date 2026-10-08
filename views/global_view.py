import logging

import discord

from constants import ACCENT_COLOR, DOCS_BASE_URL, INVITE_URL, VOTE_URL
from analytics.recorder import recorder
from utils.role_manager import ColorRoleError

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


def http_error_description(messages: dict, error: discord.HTTPException) -> str:
    if error.code == 50013:
        return messages["err_50013"]
    if error.code == 670006:
        return messages["err_670006"]
    return messages["err_http"].format(error.code, error.text)


def error_description(messages: dict, error: Exception) -> str:
    """User-facing text for any failure of a color operation."""
    if isinstance(error, ColorRoleError):
        return messages[error.message_key]
    if isinstance(error, discord.HTTPException):
        return http_error_description(messages, error)
    return messages["exception"]


def make_invite_button() -> discord.ui.Button:
    return discord.ui.Button(
        label="Add HueTweaker to your server",
        style=discord.ButtonStyle.link,
        emoji="<:star:1362879443625971783>",
        url=INVITE_URL,
    )


def make_vote_button() -> discord.ui.Button:
    return discord.ui.Button(
        label="Vote on top.gg",
        style=discord.ButtonStyle.link,
        emoji="<:star:1362879443625971783>",
        url=VOTE_URL,
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


class VoteLayout(discord.ui.LayoutView):
    """Asks the user to vote on top.gg to unlock a feature."""

    def __init__(self, messages: dict, description: str = "", docs_page: str = ""):
        super().__init__()
        container = discord.ui.Container(accent_colour=discord.Color(ACCENT_COLOR))
        container.add_item(discord.ui.TextDisplay(description))
        container.add_item(discord.ui.Separator(spacing=discord.SeparatorSpacing.large))
        container.add_item(discord.ui.ActionRow(make_vote_button(), make_docs_button(docs_page)))
        self.add_item(container)


async def gradient_gate(
    messages: dict, votes, interaction: discord.Interaction, source: str, docs_page: str = "", require_vote: bool = True
) -> discord.ui.LayoutView | None:
    if "ENHANCED_ROLE_COLORS" not in interaction.guild.features:
        recorder.blocked(interaction, source, "gradient_unsupported")
        return GlobalLayout(messages, messages['err_670006'], docs_page)
    if require_vote and not await votes.has_voted(interaction.user.id):
        recorder.blocked(interaction, source, "vote_required")
        return VoteLayout(messages, messages['vote_gradient'], docs_page)
    return None
