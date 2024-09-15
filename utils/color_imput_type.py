import discord


def color_type(interaction, color):
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
