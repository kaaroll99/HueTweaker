import re
from functools import lru_cache

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from colormath.color_conversions import convert_color
from colormath.color_objects import sRGBColor, CMYKColor, HSLColor

from utils.data_loader import load_json

rgb_pattern = re.compile(r"rgb\((\d+),\s*(\d+),\s*(\d+)\)")
hsl_pattern = re.compile(r"hsl\((\d+(\.\d+)?),\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")
cmyk_pattern = re.compile(r"cmyk\((\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%,\s*(\d+(\.\d+)?)%\)$")

hex_regex = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
rgb_regex = re.compile(r"^rgb\((25[0-5]|2[0-4]\d|[01]?\d{1,2})\s*,\s*(25[0-5]|2[0-4]\d|[01]?\d{1,2})\s*,\s*(25[0-5]|2[0-4]\d|[01]?\d{1,2})\)$")
hsl_regex = re.compile(r"^hsl\((\d+(\.\d+)?|100(\.0+)?),\s*(\d+(\.\d+)?|100(\.0+)?)%\s*,\s*(\d+(\.\d+)?|100(\.0+)?)%\)$")
cmyk_regex = re.compile(r"^cmyk\((100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%,\s*(100(\.0+)?|\d+(\.\d+)?)%\)$")


@lru_cache(maxsize=1)
def _load_css_color_cache():
    data = load_json("assets/css-color-names.json")
    lowered = {name.lower(): value for name, value in data.items()}
    return lowered


class ColorUtils:
    __slots__ = ['color', 'color_format', 'find_similar_colors']

    def __init__(self, color, color_format=None, find_similar_colors=False):
        self.color = color
        self.color_format = color_format
        self.find_similar_colors = find_similar_colors

    def __determine_color_format(self):
        self.color = self.color.strip()
        lowered = _load_css_color_cache()
        css_name = re.sub(r"[^A-Za-z]", "", self.color.lower())
        if css_name in lowered:
            self.color = lowered[css_name]
            self.color_format = "hex"
        elif hex_regex.match(self.color):
            self.color = self.color.lstrip("#")
            if len(self.color) == 3:
                self.color = ''.join([x * 2 for x in self.color])
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
            rgb_color = None
            if self.color_format == "hex":
                rgb_color = sRGBColor.new_from_rgb_hex(self.color)
            elif self.color_format == "rgb":
                rgb_values = self.__parse_rgb()
                rgb_color = sRGBColor(*np.array(rgb_values) / 255.0)
            elif self.color_format == "hsl":
                hsl_values = self.__parse_hsl()
                rgb_color = convert_color(HSLColor(hsl_values[0], hsl_values[1] / 100.0, hsl_values[2] / 100.0),
                                          sRGBColor)
            elif self.color_format == "cmyk":
                cmyk_values = self.__parse_cmyk()
                rgb_color = convert_color(CMYKColor(*cmyk_values), sRGBColor)

            hex_color = rgb_color.get_rgb_hex()
            rgb_values = rgb_color.get_value_tuple()
            hsl_color = convert_color(rgb_color, HSLColor).get_value_tuple()
            cmyk_color = convert_color(rgb_color, CMYKColor).get_value_tuple()
            similar_colors = self.__find_similar_colors(hsl_color) if self.find_similar_colors else []

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

    def __parse_rgb(self):
        match = rgb_pattern.match(self.color)
        if match:
            return np.array([int(match.group(1)), int(match.group(2)), int(match.group(3))])
        raise ValueError

    def __parse_hsl(self):
        match = hsl_pattern.match(self.color)
        if match:
            return np.array([float(match.group(1)), float(match.group(3)), float(match.group(5))])
        raise ValueError

    def __parse_cmyk(self):
        match = cmyk_pattern.match(self.color)
        if match:
            return np.array([float(match.group(i)) / 100.0 for i in (1, 3, 5, 7)])
        raise ValueError

    @staticmethod
    def generate_image(color):
        rgb_color = np.array(color) * 255
        rgb_color = rgb_color.astype(np.uint8)
        image_array = np.full((50, 300, 3), rgb_color, dtype=np.uint8)
        return Image.fromarray(image_array, 'RGB')

    @staticmethod
    def generate_colored_text_grid(text, hex_colors):
        try:
            font = ImageFont.truetype("assets/gg_sans_mid.ttf", 18)
        except IOError:
            font = ImageFont.load_default()

        padding = 10
        line_height = 30
        height = (len(hex_colors) * line_height) + padding * 2
        width = 400

        image = Image.new('RGBA', (width, height), (50, 51, 57, 255))
        draw = ImageDraw.Draw(image)

        for i, hex_color in enumerate(hex_colors):
            hex_color = hex_color.lstrip('#')

            r = int(hex_color[0:2], 16)
            g = int(hex_color[2:4], 16)
            b = int(hex_color[4:6], 16)

            numbered_text = f"{i + 1}. {text}"

            draw.text(
                (padding * 1.5, padding + i * line_height),
                numbered_text,
                fill=(r, g, b, 255),
                font=font
            )
        return image

    @staticmethod
    def __find_similar_colors(hsl_color, threshold=20):
        color_dict = _load_css_color_cache()
        similar_colors = []
        hsl_color_np = np.array(hsl_color)

        for color_name, color_hex in color_dict.items():
            rgb_color = sRGBColor.new_from_rgb_hex(color_hex)
            compare_hsl = np.array(convert_color(rgb_color, HSLColor).get_value_tuple())
            distance = np.sum((hsl_color_np - compare_hsl) ** 2)
            if distance <= threshold:
                similar_colors.append((color_name, distance))

        similar_colors.sort(key=lambda x: x[1])
        return [color[0] for color in similar_colors]
