"""
Generates high-quality playing card images using Pillow.
Features: drop shadows, subtle gradients, proper pip layouts,
face-card decorative patterns — no external image files needed.
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
from io import BytesIO
import functools

CARD_WIDTH = 150
CARD_HEIGHT = 210
CORNER_RADIUS = 14
SHADOW_OFFSET = 3
SHADOW_BLUR = 6

SUIT_SYMBOLS = {
    "Hearts": "\u2665",
    "Diamonds": "\u2666",
    "Clubs": "\u2663",
    "Spades": "\u2660",
}

SUIT_COLORS = {
    "Hearts": "#D32F2F",
    "Diamonds": "#D32F2F",
    "Clubs": "#1a1a1a",
    "Spades": "#1a1a1a",
}

# Pip positions (normalised 0-1 within the card body) for number cards
PIP_LAYOUTS = {
    "A":  [(0.5, 0.5)],
    "2":  [(0.5, 0.25), (0.5, 0.75)],
    "3":  [(0.5, 0.2), (0.5, 0.5), (0.5, 0.8)],
    "4":  [(0.33, 0.25), (0.67, 0.25), (0.33, 0.75), (0.67, 0.75)],
    "5":  [(0.33, 0.25), (0.67, 0.25), (0.5, 0.5), (0.33, 0.75), (0.67, 0.75)],
    "6":  [(0.33, 0.25), (0.67, 0.25), (0.33, 0.5), (0.67, 0.5), (0.33, 0.75), (0.67, 0.75)],
    "7":  [(0.33, 0.22), (0.67, 0.22), (0.33, 0.5), (0.67, 0.5), (0.5, 0.36), (0.33, 0.78), (0.67, 0.78)],
    "8":  [(0.33, 0.2), (0.67, 0.2), (0.33, 0.4), (0.67, 0.4), (0.5, 0.3), (0.33, 0.6), (0.67, 0.6), (0.5, 0.7)],
    "9":  [(0.33, 0.18), (0.67, 0.18), (0.33, 0.38), (0.67, 0.38), (0.5, 0.5),
           (0.33, 0.62), (0.67, 0.62), (0.33, 0.82), (0.67, 0.82)],
    "10": [(0.33, 0.16), (0.67, 0.16), (0.33, 0.34), (0.67, 0.34), (0.5, 0.25),
           (0.5, 0.75), (0.33, 0.52), (0.67, 0.52), (0.33, 0.7), (0.67, 0.7)],
}

FACE_LETTERS = {"J": "J", "Q": "Q", "K": "K"}


def _get_font(size, bold=False):
    """Return a truetype font, falling back to default if unavailable."""
    names = (["arialbd.ttf", "Arial Bold.ttf", "DejaVuSans-Bold.ttf"]
             if bold else ["arial.ttf", "Arial.ttf", "DejaVuSans.ttf"])
    for name in names:
        try:
            return ImageFont.truetype(name, size)
        except OSError:
            continue
    return ImageFont.load_default()


def _draw_shadow(img: Image.Image) -> Image.Image:
    """Add a soft drop-shadow behind the card."""
    padded = Image.new("RGBA",
                       (img.width + SHADOW_BLUR * 2 + SHADOW_OFFSET,
                        img.height + SHADOW_BLUR * 2 + SHADOW_OFFSET),
                       (0, 0, 0, 0))
    # Shadow layer
    shadow = Image.new("RGBA", img.size, (0, 0, 0, 0))
    sd = ImageDraw.Draw(shadow)
    sd.rounded_rectangle([0, 0, img.width - 1, img.height - 1],
                         radius=CORNER_RADIUS, fill=(0, 0, 0, 80))
    shadow = shadow.filter(ImageFilter.GaussianBlur(SHADOW_BLUR))
    padded.paste(shadow, (SHADOW_BLUR + SHADOW_OFFSET, SHADOW_BLUR + SHADOW_OFFSET), shadow)
    padded.paste(img, (SHADOW_BLUR, SHADOW_BLUR), img)
    return padded


@functools.lru_cache(maxsize=64)
def render_card(rank: str, suit: str) -> bytes:
    """Render a single card and return PNG bytes (with drop shadow)."""
    img = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Card body — white with very subtle warm tint
    draw.rounded_rectangle(
        [0, 0, CARD_WIDTH - 1, CARD_HEIGHT - 1],
        radius=CORNER_RADIUS,
        fill="#FAFAF8",
        outline="#C8C8C0",
        width=2,
    )

    # Inner border line for a classy look
    inset = 6
    draw.rounded_rectangle(
        [inset, inset, CARD_WIDTH - 1 - inset, CARD_HEIGHT - 1 - inset],
        radius=CORNER_RADIUS - 3,
        fill=None,
        outline="#E8E8E0",
        width=1,
    )

    color = SUIT_COLORS[suit]
    symbol = SUIT_SYMBOLS[suit]

    # Fonts
    rank_font = _get_font(24, bold=True)
    suit_corner_font = _get_font(18)
    pip_font = _get_font(22)

    # ── Top-left corner: rank + suit ──
    draw.text((12, 10), rank, fill=color, font=rank_font)
    draw.text((13, 34), symbol, fill=color, font=suit_corner_font)

    # ── Bottom-right corner (rotated 180°) ──
    corner = Image.new("RGBA", (50, 55), (0, 0, 0, 0))
    cd = ImageDraw.Draw(corner)
    cd.text((2, 2), rank, fill=color, font=rank_font)
    cd.text((3, 26), symbol, fill=color, font=suit_corner_font)
    corner = corner.rotate(180, expand=False)
    img.paste(corner, (CARD_WIDTH - 55, CARD_HEIGHT - 60), corner)

    # ── Card body area (inside the inner border) ──
    body_left = inset + 4
    body_top = 55
    body_right = CARD_WIDTH - inset - 4
    body_bottom = CARD_HEIGHT - 55
    body_w = body_right - body_left
    body_h = body_bottom - body_top

    if rank in FACE_LETTERS:
        _draw_face_card(draw, img, rank, suit, color, symbol,
                        body_left, body_top, body_w, body_h)
    elif rank in PIP_LAYOUTS:
        _draw_pips(draw, rank, suit, color, symbol, pip_font,
                   body_left, body_top, body_w, body_h)

    # Add drop shadow
    final = _draw_shadow(img)
    buf = BytesIO()
    final.save(buf, format="PNG")
    return buf.getvalue()


def _draw_pips(draw, rank, suit, color, symbol, font,
               bx, by, bw, bh):
    """Draw suit pips in the correct positions for number cards."""
    positions = PIP_LAYOUTS.get(rank, [])
    for (nx, ny) in positions:
        x = bx + int(nx * bw)
        y = by + int(ny * bh)
        bbox = draw.textbbox((0, 0), symbol, font=font)
        tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
        # Flip bottom-half pips
        draw.text((x - tw // 2, y - th // 2), symbol, fill=color, font=font)


def _draw_face_card(draw, img, rank, suit, color, symbol,
                    bx, by, bw, bh):
    """Draw a decorative face card (J/Q/K) — large centered letter + suit frame."""
    # Background tint for face cards
    face_colors = {
        "J": "#FFF8E1",  # warm yellow tint
        "Q": "#FCE4EC",  # pink tint
        "K": "#E8EAF6",  # blue-grey tint
    }
    tint = face_colors.get(rank, "#FFFFFF")
    draw.rounded_rectangle(
        [bx - 2, by - 6, bx + bw + 2, by + bh + 6],
        radius=6, fill=tint, outline=color + "30", width=1,
    )

    # Large centered rank letter
    big_font = _get_font(52, bold=True)
    bbox = draw.textbbox((0, 0), rank, font=big_font)
    tw, th = bbox[2] - bbox[0], bbox[3] - bbox[1]
    cx = bx + (bw - tw) // 2
    cy = by + (bh - th) // 2 - 8
    # Shadow behind letter
    draw.text((cx + 1, cy + 1), rank, fill="#00000020", font=big_font)
    draw.text((cx, cy), rank, fill=color, font=big_font)

    # Suit symbol below the letter
    suit_font = _get_font(28)
    bbox2 = draw.textbbox((0, 0), symbol, font=suit_font)
    sw, sh = bbox2[2] - bbox2[0], bbox2[3] - bbox2[1]
    draw.text((bx + (bw - sw) // 2, cy + th + 2), symbol, fill=color, font=suit_font)

    # Corner decorative dots
    dot_r = 3
    for dx, dy in [(bx + 6, by + 2), (bx + bw - 6, by + 2),
                   (bx + 6, by + bh - 2), (bx + bw - 6, by + bh - 2)]:
        draw.ellipse([dx - dot_r, dy - dot_r, dx + dot_r, dy + dot_r],
                     fill=color + "40")


@functools.lru_cache(maxsize=1)
def render_card_back() -> bytes:
    """Render an ornate card back and return PNG bytes (with shadow)."""
    img = Image.new("RGBA", (CARD_WIDTH, CARD_HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Outer body — deep blue
    draw.rounded_rectangle(
        [0, 0, CARD_WIDTH - 1, CARD_HEIGHT - 1],
        radius=CORNER_RADIUS,
        fill="#0D47A1",
        outline="#082E6A",
        width=2,
    )

    # Inner border
    inset = 8
    draw.rounded_rectangle(
        [inset, inset, CARD_WIDTH - 1 - inset, CARD_HEIGHT - 1 - inset],
        radius=CORNER_RADIUS - 4,
        fill="#1565C0",
        outline="#90CAF9",
        width=1,
    )

    # Cross-hatch diamond pattern
    inner_inset = 14
    for y in range(inner_inset, CARD_HEIGHT - inner_inset, 14):
        for x in range(inner_inset, CARD_WIDTH - inner_inset, 14):
            # Check if inside the rounded inner rect
            if (inner_inset + 4 < x < CARD_WIDTH - inner_inset - 4 and
                    inner_inset + 4 < y < CARD_HEIGHT - inner_inset - 4):
                draw.regular_polygon(
                    (x, y, 4), n_sides=4,
                    fill="#1E88E5", outline="#42A5F5",
                )

    # Central decorative circle
    cx, cy = CARD_WIDTH // 2, CARD_HEIGHT // 2
    for r, fill_c, outline_c in [
        (22, "#0D47A1", "#90CAF9"),
        (16, "#1565C0", "#64B5F6"),
        (10, "#1E88E5", "#BBDEFB"),
    ]:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                     fill=fill_c, outline=outline_c, width=1)

    # Star in center
    star_font = _get_font(18, bold=True)
    draw.text((cx - 5, cy - 10), "★", fill="#BBDEFB", font=star_font)

    final = _draw_shadow(img)
    buf = BytesIO()
    final.save(buf, format="PNG")
    return buf.getvalue()
