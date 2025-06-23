import random
import re

import discord

from utils.data_loader import load_json
from utils.color_format import hex_regex, rgb_regex, ColorUtils


def fetch_color_representation(interaction, color):
    if color.startswith("<@") and color.endswith(">"):
        cleaned_color = re.sub(r"[<>@]", "", color)
        copy_role = discord.utils.get(interaction.guild.roles, name=f"color-{cleaned_color}")
        if copy_role is None:
            raise ValueError
        else:
            return str(copy_role.color)
    elif color == "random":
        return "#{:06x}".format(random.randint(0, 0xFFFFFF))
    else:
        return color


def color_parser(color):
    data = load_json("assets/css-color-names.json")
    css_name = re.sub(r"[^A-Za-z]", "", color.lower())
    if css_name in map(lambda x: x.lower(), data.keys()):
        return data[css_name]
    else:
        color_utils = ColorUtils(color)
        result = color_utils.color_converter()
        if result is not None:
            return result["Hex"].lstrip("#")
        else:
            raise ValueError