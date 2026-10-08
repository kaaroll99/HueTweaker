import random
import re

import discord

from utils.color_format import ColorUtils, Colors, preset_colors
from utils.role_manager import find_color_role

MAX_COLOR_INPUT_LEN = 32
BLACK_HEX = "000000"
# Discord treats #000000 as "no color", so pure black is stored as the nearest visible value.
NEAR_BLACK_HEX = "000001"

_mention_re = re.compile(r"^<@!?(\d{15,20})>$")


class MentionedUserHasNoColor(ValueError):
    """The mentioned user has no bot-managed color role."""


def _role_colors(role: discord.Role) -> tuple[str, str | None, str | None]:
    primary = f"{role.color.value:06x}"
    secondary = f"{role.secondary_color.value:06x}" if role.secondary_color else None
    tertiary = f"{role.tertiary_color.value:06x}" if role.tertiary_color else None
    return primary, secondary, tertiary


async def resolve_mention(interaction: discord.Interaction, db, text: str) -> tuple[str, str | None, str | None] | None:
    """If ``text`` mentions a user, return that user's ``(primary, secondary, tertiary)`` hex; else ``None``.
    Raises ``MentionedUserHasNoColor`` when the user has no color role (or a colorless one)."""
    match = _mention_re.match(text.strip())
    if match is None:
        return None
    if interaction.guild is None:
        raise MentionedUserHasNoColor
    copy_role = await find_color_role(db, interaction.guild, int(match.group(1)))
    if copy_role is None or copy_role.color.value == 0:
        raise MentionedUserHasNoColor
    return _role_colors(copy_role)


async def fetch_color_representation(interaction: discord.Interaction, db, color: str) -> str:
    """Turn ``@mention`` / ``random`` into a hex string; other input is returned unchanged."""
    if len(color) > MAX_COLOR_INPUT_LEN:
        raise ValueError
    mentioned = await resolve_mention(interaction, db, color)
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


def parse_static_style(color: str, secondary_color: str | None = None) -> tuple[Colors, bool]:
    if not secondary_color:
        preset = preset_colors(color)
        if preset is not None:
            return preset, False
    primary_hex = color_parser(color)
    secondary_hex = color_parser(secondary_color) if secondary_color else None
    if primary_hex is None or (secondary_color and secondary_hex is None):
        raise ValueError
    primary_hex, secondary_hex, is_black = check_black(primary_hex, secondary_hex)
    return (int(primary_hex, 16), (int(secondary_hex, 16) if secondary_hex else None), None), is_black


async def parse_color_pair(
    interaction: discord.Interaction, db, color: str, secondary_color: str | None
) -> tuple[Colors, bool]:
    """Resolve the ``/set``, ``/gradient`` and ``/force set`` inputs into
    ``((primary, secondary, tertiary), is_black)``. A preset name or a mention of a user with a
    gradient (and no secondary color) gives the whole style. Raises ``ValueError`` on invalid input."""
    if len(color) > MAX_COLOR_INPUT_LEN:
        raise ValueError
    if secondary_color is None:
        preset = preset_colors(color)
        if preset is not None:
            return preset, False

    primary_hex: str | None
    secondary_hex: str | None = None
    tertiary_hex: str | None = None

    mentioned = await resolve_mention(interaction, db, color)
    if mentioned is not None:
        primary_hex, copied_secondary, copied_tertiary = mentioned
        if secondary_color is None:
            secondary_hex, tertiary_hex = copied_secondary, copied_tertiary
    else:
        primary_hex = color_parser(await fetch_color_representation(interaction, db, color))

    if secondary_color:
        secondary_hex = color_parser(await fetch_color_representation(interaction, db, secondary_color))
        if secondary_hex is None:
            raise ValueError

    if primary_hex is None:
        raise ValueError

    if tertiary_hex is not None:
        return (int(primary_hex, 16), int(secondary_hex, 16), int(tertiary_hex, 16)), False

    primary_hex, secondary_hex, is_black = check_black(primary_hex, secondary_hex)
    return (int(primary_hex, 16), (int(secondary_hex, 16) if secondary_hex else None), None), is_black
