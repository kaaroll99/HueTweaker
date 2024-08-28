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
        if re.sub(r"[^A-Za-z]", "", self.color.lower()) in map(lambda x: x.lower(), data.keys()):
            self.color = data[self.color]
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
            if self.color_format == "hex":
                rgb_color = sRGBColor.new_from_rgb_hex(self.color)
            elif self.color_format == "rgb":
                rgb_values = self.__parse_rgb()
                if rgb_values is None:
                    raise ValueError("Invalid RGB format")
                rgb_color = sRGBColor(*np.array(rgb_values) / 255.0)
            elif self.color_format == "hsl":
                hsl_values = self.__parse_hsl()
                if hsl_values is None:
                    raise ValueError("Invalid HSL format")
                rgb_color = convert_color(HSLColor(hsl_values[0], hsl_values[1] / 100.0, hsl_values[2] / 100.0), sRGBColor)
            elif self.color_format == "cmyk":
                cmyk_values = self.__parse_cmyk()
                if cmyk_values is None:
                    raise ValueError("Invalid CMYK format")
                rgb_color = convert_color(CMYKColor(*cmyk_values), sRGBColor)

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
        rgb_color = np.array(color) * 255
        rgb_color = rgb_color.astype(np.uint8)
        image_array = np.full((100, 300, 3), rgb_color, dtype=np.uint8)
        return Image.fromarray(image_array, 'RGB')

    def color_parser(self):
        data = load_json("assets/css-color-names.json")
        if re.sub(r"[^A-Za-z]", "", self.color.lower()) in map(lambda x: x.lower(), data.keys()):
            return data[self.color]
        elif hex_regex.match(self.color):
            self.color = self.color.lstrip("#")
            if len(self.color) == 3:
                return ''.join([x * 2 for x in color_match.strip("#")])
            return self.color.strip("#")
        else:
            return -1

    def __parse_rgb(self):
        match = self.rgb_pattern.match(self.color)
        if match:
            return np.array([int(match.group(1)), int(match.group(2)), int(match.group(3))])
        return None

    def __parse_hsl(self):
        match = self.hsl_pattern.match(self.color)
        if match:
            return np.array([float(match.group(1)), float(match.group(3)), float(match.group(5))])
        return None

    def __parse_cmyk(self):
        match = self.cmyk_pattern.match(self.color)
        if match:
            return np.array([float(match.group(i)) / 100.0 for i in (1, 3, 5, 7)])
        return None

    @staticmethod
    def __find_similar_colors(hsl_color, threshold=20):
        color_dict = load_json("assets/css-color-names.json")
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
