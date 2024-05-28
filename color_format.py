import re
import json
from colormath.color_objects import sRGBColor, CMYKColor, HSLColor
from colormath.color_conversions import convert_color
from PIL import Image
from config import hex_regex

class ColorUtils:
    rgb_pattern = re.compile(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)")
    hsl_pattern = re.compile(r"hsl\((\d+(\.\d+)?),\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")
    cmyk_pattern = re.compile(r"cmyk\((\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")

    def __init__(self, color):
        self.color = color

    def color_converter(self, color_format):
        if color_format is None:
            return None
        try:
            if color_format == "hex":
                rgb_color = sRGBColor.new_from_rgb_hex(self.color)
            elif color_format == "rgb":
                rgb_values = self.__parse_rgb()
                if rgb_values is None:
                    raise ValueError("Invalid RGB format")
                rgb_color = sRGBColor(rgb_values[0] / 255.0, rgb_values[1] / 255.0, rgb_values[2] / 255.0)
            elif color_format == "hsl":
                hsl_values = self.__parse_hsl()
                if hsl_values is None:
                    raise ValueError("Invalid HSL format")
                rgb_color = convert_color(HSLColor(hsl_values[0], hsl_values[1] / 100.0, hsl_values[2] / 100.0), sRGBColor)
            elif color_format == "cmyk":
                cmyk_values = self.__parse_cmyk()
                if cmyk_values is None:
                    raise ValueError("Invalid CMYK format")
                rgb_color = convert_color(CMYKColor(cmyk_values[0], cmyk_values[1], cmyk_values[2], cmyk_values[3]), sRGBColor)

            hex_color = rgb_color.get_rgb_hex()
            rgb_values = rgb_color.get_value_tuple()
            hsl_color = convert_color(rgb_color, HSLColor).get_value_tuple()
            cmyk_color = convert_color(rgb_color, CMYKColor).get_value_tuple()
            similar_colors = self.__find_similar_colors(hsl_color)

            result = {
                "Input": self.color,
                "Hex": hex_color,
                "RGB": rgb_values,
                "HSL": hsl_color,
                "CMYK": cmyk_color,
                "Similars": similar_colors
            }

            return result

        except ValueError as e:
            self.color = "ffffff"
            return self.color_converter("hex")

    @staticmethod
    def generate_image_from_rgb_float(rgb_float_color):
        image = Image.new("RGB", (300, 100))
        for x in range(300):
            for y in range(100):
                image.putpixel((x, y), tuple(int(val * 255) for val in rgb_float_color))
        return image

    def color_parser(self):
        with open("assets/css-color-names.json", "r", encoding="utf-8") as file:
            data = json.load(file)
        color_match = self.color.lower().replace(" ", "")
        if color_match in map(lambda x: x.lower(), data.keys()):
            return data[color_match]
        elif hex_regex.match(color_match):
            if len(color_match.strip("#")) == 3:
                return ''.join([x * 2 for x in color_match.strip("#")])
            else:
                return color_match.strip("#")
        else:
            return -1

    def __parse_rgb(self):
        match = self.rgb_pattern.match(self.color)
        if match:
            return int(match.group(1)), int(match.group(2)), int(match.group(3))
        return None

    def __parse_hsl(self):
        match = self.hsl_pattern.match(self.color)
        if match:
            return float(match.group(1)), float(match.group(3)), float(match.group(5))
        return None

    def __parse_cmyk(self):
        match = self.cmyk_pattern.match(self.color)
        if match:
            return (float(match.group(1)) / 100.0, float(match.group(3)) / 100.0,
                    float(match.group(5)) / 100.0, float(match.group(7)) / 100.0)
        return None

    @staticmethod
    def __hsl_distance(hsl1, hsl2):
        return sum((x[0] - x[1]) ** 2 for x in zip(hsl1, hsl2))

    def __find_similar_colors(self, hsl_color, threshold=20):
        with open("assets/css-color-names.json", "r", encoding="utf-8") as file:
            color_dict = json.load(file)
        similar_colors = []

        for color_name, color_hex in color_dict.items():
            rgb_color = sRGBColor.new_from_rgb_hex(color_hex)
            compare_hsl = convert_color(rgb_color, HSLColor).get_value_tuple()
            distance = self.__hsl_distance(hsl_color, compare_hsl)
            if distance <= threshold:
                similar_colors.append((color_name, distance))

        similar_colors.sort(key=lambda x: x[1])
        return [color[0] for color in similar_colors]
