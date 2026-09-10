"""
Design tokens for the "Marquee" theme — a late-night single-screen
cinema rendered in CSS: deep charcoal auditorium, a warm marquee-bulb
gold, and ticket-stub cards with a torn perforation edge.

This module owns only presentation. It never talks to the API and
never imports anything from `app/`.
"""

import streamlit as st

# ---------------------------------------------------------------------------
# Palette — named, not decorative. Every color maps to a real cinema surface.
# ---------------------------------------------------------------------------
COLORS = {
    "void": "#0B0D10",        # auditorium dark — page background
    "screen": "#14181F",      # projection surface — card / panel background
    "screen_raised": "#1B2029",  # slightly lifted panel (hover / active)
    "rule": "#262C36",        # hairline borders, dividers
    "marquee": "#E8B84B",     # marquee-bulb gold — primary accent
    "marquee_dim": "#8A6B2E", # gold at rest / borders
    "velvet": "#C1443A",      # velvet-curtain red — ratings, live badges
    "ink": "#F4F1EA",         # marquee-lit off-white — primary text
    "ink_dim": "#9AA0AC",     # muted text
    "ink_faint": "#5C6270",   # faintest text / placeholders
}

FONT_DISPLAY = "Fraunces"
FONT_BODY = "Inter"
FONT_MONO = "IBM Plex Mono"

GOOGLE_FONTS_URL = (
    "https://fonts.googleapis.com/css2?"
    "family=Fraunces:opsz,wght@9..144,400;9..144,500;9..144,600;9..144,700&"
    "family=Inter:wght@400;500;600;700&"
    "family=IBM+Plex+Mono:wght@400;500&"
    "display=swap"
)


def inject_base_css() -> None:
    """Loads fonts + the compiled stylesheet once per render."""
    with open("styles.css", "r", encoding="utf-8") as f:
        css = f.read()

    tokens = {
        f"__{key.upper()}__": value for key, value in COLORS.items()
    }
    tokens.update(
        {
            "__FONT_DISPLAY__": FONT_DISPLAY,
            "__FONT_BODY__": FONT_BODY,
            "__FONT_MONO__": FONT_MONO,
        }
    )
    for token, value in tokens.items():
        css = css.replace(token, value)

    # IMPORTANT: Streamlit's st.markdown runs content through a CommonMark
    # parser before injecting raw HTML. CommonMark closes an HTML block
    # (like <style>...</style>) at the first blank line, which would dump
    # the rest of the CSS as visible page text. Collapsing all whitespace
    # to single spaces removes every blank line and keeps the whole
    # stylesheet inside one unbroken <style> block.
    css = " ".join(css.split())

    st.markdown(
        f"""
        <link rel="preconnect" href="https://fonts.googleapis.com">
        <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
        <link href="{GOOGLE_FONTS_URL}" rel="stylesheet">
        <style>{css}</style>
        """,
        unsafe_allow_html=True,
    )
