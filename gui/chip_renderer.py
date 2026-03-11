"""
Generates casino chip images with ₹ denominations using Pillow.
No external assets required.
"""

from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import functools
import math

CHIP_SIZE = 64
CHIP_DENOMINATIONS = {
    1:   {"fill": "#f5f5dc", "edge": "#c8b896", "text": "#555555", "stripe": "#d4c4a0"},
    10:  {"fill": "#e8e8e8", "edge": "#cccccc", "text": "#333333", "stripe": "#aaaaaa"},
    50:  {"fill": "#e53935", "edge": "#b71c1c", "text": "#ffffff", "stripe": "#ef5350"},
    100: {"fill": "#2e7d32", "edge": "#1b5e20", "text": "#ffffff", "stripe": "#43a047"},
    300: {"fill": "#1565c0", "edge": "#0d47a1", "text": "#ffffff", "stripe": "#1e88e5"},
    500: {"fill": "#212121", "edge": "#000000", "text": "#ffd700", "stripe": "#424242"},
}


def _get_font(size: int):
    try:
        return ImageFont.truetype("arial.ttf", size)
    except OSError:
        try:
            return ImageFont.truetype("DejaVuSans-Bold.ttf", size)
        except OSError:
            return ImageFont.load_default()


@functools.lru_cache(maxsize=16)
def render_chip(denomination: int) -> bytes:
    """Render a single chip and return PNG bytes."""
    style = CHIP_DENOMINATIONS.get(denomination, CHIP_DENOMINATIONS[10])
    size = CHIP_SIZE
    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    r = size // 2 - 2

    # Drop shadow
    draw.ellipse([cx - r + 2, cy - r + 2, cx + r + 2, cy + r + 2],
                 fill=(0, 0, 0, 60))

    # Outer edge ring
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=style["edge"])

    # Main chip body
    inner_r = r - 3
    draw.ellipse([cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
                 fill=style["fill"])

    # Edge stripes (8 evenly spaced notches)
    for i in range(8):
        angle = i * (360 / 8)
        rad = math.radians(angle)
        x1 = cx + math.cos(rad) * (r - 6)
        y1 = cy + math.sin(rad) * (r - 6)
        x2 = cx + math.cos(rad) * (r - 1)
        y2 = cy + math.sin(rad) * (r - 1)
        draw.line([(x1, y1), (x2, y2)], fill=style["stripe"], width=3)

    # Inner circle decoration
    decor_r = inner_r - 8
    draw.ellipse([cx - decor_r, cy - decor_r, cx + decor_r, cy + decor_r],
                 outline=style["stripe"], width=1)

    # Text: ₹ + denomination
    text = f"₹{denomination}"
    font = _get_font(14 if denomination < 1000 else 12)
    bbox = draw.textbbox((0, 0), text, font=font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((cx - tw // 2, cy - th // 2 - 1), text,
              fill=style["text"], font=font)

    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


def decompose_bet(amount: int) -> list[int]:
    """Break a bet amount into chip denominations (greedy, largest first)."""
    denoms = sorted(CHIP_DENOMINATIONS.keys(), reverse=True)
    chips = []
    remaining = amount
    for d in denoms:
        while remaining >= d:
            chips.append(d)
            remaining -= d
    return chips


def decompose_bet_grouped(amount: int) -> list[tuple[int, int]]:
    """Break a bet into grouped chips: list of (denomination, count)."""
    denoms = sorted(CHIP_DENOMINATIONS.keys(), reverse=True)
    groups = []
    remaining = amount
    for d in denoms:
        count = remaining // d
        if count > 0:
            groups.append((d, count))
            remaining -= d * count
    return groups


def render_chip_stack(amount: int) -> list[bytes]:
    """Return a list of chip PNG bytes for the given amount."""
    return [render_chip(d) for d in decompose_bet(amount)]
