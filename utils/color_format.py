"""Color notations and conversions, user-facing labels, style encoding and generated images."""

import re
from functools import lru_cache
from io import BytesIO

import numpy as np
from PIL import Image, ImageDraw, ImageFont
from colormath.color_conversions import convert_color
from colormath.color_objects import sRGBColor, CMYKColor, HSLColor, LabColor

from constants import HOLOGRAPHIC_COLORS
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


_BOOK_BACKGROUND = (50, 51, 57, 255)
_BOOK_TEXT = (219, 222, 225)
_BOOK_MUTED_TEXT = (148, 155, 164)
_MIN_READABLE_CONTRAST = 2.0


def _relative_luminance(rgb: tuple[int, int, int]) -> float:
    """Return the WCAG relative luminance of an 8-bit sRGB color."""
    def channel(value: int) -> float:
        c = value / 255
        return c / 12.92 if c <= 0.03928 else ((c + 0.055) / 1.055) ** 2.4
    r, g, b = (channel(v) for v in rgb)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def _contrast_ratio(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    """Return the WCAG contrast ratio of two colors, from 1 (same) to 21 (black on white)."""
    la, lb = sorted((_relative_luminance(a), _relative_luminance(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def css_name_key(text: str) -> str:
    """Normalize user input for a CSS name lookup: ``"Royal Blue"`` -> ``"royalblue"``."""
    return re.sub(r"[\s_-]", "", text.strip().lower())


def name_and_hex(color: int | str) -> tuple[str, str]:
    """Return ``(label, "#RRGGBB")``; the label is the CSS name when one matches, else the HEX."""
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


HOLOGRAPHIC_NAME = "Holographic"

Colors = tuple[int, int | None, int | None]


@lru_cache(maxsize=1)
def color_presets() -> dict[str, tuple[str, Colors]]:
    """Return the named presets as ``{css_name_key(name): (name, colors)}``, holographic included.

    Raises ``ValueError`` when a preset name collides with a CSS name, a HEX code or ``random``.
    """
    presets = {
        css_name_key(name): (name, (int(primary, 16), int(secondary, 16), None))
        for name, (primary, secondary) in load_json("assets/gradient-presets.json").items()
    }
    presets[css_name_key(HOLOGRAPHIC_NAME)] = (HOLOGRAPHIC_NAME, HOLOGRAPHIC_COLORS)
    # A preset is looked up before colors, so a name that is also a color would silently replace it.
    for key, (name, _) in presets.items():
        if key == "random" or key in _load_css_color_cache() or hex_regex.match(key):
            raise ValueError(f"Preset name {name!r} collides with a color name, HEX code or 'random'")
    return presets


def preset_colors(text: str) -> Colors | None:
    preset = color_presets().get(css_name_key(text))
    return preset[1] if preset else None


_stored_hex_re = re.compile(r"^#?[0-9a-fA-F]{6}$")


def encode_style(colors: Colors) -> str:
    """Encode a style for the palette and favorites columns: ``rrggbb``, ``rrggbb+rrggbb`` or three parts."""
    return "+".join(f"{c:06x}" for c in colors if c is not None)


def decode_style(text: str | None) -> Colors | None:
    """Decode ``encode_style`` text, including older ``#RRGGBB`` values.

    Return None for empty or malformed text, so a bad slot is skipped instead of failing.
    """
    if not isinstance(text, str) or not text.strip():
        return None
    parts = text.strip().split("+")
    if len(parts) > 3 or not all(_stored_hex_re.match(part) for part in parts):
        return None
    values = [int(part.lstrip("#"), 16) for part in parts]
    return values[0], (values[1] if len(values) > 1 else None), (values[2] if len(values) > 2 else None)


def preset_name(colors: Colors) -> str | None:
    return next((name for name, value in color_presets().values() if value == colors), None)


def format_colors_label(primary: int, secondary: int | None = None, tertiary: int | None = None) -> str:
    """Return the label of a solid color, a ``primary + secondary`` gradient or the holographic style."""
    if tertiary is not None:
        return HOLOGRAPHIC_NAME
    if secondary is None:
        return format_color_label(primary)
    pair = f"{format_color_label(primary)} + {format_color_label(secondary)}"
    name = preset_name((primary, secondary, None))
    return f"{name} ({pair})" if name else pair


def _color_stops(primary: int, secondary: int | None = None, tertiary: int | None = None) -> list[tuple[int, int, int]]:
    return [_int_to_rgb(c) for c in (primary, secondary, tertiary) if c is not None]


def _paint_text(image: Image.Image, xy: tuple[float, float], text: str, font, stops: list[tuple[int, int, int]]) -> None:
    """Draw ``text`` filled with a horizontal gradient through ``stops``; one stop draws it solid."""
    if len(stops) == 1:
        ImageDraw.Draw(image).text(xy, text, fill=(*stops[0], 255), font=font)
        return

    mask = Image.new('L', image.size, 0)
    ImageDraw.Draw(mask).text(xy, text, font=font, fill=255)
    bbox = mask.getbbox()
    if bbox is None:
        return

    left, right = bbox[0], bbox[2]
    span = max(1, right - left)
    stops_arr = np.array(stops, dtype=float)
    position = np.linspace(0, len(stops) - 1, span)
    index = np.minimum(position.astype(int), len(stops) - 2)
    fraction = (position - index)[:, None]
    row = stops_arr[index] * (1 - fraction) + stops_arr[index + 1] * fraction

    fill = np.zeros((image.height, image.width, 3), dtype=np.uint8)
    fill[:, :left] = stops_arr[0]
    fill[:, left:left + span] = row.astype(np.uint8)[:image.width - left]
    fill[:, left + span:] = stops_arr[-1]
    image.paste(Image.fromarray(fill, 'RGB'), (0, 0), mask)


def dominant_colors(image_bytes: bytes, count: int = 5, min_distance: float = 20.0) -> list[int]:
    """Return up to ``count`` dominant colors of an image, most common first.

    Transparent pixels are ignored. Colors unreadable on Discord's dark theme are skipped, and so
    are colors closer than ``min_distance`` (in Lab) to one already picked.
    """
    with Image.open(BytesIO(image_bytes)) as source:
        image = source.convert('RGBA')
    image.thumbnail((64, 64))
    pixels = [pixel[:3] for pixel in image.getdata() if pixel[3] >= 128]
    if not pixels:
        return []

    strip = Image.new('RGB', (len(pixels), 1))
    strip.putdata(pixels)
    quantized = strip.quantize(colors=16, method=Image.Quantize.MEDIANCUT)
    palette = quantized.getpalette()

    picked: list[int] = []
    picked_lab: list[np.ndarray] = []
    for _, index in sorted(quantized.getcolors(), reverse=True):
        rgb = tuple(palette[index * 3:index * 3 + 3])
        if _contrast_ratio(rgb, _BOOK_BACKGROUND[:3]) < _MIN_READABLE_CONTRAST:
            continue
        lab = np.array(convert_color(sRGBColor(*rgb, is_upscaled=True), LabColor).get_value_tuple())
        if any(np.linalg.norm(lab - other) < min_distance for other in picked_lab):
            continue
        picked.append((rgb[0] << 16) | (rgb[1] << 8) | rgb[2])
        picked_lab.append(lab)
        if len(picked) == count:
            break
    return picked


def _in_range(values, limits) -> bool:
    return all(0.0 <= v <= hi for v, hi in zip(values, limits))


class ColorUtils:
    """Parse a color in any supported notation, convert it and render color images."""

    __slots__ = ['color', 'color_format', 'find_similar_colors', '_values']

    def __init__(self, color, color_format=None, find_similar_colors=False):
        self.color = color
        self.color_format = color_format
        self.find_similar_colors = find_similar_colors
        self._values: tuple[float, ...] = ()

    def __determine_color_format(self):
        """Detect the notation and extract its numbers.

        CSS names and HEX are normalized to six hex digits in ``color``; invalid or out-of-range
        input leaves ``color_format`` as None.
        """
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
        """Return the color in every notation, or None for invalid input.

        The keys are ``Input``, ``Hex``, ``RGB``, ``HSL``, ``CMYK`` and ``Similars`` (CSS names,
        filled only with ``find_similar_colors``). Values are colormath tuples: RGB, saturation,
        lightness and CMYK are 0..1 floats, hue is in degrees.
        """
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
        """Return a 300x50 swatch of an RGB color given as 0..1 floats."""
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
        """Render a numbered list where each line is ``{i}. {nick} {label}`` drawn in its own color.

        ``colors`` may be ints, hex strings or ``(primary, secondary[, tertiary])`` tuples.
        """
        font = _get_font()

        padding = 10
        line_height = 30

        lines, stops = [], []
        for i, color in enumerate(colors):
            parts = color if isinstance(color, tuple) else (color,)
            primary = parts[0] if isinstance(parts[0], int) else int(str(parts[0]).lstrip('#'), 16)
            rest = tuple(parts[1:]) + (None,) * (3 - len(parts))
            lines.append(f"{i + 1}. {nick} {format_colors_label(primary, *rest)}")
            stops.append(_color_stops(primary, *rest))

        height = (len(colors) * line_height) + padding * 2
        measure = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        max_text = max((measure.textlength(line, font=font) for line in lines), default=0)
        width = max(400, int(max_text + padding * 3))

        image = Image.new('RGBA', (width, height), (50, 51, 57, 255))
        for i, (line, line_stops) in enumerate(zip(lines, stops)):
            _paint_text(image, (padding * 1.5, padding + i * line_height), line, font, line_stops)
        return image

    @staticmethod
    def generate_color_book_image(names):
        """Render CSS color names with swatches and HEX codes, in two columns above 12 names."""
        font = _get_font()
        css = _load_css_color_cache()

        padding, line_height, swatch, gap = 14, 32, 22, 10
        rows = [(name, css[name.lower()].lstrip('#').upper()) for name in names]
        columns = 1 if len(rows) <= 12 else 2
        per_column = -(-len(rows) // columns)

        measure = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        name_width = max((measure.textlength(name, font=font) for name, _ in rows), default=0)
        hex_width = measure.textlength("#DDDDDD", font=font)
        column_width = int(swatch + gap + name_width + gap * 2 + hex_width + padding * 2)

        width = padding + columns * column_width
        height = padding * 2 + per_column * line_height
        image = Image.new('RGBA', (width, height), _BOOK_BACKGROUND)
        draw = ImageDraw.Draw(image)

        for i, (name, hex_value) in enumerate(rows):
            x = padding + (i // per_column) * column_width
            y = padding + (i % per_column) * line_height
            fill = _int_to_rgb(int(hex_value, 16))

            draw.rounded_rectangle((x, y + 2, x + swatch, y + 2 + swatch), radius=5, fill=fill,
                                   outline=_BOOK_MUTED_TEXT, width=1)
            readable = _contrast_ratio(fill, _BOOK_BACKGROUND[:3]) >= _MIN_READABLE_CONTRAST
            draw.text((x + swatch + gap, y + 2), name, fill=fill if readable else _BOOK_TEXT, font=font)
            draw.text((x + swatch + gap + name_width + gap * 2, y + 2), f"#{hex_value}",
                      fill=_BOOK_MUTED_TEXT, font=font)
        return image

    @staticmethod
    def generate_preset_book_image():
        font = _get_font()
        padding, line_height, gap = 14, 32, 24

        rows = []
        for name, colors in color_presets().values():
            codes = " → ".join(f"#{c:06X}" for c in colors if c is not None)
            rows.append((name, codes, _color_stops(*colors)))

        measure = ImageDraw.Draw(Image.new('RGBA', (1, 1)))
        name_width = max(measure.textlength(name, font=font) for name, _, _ in rows)
        codes_width = max(measure.textlength(codes, font=font) for _, codes, _ in rows)
        width = int(padding * 2 + name_width + gap + codes_width)
        height = padding * 2 + len(rows) * line_height

        image = Image.new('RGBA', (width, height), _BOOK_BACKGROUND)
        draw = ImageDraw.Draw(image)
        for i, (name, codes, stops) in enumerate(rows):
            y = padding + i * line_height + 2
            _paint_text(image, (padding, y), name, font, stops)
            draw.text((padding + name_width + gap, y), codes, fill=_BOOK_MUTED_TEXT, font=font)
        return image

    @staticmethod
    def generate_preview_image(text, color_int, secondary_color_int=None, tertiary_color_int=None):
        font = _get_font()

        padding = 10
        line_height = 30
        image = Image.new('RGBA', (400, line_height + padding * 2), (50, 51, 57, 255))
        _paint_text(image, (padding * 1.5, padding), text, font,
                    _color_stops(color_int, secondary_color_int, tertiary_color_int))
        return image

    @staticmethod
    def __find_similar_colors(rgb_color: sRGBColor, threshold: float = SIMILAR_COLOR_THRESHOLD):
        """Return the CSS color names within ``threshold`` (CIE76 distance in Lab), closest first."""
        target = np.array(convert_color(rgb_color, LabColor).get_value_tuple())
        similar_colors = []
        for color_name, lab in _load_css_lab_cache().items():
            distance = float(np.linalg.norm(target - lab))
            if distance <= threshold:
                similar_colors.append((color_name, distance))
        similar_colors.sort(key=lambda x: x[1])
        return [color[0] for color in similar_colors]
