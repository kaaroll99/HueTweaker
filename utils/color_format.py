import re

import numpy as np
from PIL import Image
from colormath.color_conversions import convert_color
from colormath.color_objects import sRGBColor, CMYKColor, HSLColor

from config import hex_regex, rgb_regex, hsl_regex, cmyk_regex
from utils.data_loader import load_json


class ColorUtils:
    __slots__ = ['color', 'color_format']
    rgb_pattern = re.compile(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)")
    hsl_pattern = re.compile(r"hsl\((\d+(\.\d+)?),\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")
    cmyk_pattern = re.compile(r"cmyk\((\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")

    def __init__(self, color, color_format=None):
        self.color = color
        self.color_format = color_format

    def __determine_color_format(self):
        data = load_json("assets/css-color-names.json")
        self.color = re.sub(r"[^A-Za-z]", "", self.color.lower())
        if self.color in map(lambda x: x.lower(), data.keys()):
            self.color = data[self.color]
            self.color_format = "hex"
        elif hex_regex.match(self.color):
            if len(self.color.strip("#")) == 3:
                self.color = ''.join([x * 2 for x in self.color.strip("#")])
            else:
                self.color = self.color.strip("#")
                self.color_format = "hex"
        elif rgb_regex.match(self.color):
            self.color_format = "rgb"
        elif hsl_regex.match(self.color):
            self.color_format = "hsl"
        elif cmyk_regex.match(self.color):
            self.color_format = "cmyk"
        else:
            self.color_format = None

    def color_converter(self):
        self.__determine_color_format()
        if self.color_format is None:
            return None
        try:
            if self.color_format == "hex":
                rgb_color = sRGBColor.new_from_rgb_hex(self.color)
            elif self.color_format == "rgb":
                rgb_values = self.__parse_rgb()
                if rgb_values is None:
                    raise ValueError("Invalid RGB format")
                rgb_color = sRGBColor(rgb_values[0] / 255.0, rgb_values[1] / 255.0, rgb_values[2] / 255.0)
            elif self.color_format == "hsl":
                hsl_values = self.__parse_hsl()
                if hsl_values is None:
                    raise ValueError("Invalid HSL format")
                rgb_color = convert_color(HSLColor(hsl_values[0], hsl_values[1] / 100.0, hsl_values[2] / 100.0), sRGBColor)
            elif self.color_format == "cmyk":
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

        except ValueError:
            self.color = "ffffff"
            self.color_format = "hex"
            return self.color_converter()

    @staticmethod
    def generate_image(color):
        rgb_float_color = np.array([float(val) for val in color])
        image_array = np.tile(rgb_float_color, (100, 300, 1)) * 255
        return Image.fromarray(image_array.astype('uint8'), 'RGB')

    def color_parser(self):
        data = load_json("assets/css-color-names.json")
        color_match = re.sub(r"[^A-Za-z]", "", self.color.lower())
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
        color_dict = load_json("assets/css-color-names.json")
        similar_colors = []

        for color_name, color_hex in color_dict.items():
            rgb_color = sRGBColor.new_from_rgb_hex(color_hex)
            compare_hsl = convert_color(rgb_color, HSLColor).get_value_tuple()
            distance = self.__hsl_distance(hsl_color, compare_hsl)
            if distance <= threshold:
                similar_colors.append((color_name, distance))

        similar_colors.sort(key=lambda x: x[1])
        return [color[0] for color in similar_colors]
