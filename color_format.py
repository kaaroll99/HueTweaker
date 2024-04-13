import re
import json
from colormath.color_objects import sRGBColor, CMYKColor, HSLColor
from colormath.color_conversions import convert_color
from PIL import Image

rgb = re.compile(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)")
hsl = re.compile(r"hsl\((\d+(\.\d+)?),\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")
cmyk = re.compile(r"cmyk\((\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")


def parse_rgb(input_color):
    match = rgb.match(input_color)
    if match:
        return (int(match.group(1)), int(match.group(2)), int(match.group(3)))
    return None


def parse_hsl(input_color):
    match = hsl.match(input_color)
    if match:
        return (float(match.group(1)), float(match.group(3)), float(match.group(5)))
    return None


def parse_cmyk(input_color):
    match = cmyk.match(input_color)
    if match:
        return (float(match.group(1)) / 100.0, float(match.group(3)) / 100.0, float(match.group(5)) / 100.0,
                float(match.group(7)) / 100.0)
    return None


def hsl_distance(hsl1, hsl2):
    return sum((x[0] - x[1]) ** 2 for x in zip(hsl1, hsl2))


def find_similar_colors(color, threshold=20):
    with open("assets/css-color-names.json", "r", encoding="utf-8") as file:
        color_dict = json.load(file)
    similar_colors = []

    for color_name, color_hex in color_dict.items():
        rgb_color = sRGBColor.new_from_rgb_hex(color_hex)
        compare_hsl = convert_color(rgb_color, HSLColor).get_value_tuple()
        distance = hsl_distance(color, compare_hsl)
        if distance <= threshold:
            similar_colors.append((color_name, distance))

    similar_colors.sort(key=lambda x: x[1])
    return [color[0] for color in similar_colors]


def color_converter(input_color, color_format):
    if color_format is None:
        return None

    try:
        if color_format == "hex":
            rgb_color = sRGBColor.new_from_rgb_hex(input_color)
        elif color_format == "rgb":
            rgb_values = parse_rgb(input_color)
            if rgb_values is None:
                raise ValueError("Invalid RGB format")
            rgb_color = sRGBColor(rgb_values[0] / 255.0, rgb_values[1] / 255.0, rgb_values[2] / 255.0)
        elif color_format == "hsl":
            hsl_values = parse_hsl(input_color)
            if hsl_values is None:
                raise ValueError("Invalid HSL format")
            rgb_color = convert_color(HSLColor(hsl_values[0], hsl_values[1] / 100.0, hsl_values[2] / 100.0), sRGBColor)
        elif color_format == "cmyk":
            cmyk_values = parse_cmyk(input_color)
            if cmyk_values is None:
                raise ValueError("Invalid CMYK format")
            rgb_color = convert_color(CMYKColor(cmyk_values[0], cmyk_values[1], cmyk_values[2], cmyk_values[3]),
                                      sRGBColor)

        hex_color = rgb_color.get_rgb_hex()
        rgb_values = rgb_color.get_value_tuple()
        hsl_color = convert_color(rgb_color, HSLColor).get_value_tuple()
        cmyk_color = convert_color(rgb_color, CMYKColor).get_value_tuple()
        similar_colors = find_similar_colors(hsl_color)

        result = {
            "Input": input_color,
            "Hex": hex_color,
            "RGB": rgb_values,
            "HSL": hsl_color,
            "CMYK": cmyk_color,
            "Similars": similar_colors
        }

        return result

    except ValueError as e:
        color_converter("ffffff", "hex")


def generate_image_from_rgb_float(rgb_float_color):
    image = Image.new("RGB", (300, 100))
    for x in range(300):
        for y in range(100):
            image.putpixel((x, y), tuple(int(val * 255) for val in rgb_float_color))
    return image
