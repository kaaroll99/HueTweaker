import re
import json
from colormath.color_objects import sRGBColor, CMYKColor, HSLColor
from colormath.color_conversions import convert_color
from PIL import Image


def detect_color_format(input_color):
    hex_pattern = r"^(#?[0-9a-fA-F]{6})$"
    rgb_pattern = r"^rgb\((\d+),\s*(\d+),\s*(\d+)\)$"
    hsl_pattern = r"^hsl\((\d+(\.\d+)?),\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$"
    cmyk_pattern = r"^cmyk\((\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$"
    integer_pattern = r"^\d+$"

    if re.match(hex_pattern, input_color):
        return "hex"
    elif re.match(rgb_pattern, input_color):
        return "rgb"
    elif re.match(hsl_pattern, input_color):
        return "hsl"
    elif re.match(cmyk_pattern, input_color):
        return "cmyk"
    elif re.match(integer_pattern, input_color):
        return "integer"
    else:
        return None


def parse_rgb(input_color):
    match = re.match(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)", input_color)
    if match:
        r = int(match.group(1))
        g = int(match.group(2))
        b = int(match.group(3))
        return (r, g, b)
    return None


def parse_hsl(input_color):
    match = re.match(r"hsl\((\d+(\.\d+)?),\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$", input_color)
    if match:
        return (float(match.group(1)), float(match.group(3)), float(match.group(5)))
    return None


def parse_cmyk(input_color):
    match = re.match(r"cmyk\((\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$", input_color)
    if match:
        return (float(match.group(1)) / 100.0, float(match.group(3)) / 100.0, float(match.group(5)) / 100.0,
                float(match.group(7)) / 100.0)
    return None


def hsl_distance(hsl1, hsl2):
    return sum((x[0] - x[1]) ** 2 for x in zip(hsl1, hsl2))


def find_similar_colors(color, threshold=0.2):
    with open("assets/css-color-names.json", "r", encoding="utf-8") as file:
        color_dict = json.load(file)
    similar_colors = []

    for color_name, color_hex in color_dict.items():
        rgb_color = sRGBColor.new_from_rgb_hex(color_hex)
        compare_hsl = convert_color(rgb_color, HSLColor).get_value_tuple()
        distance = hsl_distance(color, compare_hsl)
        if distance <= threshold:
            similar_colors.append(color_name)

    return similar_colors


def color_converter(input_color):
    color_format = detect_color_format(input_color)

    if color_format is None:
        result = {"error": "Invalid color format"}
        return json.dumps(result)

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
        elif color_format == "integer":
            integer_value = int(input_color)
            r = (integer_value >> 16) & 0xFF
            g = (integer_value >> 8) & 0xFF
            b = integer_value & 0xFF
            rgb_color = sRGBColor(r / 255.0, g / 255.0, b / 255.0)

        hex_color = rgb_color.get_rgb_hex()
        rgb_values = rgb_color.get_value_tuple()
        hsl_color = convert_color(rgb_color, HSLColor).get_value_tuple()
        cmyk_color = convert_color(rgb_color, CMYKColor).get_value_tuple()
        integer_color = int("0x" + hex_color[1:], 16)
        similar_colors = find_similar_colors(hsl_color)

        result = {
            "Input": input_color,
            "Hex": hex_color,
            "RGB": rgb_values,
            "HSL": hsl_color,
            "CMYK": cmyk_color,
            "Integer": str(integer_color),
            "Similars": similar_colors
        }

        return result

    except ValueError as e:
        result = {
            "error": str(e)
        }
        return json.dumps(result)


def generate_image_from_rgb_float(rgb_float_color):
    image = Image.new("RGB", (300, 100))
    for x in range(300):
        for y in range(100):
            image.putpixel((x, y), tuple(int(val * 255) for val in rgb_float_color))
    return image
