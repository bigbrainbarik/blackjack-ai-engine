"""
Card & chip dealing / revealing animations.

Each function returns an HTML string that can be rendered via
``st.components.html()`` or ``st.markdown(unsafe_allow_html=True)``.
Cards are embedded as base64-encoded ``<img>`` tags and animated with CSS.
"""

import base64
from typing import List, Tuple, Optional


def _b64_img(png_bytes: bytes) -> str:
    """Convert raw PNG bytes into an inline base64 data-URI."""
    encoded = base64.b64encode(png_bytes).decode()
    return f"data:image/png;base64,{encoded}"


def animated_cards_html(
    card_images: List[bytes],
    card_width: int = 110,
    stagger_ms: int = 150,
    flip_index: Optional[int] = None,
    back_image: Optional[bytes] = None,
    shake: bool = False,
    label: str = "",
    total_text: str = "",
) -> str:
    """
    Render a row of cards with staggered deal-in animation.

    Parameters
    ----------
    card_images : list of PNG bytes for each card face
    card_width  : display width in pixels
    stagger_ms  : ms delay between each card's entrance
    flip_index  : if set, that card index shows back first then flips
    back_image  : PNG bytes for card back (needed if flip_index is set)
    shake       : if True, the container shakes (bust effect)
    label       : text label above the card row (e.g. "Dealer", "Player")
    total_text  : text below cards (e.g. "Hard 18")
    """
    card_height = int(card_width * 1.4)
    cards_html = []

    for i, img_bytes in enumerate(card_images):
        face_uri = _b64_img(img_bytes)
        delay = i * stagger_ms

        if flip_index is not None and i == flip_index and back_image:
            back_uri = _b64_img(back_image)
            # 3D flip card
            cards_html.append(f"""
            <div class="card-slot flip-card" style="animation-delay:{delay}ms; --flip-delay:{delay + 400}ms;">
              <div class="flip-inner">
                <div class="flip-front">
                  <img src="{back_uri}" width="{card_width}" height="{card_height}" />
                </div>
                <div class="flip-back">
                  <img src="{face_uri}" width="{card_width}" height="{card_height}" />
                </div>
              </div>
            </div>""")
        else:
            cards_html.append(f"""
            <div class="card-slot" style="animation-delay:{delay}ms;">
              <img src="{face_uri}" width="{card_width}" height="{card_height}" />
            </div>""")

    shake_class = "shake-anim" if shake else ""
    label_html = f'<div class="anim-label">{label}</div>' if label else ""
    total_html = f'<div class="anim-total">{total_text}</div>' if total_text else ""

    return f"""
    <div class="animated-hand {shake_class}">
      {label_html}
      <div class="cards-row" id="cardsRow">
        {"".join(cards_html)}
      </div>
      {total_html}
    </div>
    <script>
    // Auto-scroll to the newest (rightmost) card
    var row = document.getElementById('cardsRow');
    if (row) {{ setTimeout(function(){{ row.scrollLeft = row.scrollWidth; }}, {len(card_images) * stagger_ms + 200}); }}
    </script>
    """


def get_animation_css() -> str:
    """Global CSS for all card animations — inject once per page."""
    return """<style>
html, body { margin: 0; padding: 4px; overflow: hidden; }
/* ── Card deal-in ── */
.animated-hand {
    text-align: center;
    margin: 8px 0;
}
.cards-row {
    display: flex;
    gap: 6px;
    perspective: 800px;
    flex-wrap: nowrap;
    overflow-x: auto;
    overflow-y: hidden;
    padding-bottom: 4px;
    scroll-behavior: smooth;
}
/* thin scrollbar for card rows */
.cards-row::-webkit-scrollbar { height: 4px; }
.cards-row::-webkit-scrollbar-thumb { background: rgba(255,255,255,0.25); border-radius: 2px; }
.cards-row::-webkit-scrollbar-track { background: transparent; }
.card-slot {
    opacity: 0;
    transform: translateY(-60px) scale(0.8);
    animation: dealIn 0.4s ease forwards;
    filter: drop-shadow(0 4px 12px rgba(0,0,0,0.45));
    border-radius: 10px;
}
.card-slot img {
    border-radius: 10px;
    display: block;
}
@keyframes dealIn {
    0%   { opacity: 0; transform: translateY(-60px) scale(0.8) rotate(-5deg); }
    60%  { opacity: 1; transform: translateY(4px) scale(1.02) rotate(0.5deg); }
    100% { opacity: 1; transform: translateY(0) scale(1) rotate(0deg); }
}

/* ── 3D Flip ── */
.flip-card {
    perspective: 600px;
}
.flip-inner {
    position: relative;
    width: 100%;
    height: 100%;
    transform-style: preserve-3d;
    animation: dealIn 0.4s ease forwards, flipReveal 0.6s ease forwards;
    animation-delay: inherit, var(--flip-delay, 0.6s);
}
.flip-front, .flip-back {
    backface-visibility: hidden;
    position: absolute;
    top: 0; left: 0;
}
.flip-front {
    z-index: 2;
}
.flip-back {
    transform: rotateY(180deg);
}
@keyframes flipReveal {
    0%   { transform: rotateY(0deg); }
    100% { transform: rotateY(180deg); }
}

/* ── Shake / Bust ── */
.shake-anim .cards-row {
    animation: bustShake 0.5s ease 0.6s;
}
@keyframes bustShake {
    0%, 100% { transform: translateX(0); }
    15%      { transform: translateX(-8px) rotate(-1deg); }
    30%      { transform: translateX(8px) rotate(1deg); }
    45%      { transform: translateX(-6px); }
    60%      { transform: translateX(6px); }
    75%      { transform: translateX(-3px); }
    90%      { transform: translateX(3px); }
}

/* ── Labels ── */
.anim-label {
    font-family: 'Segoe UI', 'Inter', Roboto, -apple-system, sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    color: #f0f0f0;
    text-transform: uppercase;
    letter-spacing: 1.5px;
    margin-bottom: 6px;
    text-shadow: 0 1px 4px rgba(0,0,0,0.4);
    text-align: center;
}
.anim-total {
    font-family: 'Segoe UI', 'Inter', Roboto, -apple-system, sans-serif;
    font-size: 0.9rem;
    font-weight: 600;
    color: #d0d0d0;
    margin-top: 6px;
    text-align: center;
}
</style>"""


def chip_stack_html(chips: List[Tuple[int, int, bytes]], label: str = "") -> str:
    """
    Render a horizontal chip row with multiplier counts.

    chips: list of (denomination, count, png_bytes)
    """
    elements = []
    for i, (denom, count, img_bytes) in enumerate(chips):
        uri = _b64_img(img_bytes)
        delay = i * 80
        count_html = f'<span class="chip-count">&times;{count}</span>' if count > 1 else ''
        elements.append(
            f'<div class="chip-group" style="animation-delay:{delay}ms;">'
            f'<img src="{uri}" width="40" height="40" />'
            f'{count_html}</div>'
        )
    label_html = f'<div class="chip-label">{label}</div>' if label else ""
    return f"""
    <div class="chip-stack">
      <div class="chips-row">{"".join(elements)}</div>
      {label_html}
    </div>
    <style>
    .chip-stack {{ text-align: center; }}
    .chips-row {{ display: inline-flex; flex-direction: row; align-items: center; gap: 6px; justify-content: center; flex-wrap: wrap; }}
    .chip-group {{
        display: flex;
        align-items: center;
        gap: 2px;
        opacity: 0;
        transform: translateY(10px);
        animation: chipIn 0.3s ease forwards;
    }}
    .chip-count {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 0.8rem;
        font-weight: 700;
        color: #e0e0e0;
        text-shadow: 0 1px 2px rgba(0,0,0,0.5);
    }}
    @keyframes chipIn {{
        to {{ opacity: 1; transform: translateY(0); }}
    }}
    .chip-label {{
        font-family: 'Segoe UI', 'Inter', sans-serif;
        font-size: 0.85rem;
        color: #ccc;
        margin-top: 4px;
    }}
    </style>"""
