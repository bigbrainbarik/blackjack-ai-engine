"""
Three visual themes for the Blackjack UI.

Each theme is a dict of CSS custom-property values.  ``get_theme_css()``
returns a complete ``<style>`` block that the main page injects via
``st.markdown(unsafe_allow_html=True)``.
"""

THEMES = {
    "casino_green": {
        "name": "Casino Green",
        "bg": "linear-gradient(145deg, #0d3b0d 0%, #14532d 40%, #166534 70%, #0d3b0d 100%)",
        "sidebar_bg": "#1a1a1a",
        "card_table": "rgba(22, 101, 52, 0.35)",
        "text": "#f0f0f0",
        "text_muted": "#a3c9a3",
        "accent": "#d4a044",
        "accent2": "#c8a94e",
        "metric_bg": "rgba(0, 0, 0, 0.35)",
        "metric_border": "rgba(212, 160, 68, 0.25)",
        "btn_primary_bg": "#b8860b",
        "btn_primary_hover": "#d4a044",
        "btn_primary_text": "#fff",
        "btn_secondary_bg": "rgba(255,255,255,0.08)",
        "btn_secondary_hover": "rgba(255,255,255,0.16)",
        "btn_secondary_text": "#e0e0e0",
        "divider": "rgba(212, 160, 68, 0.2)",
        "win": "#4ade80",
        "lose": "#f87171",
        "push": "#fbbf24",
        "bust": "#fb923c",
        "blackjack": "#ffd700",
        "surrender": "#c084fc",
        "glow_color": "rgba(212, 160, 68, 0.4)",
        "card_shadow": "0 4px 16px rgba(0,0,0,0.5)",
    },
    "dark_neon": {
        "name": "Dark Neon",
        "bg": "linear-gradient(160deg, #0a0a0a 0%, #0f0f23 50%, #0a0a0a 100%)",
        "sidebar_bg": "#0d0d1a",
        "card_table": "rgba(15, 15, 35, 0.6)",
        "text": "#e0e0e0",
        "text_muted": "#888",
        "accent": "#00e5ff",
        "accent2": "#ff2dce",
        "metric_bg": "rgba(0, 229, 255, 0.06)",
        "metric_border": "rgba(0, 229, 255, 0.2)",
        "btn_primary_bg": "rgba(0, 229, 255, 0.15)",
        "btn_primary_hover": "rgba(0, 229, 255, 0.3)",
        "btn_primary_text": "#00e5ff",
        "btn_secondary_bg": "rgba(255, 45, 206, 0.1)",
        "btn_secondary_hover": "rgba(255, 45, 206, 0.2)",
        "btn_secondary_text": "#ff2dce",
        "divider": "rgba(0, 229, 255, 0.15)",
        "win": "#39ff14",
        "lose": "#ff3131",
        "push": "#ffe600",
        "bust": "#ff6b2b",
        "blackjack": "#ffd700",
        "surrender": "#d946ef",
        "glow_color": "rgba(0, 229, 255, 0.35)",
        "card_shadow": "0 0 20px rgba(0, 229, 255, 0.25)",
    },
    "minimalist_dark": {
        "name": "Minimalist Dark",
        "bg": "#1a1a2e",
        "sidebar_bg": "#16162a",
        "card_table": "rgba(255,255,255,0.03)",
        "text": "#e8e8e8",
        "text_muted": "#888",
        "accent": "#7c83ff",
        "accent2": "#7c83ff",
        "metric_bg": "rgba(255,255,255,0.04)",
        "metric_border": "rgba(124, 131, 255, 0.15)",
        "btn_primary_bg": "#7c83ff",
        "btn_primary_hover": "#9ba0ff",
        "btn_primary_text": "#0e0e1a",
        "btn_secondary_bg": "rgba(255,255,255,0.06)",
        "btn_secondary_hover": "rgba(255,255,255,0.12)",
        "btn_secondary_text": "#c0c0c0",
        "divider": "rgba(255,255,255,0.07)",
        "win": "#34d399",
        "lose": "#fb7185",
        "push": "#fbbf24",
        "bust": "#fb923c",
        "blackjack": "#fde68a",
        "surrender": "#c084fc",
        "glow_color": "rgba(124, 131, 255, 0.2)",
        "card_shadow": "0 2px 8px rgba(0,0,0,0.3)",
    },
}


def get_theme(name: str) -> dict:
    return THEMES.get(name, THEMES["casino_green"])


def get_theme_css(name: str) -> str:
    """Return a full <style> block for the given theme."""
    t = get_theme(name)
    return f"""<style>
/* ── Google Fonts ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

/* ── Root Variables ── */
:root {{
    --bg: {t["bg"]};
    --sidebar-bg: {t["sidebar_bg"]};
    --card-table: {t["card_table"]};
    --text: {t["text"]};
    --text-muted: {t["text_muted"]};
    --accent: {t["accent"]};
    --accent2: {t["accent2"]};
    --metric-bg: {t["metric_bg"]};
    --metric-border: {t["metric_border"]};
    --divider: {t["divider"]};
    --glow: {t["glow_color"]};
    --card-shadow: {t["card_shadow"]};
    --win: {t["win"]};
    --lose: {t["lose"]};
    --push: {t["push"]};
    --bust: {t["bust"]};
    --blackjack: {t["blackjack"]};
    --surrender: {t["surrender"]};
}}

/* ── Base app background ── */
.stApp {{
    background: {t["bg"]};
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}}

/* ── All text white by default ── */
.stApp h1, .stApp h2, .stApp h3, .stApp h4, .stApp p, .stApp label,
.stApp .stMarkdown, .stApp li, .stApp td, .stApp th,
.stApp [data-testid="stMetricValue"],
.stApp [data-testid="stMetricLabel"] {{
    color: {t["text"]} !important;
    font-family: 'Inter', sans-serif;
}}
/* Color override for spans — but DO NOT override font-family,
   because Streamlit icons use Material Symbols Rounded on spans. */
.stApp .stMarkdown span, .stApp p span, .stApp label span {{
    color: {t["text"]} !important;
}}

/* ── Title & headings ── */
.stApp h1 {{
    font-weight: 800;
    letter-spacing: -0.5px;
    text-shadow: 0 2px 8px rgba(0,0,0,0.3);
}}
.stApp h2, .stApp h3 {{
    font-weight: 700;
}}

/* ── Metric cards — glassmorphism ── */
div[data-testid="stMetric"] {{
    background: {t["metric_bg"]};
    backdrop-filter: blur(12px);
    -webkit-backdrop-filter: blur(12px);
    border: 1px solid {t["metric_border"]};
    border-radius: 14px;
    padding: 14px 18px;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}}
div[data-testid="stMetric"]:hover {{
    transform: translateY(-2px);
    box-shadow: 0 8px 24px rgba(0,0,0,0.25);
}}

/* ── Sidebar ── */
section[data-testid="stSidebar"] {{
    background: {t["sidebar_bg"]};
}}
section[data-testid="stSidebar"] h1,
section[data-testid="stSidebar"] h2,
section[data-testid="stSidebar"] h3,
section[data-testid="stSidebar"] p,
section[data-testid="stSidebar"] span,
section[data-testid="stSidebar"] label,
section[data-testid="stSidebar"] .stMarkdown {{
    color: #eee !important;
}}

/* ── Buttons — primary ── */
.stApp .stButton > button {{
    font-family: 'Inter', sans-serif;
    font-size: 0.95rem;
    font-weight: 600;
    padding: 0.55rem 1rem;
    border-radius: 10px;
    min-height: 2.8rem;
    white-space: nowrap;
    letter-spacing: 0.3px;
    transition: transform 0.15s ease, box-shadow 0.15s ease, background 0.2s ease;
    border: 1px solid transparent;
}}
.stApp .stButton > button:hover {{
    transform: scale(1.04);
    box-shadow: 0 4px 18px {t["glow_color"]};
}}
.stApp .stButton > button:active {{
    transform: scale(0.96);
}}

/* ── Primary action buttons (type=primary) ── */
.stApp .stButton > button[kind="primary"],
.stApp .stButton > button[data-testid*="primary"] {{
    background: {t["btn_primary_bg"]};
    color: {t["btn_primary_text"]};
    border: 1px solid rgba(255,255,255,0.08);
}}
.stApp .stButton > button[kind="primary"]:hover,
.stApp .stButton > button[data-testid*="primary"]:hover {{
    background: {t["btn_primary_hover"]};
}}

/* ── Dividers ── */
.stApp hr {{
    border-color: {t["divider"]} !important;
}}

/* ── Result text classes ── */
.result-win       {{ color: {t["win"]} !important; font-size: 1.6rem; font-weight: 700; text-shadow: 0 0 12px {t["win"]}40; }}
.result-lose      {{ color: {t["lose"]} !important; font-size: 1.6rem; font-weight: 700; }}
.result-push      {{ color: {t["push"]} !important; font-size: 1.6rem; font-weight: 700; }}
.result-bust      {{ color: {t["bust"]} !important; font-size: 1.6rem; font-weight: 700; text-shadow: 0 0 10px {t["bust"]}40; }}
.result-blackjack {{ color: {t["blackjack"]} !important; font-size: 1.8rem; font-weight: 800; text-shadow: 0 0 18px {t["blackjack"]}60; }}
.result-surrender {{ color: {t["surrender"]} !important; font-size: 1.6rem; font-weight: 700; }}

/* ── Card area ── */
.card-label {{
    text-align: center;
    font-size: 1.15rem;
    font-weight: 700;
    color: {t["text"]};
    text-shadow: 0 1px 4px rgba(0,0,0,0.3);
    letter-spacing: 0.5px;
    text-transform: uppercase;
}}
.hand-label {{
    font-size: 0.95rem;
    font-weight: 600;
    color: {t["text_muted"]};
    margin-bottom: 2px;
}}

/* ── Card table felt area ── */
.card-table-area {{
    background: {t["card_table"]};
    border-radius: 20px;
    padding: 24px;
    margin: 12px 0;
    border: 1px solid rgba(255,255,255,0.05);
}}

/* ── Progress bars (NN confidence) ── */
.stProgress > div > div > div {{
    background: {t["accent"]} !important;
}}

/* ── Expander styling ── */
.stApp details {{
    border-color: {t["divider"]} !important;
}}

/* ── Tabs ── */
.stTabs [data-baseweb="tab-list"] button {{
    color: {t["text_muted"]} !important;
    font-weight: 500;
}}
.stTabs [data-baseweb="tab-list"] button[aria-selected="true"] {{
    color: {t["accent"]} !important;
    border-bottom-color: {t["accent"]} !important;
}}

/* ── Info/warning boxes ── */
.stAlert {{
    background: rgba(255,255,255,0.04) !important;
    border-color: {t["accent"]}40 !important;
    color: {t["text"]} !important;
}}

/* ── Scrollbar ── */
::-webkit-scrollbar {{
    width: 8px;
}}
::-webkit-scrollbar-thumb {{
    background: rgba(255,255,255,0.15);
    border-radius: 4px;
}}
::-webkit-scrollbar-track {{
    background: transparent;
}}

/* ── Hide ALL default Streamlit page navigation ── */
[data-testid="stSidebarNav"],
[data-testid="stSidebarNavItems"],
[data-testid="stSidebarNavSeparator"],
[data-testid="stSidebarNavLink"],
header[data-testid="stHeader"] nav,
section[data-testid="stSidebar"] > div > ul,
section[data-testid="stSidebar"] > div > nav {{
    display: none !important;
}}
</style>"""
