import random
import re

import discord

from utils.color_format import ColorUtils

MAX_COLOR_INPUT_LEN = 32
BLACK_HEX = "000000"
# Discord treats #000000 as "no color", so pure black is stored as the nearest visible value.
NEAR_BLACK_HEX = "000001"

_mention_re = re.compile(r"^<@!?(\d{15,20})>$")


class MentionedUserHasNoColor(ValueError):
    """The mentioned user has no bot-managed color role."""


def _role_colors(role: discord.Role) -> tuple[str, str | None]:
    primary = f"{role.color.value:06x}"
    secondary = f"{role.secondary_color.value:06x}" if role.secondary_color else None
    return primary, secondary


def resolve_mention(interaction: discord.Interaction, text: str) -> tuple[str, str | None] | None:
    """If ``text`` mentions a user, return that user's ``(primary, secondary)`` hex; else ``None``.
    Raises ``MentionedUserHasNoColor`` when the user has no color role (or a colorless one)."""
    match = _mention_re.match(text.strip())
    if match is None:
        return None
    if interaction.guild is None:
        raise MentionedUserHasNoColor
    copy_role = discord.utils.get(interaction.guild.roles, name=f"color-{match.group(1)}")
    if copy_role is None or copy_role.color.value == 0:
        raise MentionedUserHasNoColor
    return _role_colors(copy_role)


def fetch_color_representation(interaction: discord.Interaction, color: str) -> str:
    """Turn ``@mention`` / ``random`` into a hex string; other input is returned unchanged."""
    if len(color) > MAX_COLOR_INPUT_LEN:
        raise ValueError
    mentioned = resolve_mention(interaction, color)
    if mentioned is not None:
        return f"#{mentioned[0]}"
    if color.strip().lower() == "random":
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    return color


def color_parser(color: str) -> str | None:
    """Parse hex / CSS name / rgb() / hsl() / cmyk() into 6 lowercase hex digits, or ``None``."""
    if len(color) > MAX_COLOR_INPUT_LEN:
        return None
    result = ColorUtils(color).color_converter()
    if result is not None:
        return result["Hex"].lstrip("#").lower()
    return None


def check_black(primary_hex: str | None, secondary_hex: str | None) -> tuple[str | None, str | None, bool]:
    is_black = False
    if primary_hex == BLACK_HEX:
        is_black = True
        primary_hex = NEAR_BLACK_HEX
    if secondary_hex == BLACK_HEX:
        is_black = True
        secondary_hex = NEAR_BLACK_HEX
    return primary_hex, secondary_hex, is_black


def parse_color_pair(
    interaction: discord.Interaction, color: str, secondary_color: str | None
) -> tuple[int, int | None, bool]:
    """Resolve the ``/set``, ``/gradient`` and ``/force set`` inputs into ``(primary, secondary, is_black)``
    integer values. Mentioning a user with a gradient (and giving no secondary color) copies the
    whole gradient. Raises ``ValueError`` on invalid input."""
    primary_hex: str | None
    secondary_hex: str | None = None

    mentioned = resolve_mention(interaction, color) if len(color) <= MAX_COLOR_INPUT_LEN else None
    if mentioned is not None:
        primary_hex, copied_secondary = mentioned
        if secondary_color is None:
            secondary_hex = copied_secondary
    else:
        primary_hex = color_parser(fetch_color_representation(interaction, color))

    if secondary_color:
        secondary_hex = color_parser(fetch_color_representation(interaction, secondary_color))
        if secondary_hex is None:
            raise ValueError

    if primary_hex is None:
        raise ValueError

    primary_hex, secondary_hex, is_black = check_black(primary_hex, secondary_hex)
    return int(primary_hex, 16), (int(secondary_hex, 16) if secondary_hex else None), is_black
