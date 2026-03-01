import random
import re

import discord

from utils.color_format import ColorUtils, _load_css_color_cache

MAX_COLOR_INPUT_LEN = 32


def fetch_color_representation(interaction: discord.Interaction, color: str) -> str:
    """Resolve special color inputs (mentions, 'random') into raw color strings."""
    if len(color) > MAX_COLOR_INPUT_LEN:
        raise ValueError
    if color.startswith("<@") and color.endswith(">"):
        cleaned_color = re.sub(r"[<>@]", "", color)
        copy_role = discord.utils.get(interaction.guild.roles, name=f"color-{cleaned_color}")
        if copy_role is None:
            raise ValueError
        return str(copy_role.color)
    elif color == "random":
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    return color


def color_parser(color: str) -> str | None:
    """Parse any supported color format and return a 6-char hex string (no '#'), or None."""
    if len(color) > MAX_COLOR_INPUT_LEN:
        return None
    # Check CSS name first using the shared cache (no disk I/O)
    css_name = re.sub(r"[^A-Za-z]", "", color.lower())
    css_colors = _load_css_color_cache()
    if css_name in css_colors:
        return css_colors[css_name]
    # Fall back to full color conversion
    result = ColorUtils(color).color_converter()
    if result is not None:
        return result["Hex"].lstrip("#")
    return None


def check_black(primary_hex: str | None, secondary_hex: str | None) -> tuple[str | None, str | None, bool]:
    """Adjust pure black (#000000) to #000001 due to Discord treating 0 as 'no color'."""
    is_black = False
    if primary_hex == "000000":
        is_black = True
        primary_hex = "000001"
    if secondary_hex == "000000":
        is_black = True
        secondary_hex = "000001"
    return primary_hex, secondary_hex, is_black
