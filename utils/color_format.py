import re
from functools import lru_cache
from io import BytesIO

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
def _load_css_color_cache() -> dict[str, str]:
    data = load_json("assets/css-color-names.json")
    return {name.lower(): value for name, value in data.items()}


@lru_cache(maxsize=1)
def _load_css_name_by_hex() -> dict[str, str]:
    reverse: dict[str, str] = {}
    for name, hex_val in _load_css_color_cache().items():
        reverse.setdefault(hex_val.lower(), name)
    return reverse


@lru_cache(maxsize=1)
def _load_css_hsl_cache() -> dict[str, np.ndarray]:
    color_dict = _load_css_color_cache()
    result = {}
    for name, hex_val in color_dict.items():
        rgb_color = sRGBColor.new_from_rgb_hex(hex_val)
        hsl = np.array(convert_color(rgb_color, HSLColor).get_value_tuple())
        result[name] = hsl
    return result


@lru_cache(maxsize=1)
def _get_font(size: int = 18) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("assets/gg_sans_mid.ttf", size)
    except IOError:
        return ImageFont.load_default()


def _int_to_rgb(color_int: int) -> tuple[int, int, int]:
    return (color_int >> 16) & 255, (color_int >> 8) & 255, color_int & 255


def name_and_hex(color: int | str) -> tuple[str, str]:
    if isinstance(color, int):
        hex_value = f"{color:06x}"
    else:
        hex_value = color.strip().lstrip("#").lower()
        if len(hex_value) == 3:
            hex_value = "".join(ch * 2 for ch in hex_value)

    formatted_hex = f"#{hex_value.upper()}"
    name = _load_css_name_by_hex().get(hex_value)
    if name is not None:
        return name, formatted_hex
    return formatted_hex, formatted_hex


def format_color_label(color: int | str) -> str:
    """Format a color as ``name (#HEX)`` when it matches a CSS color name, else ``#HEX``."""
    label, formatted_hex = name_and_hex(color)
    return formatted_hex if label == formatted_hex else f"{label} ({formatted_hex})"


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
    def to_bytes(image: Image.Image) -> BytesIO:
        buf = BytesIO()
        image.save(buf, format='PNG')
        buf.seek(0)
        return buf

    @staticmethod
    def generate_color_list_image(nick, colors):
        """Render a numbered grid where each line is ``{i}. {nick} {name (#HEX)|#HEX}``
        drawn in its own color. ``colors`` may be ints or hex strings."""
        font = _get_font()

        padding = 10
        line_height = 30

        lines, fills = [], []
        for i, color in enumerate(colors):
            color_int = color if isinstance(color, int) else int(str(color).lstrip('#'), 16)
            lines.append(f"{i + 1}. {nick} {format_color_label(color)}")
            fills.append(_int_to_rgb(color_int))

        height = (len(colors) * line_height) + padding * 2
        measure = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        max_text = max((measure.textlength(line, font=font) for line in lines), default=0)
        width = max(400, int(max_text + padding * 3))

        image = Image.new('RGBA', (width, height), (50, 51, 57, 255))
        draw = ImageDraw.Draw(image)

        for i, (line, fill) in enumerate(zip(lines, fills)):
            draw.text(
                (padding * 1.5, padding + i * line_height),
                line,
                fill=(*fill, 255),
                font=font,
            )
        return image

    @staticmethod
    def generate_preview_image(text, color_int, secondary_color_int=None):
        font = _get_font()

        padding = 10
        line_height = 30
        height = line_height + padding * 2
        width = 400

        image = Image.new('RGBA', (width, height), (50, 51, 57, 255))

        if secondary_color_int is None:
            draw = ImageDraw.Draw(image)
            r, g, b = _int_to_rgb(color_int)

            draw.text(
                (padding * 1.5, padding),
                text,
                fill=(r, g, b, 255),
                font=font,
            )
        else:
            mask = Image.new('L', (width, height), 0)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.text((padding * 1.5, padding), text, font=font, fill=255)

            bbox = mask.getbbox()
            if bbox:
                text_start = bbox[0]
                text_end = bbox[2]
                text_width = text_end - text_start
            else:
                text_start = 0
                text_end = width
                text_width = 0

            c1 = np.array(_int_to_rgb(color_int))
            c2 = np.array(_int_to_rgb(secondary_color_int))

            gradient_arr = np.zeros((height, width, 3), dtype=np.uint8)

            if text_width > 0:
                steps = text_end - text_start
                gradient_row = np.linspace(c1, c2, steps, dtype=np.uint8)

                gradient_arr[:, :text_start] = c1
                gradient_arr[:, text_start:text_end] = gradient_row
                gradient_arr[:, text_end:] = c2
            else:
                gradient_arr[:, :] = c1

            gradient_img = Image.fromarray(gradient_arr, 'RGB')
            image.paste(gradient_img, (0, 0), mask)

        return image

    @staticmethod
    def __find_similar_colors(hsl_color, threshold=20):
        hsl_cache = _load_css_hsl_cache()
        hsl_color_np = np.array(hsl_color)
        similar_colors = []

        for color_name, compare_hsl in hsl_cache.items():
            distance = np.sum((hsl_color_np - compare_hsl) ** 2)
            if distance <= threshold:
                similar_colors.append((color_name, distance))

        similar_colors.sort(key=lambda x: x[1])
        return [color[0] for color in similar_colors]
