import random
import re

import discord

from utils.data_loader import load_json
from utils.color_format import hex_regex


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
    elif hex_regex.match(color):
        color = color.lstrip("#")
        if len(color) == 3:
            return ''.join([x * 2 for x in color.strip("#")])
        return color.strip("#")
    else:
        raise ValueError