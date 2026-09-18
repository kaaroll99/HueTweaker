import re
from functools import lru_cache
from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from colormath.color_conversions import convert_color
from colormath.color_objects import sRGBColor, CMYKColor, HSLColor, LabColor

from utils.data_loader import load_json

# One regex per notation, used both for validation and for extracting the numbers.
# Value ranges are checked numerically afterwards (see ``_in_range``).
_NUM = r"(\d+(?:\.\d+)?)"
hex_regex = re.compile(r"^#?([0-9a-fA-F]{3}|[0-9a-fA-F]{6})$")
rgb_regex = re.compile(rf"^rgb\(\s*{_NUM}\s*,\s*{_NUM}\s*,\s*{_NUM}\s*\)$")
hsl_regex = re.compile(rf"^hsl\(\s*{_NUM}\s*,\s*{_NUM}%\s*,\s*{_NUM}%\s*\)$")
cmyk_regex = re.compile(rf"^cmyk\(\s*{_NUM}%\s*,\s*{_NUM}%\s*,\s*{_NUM}%\s*,\s*{_NUM}%\s*\)$")

# Colors closer than this (CIE76 distance in Lab) count as "similar" for /check.
SIMILAR_COLOR_THRESHOLD = 30.0


@lru_cache(maxsize=1)
def _load_css_color_cache() -> dict[str, str]:
    data = load_json("assets/css-color-names.json")
    return {name.lower(): value.lower() for name, value in data.items()}


@lru_cache(maxsize=1)
def _load_css_name_by_hex() -> dict[str, str]:
    reverse: dict[str, str] = {}
    for name, hex_val in _load_css_color_cache().items():
        reverse.setdefault(hex_val.lower(), name)
    return reverse


@lru_cache(maxsize=1)
def _load_css_lab_cache() -> dict[str, np.ndarray]:
    result = {}
    for name, hex_val in _load_css_color_cache().items():
        lab = convert_color(sRGBColor.new_from_rgb_hex(hex_val), LabColor)
        result[name] = np.array(lab.get_value_tuple())
    return result


@lru_cache(maxsize=1)
def _get_font(size: int = 18) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    try:
        return ImageFont.truetype("assets/gg_sans_mid.ttf", size)
    except IOError:
        return ImageFont.load_default()


def _int_to_rgb(color_int: int) -> tuple[int, int, int]:
    return (color_int >> 16) & 255, (color_int >> 8) & 255, color_int & 255


def css_name_key(text: str) -> str:
    """Normalize user input for a CSS name lookup: ``"Royal Blue"`` -> ``"royalblue"``."""
    return re.sub(r"[\s_-]", "", text.strip().lower())


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


def format_colors_label(primary: int, secondary: int | None = None) -> str:
    """Label for a solid color or a ``primary + secondary`` gradient."""
    if secondary is None:
        return format_color_label(primary)
    return f"{format_color_label(primary)} + {format_color_label(secondary)}"


def _in_range(values, limits) -> bool:
    return all(0.0 <= v <= hi for v, hi in zip(values, limits))


class ColorUtils:
    __slots__ = ['color', 'color_format', 'find_similar_colors', '_values']

    def __init__(self, color, color_format=None, find_similar_colors=False):
        self.color = color
        self.color_format = color_format
        self.find_similar_colors = find_similar_colors
        self._values: tuple[float, ...] = ()

    def __determine_color_format(self):
        """Detect the notation and extract its numbers. Invalid or out-of-range input -> ``None``."""
        self.color = self.color.strip()
        self.color_format = None
        self._values = ()

        css_name = css_name_key(self.color)
        css_colors = _load_css_color_cache()
        if css_name in css_colors:
            self.color = css_colors[css_name]
            self.color_format = "hex"
            return

        if match := hex_regex.match(self.color):
            value = match.group(1).lower()
            if len(value) == 3:
                value = ''.join(ch * 2 for ch in value)
            self.color = value
            self.color_format = "hex"
            return

        for fmt, regex, limits in (
            ("rgb", rgb_regex, (255, 255, 255)),
            ("hsl", hsl_regex, (360, 100, 100)),
            ("cmyk", cmyk_regex, (100, 100, 100, 100)),
        ):
            match = regex.match(self.color)
            if match:
                values = tuple(float(v) for v in match.groups())
                if _in_range(values, limits):
                    self.color_format = fmt
                    self._values = values
                return

    def color_converter(self):
        self.__determine_color_format()
        if self.color_format is None:
            return None
        try:
            if self.color_format == "hex":
                rgb_color = sRGBColor.new_from_rgb_hex(self.color)
            elif self.color_format == "rgb":
                rgb_color = sRGBColor(*(np.array(self._values) / 255.0))
            elif self.color_format == "hsl":
                hue, sat, light = self._values
                rgb_color = convert_color(HSLColor(hue % 360, sat / 100.0, light / 100.0), sRGBColor)
            else:
                rgb_color = convert_color(CMYKColor(*(np.array(self._values) / 100.0)), sRGBColor)

            # Clamp so conversions from HSL/CMYK never produce components outside 0..1.
            rgb_color = sRGBColor(*(min(1.0, max(0.0, c)) for c in rgb_color.get_value_tuple()))

            hex_color = rgb_color.get_rgb_hex()
            rgb_values = rgb_color.get_value_tuple()
            hsl_color = convert_color(rgb_color, HSLColor).get_value_tuple()
            cmyk_color = convert_color(rgb_color, CMYKColor).get_value_tuple()
            similar_colors = self.__find_similar_colors(rgb_color) if self.find_similar_colors else []

            return {
                "Input": self.color,
                "Hex": hex_color,
                "RGB": rgb_values,
                "HSL": hsl_color,
                "CMYK": cmyk_color,
                "Similars": similar_colors,
            }
        except (ValueError, TypeError):
            return None

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
        """Render a numbered list where each line is ``{i}. {nick} {label}`` drawn in its own
        color. ``colors`` may be ints, hex strings, or ``(primary, secondary)`` tuples."""
        font = _get_font()

        padding = 10
        line_height = 30

        lines, fills = [], []
        for i, color in enumerate(colors):
            secondary = None
            if isinstance(color, tuple):
                color, secondary = color
            color_int = color if isinstance(color, int) else int(str(color).lstrip('#'), 16)
            lines.append(f"{i + 1}. {nick} {format_colors_label(color_int, secondary)}")
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
    def __find_similar_colors(rgb_color: sRGBColor, threshold: float = SIMILAR_COLOR_THRESHOLD):
        """CSS colors sorted by perceptual distance (CIE76 in Lab), closest first."""
        target = np.array(convert_color(rgb_color, LabColor).get_value_tuple())
        similar_colors = []
        for color_name, lab in _load_css_lab_cache().items():
            distance = float(np.linalg.norm(target - lab))
            if distance <= threshold:
                similar_colors.append((color_name, distance))
        similar_colors.sort(key=lambda x: x[1])
        return [color[0] for color in similar_colors]
