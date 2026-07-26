#!/usr/bin/env python3
"""
Theme module for GitHub profile SVG generation.
Implements the tokyonight design system with strict GitHub SVG compatibility.
"""

import xml.dom.minidom

# tokyonight dark palette (default)
PALETTE_DARK = {
    "bg": "#1a1b27",           # card background
    "bg_deep": "#16161e",      # inset panels
    "border": "#2f334d",       # 1px card border, rx=10
    "blue": "#7aa2f7",         # accent primary (headings, key numbers)
    "purple": "#bb9af7",       # accent secondary
    "teal": "#73daca",         # accent positive/highlight
    "green": "#9ece6a",        # accent green
    "orange": "#ff9e64",       # accent warm highlights
    "red": "#f7768e",          # accent red
    "cyan": "#7dcfff",         # accent cyan
    "text": "#c0caf5",         # text primary
    "muted": "#565f89",        # text muted
}

# Light palette (for light mode)
PALETTE_LIGHT = {
    "bg": "#ffffff",           # card background
    "bg_deep": "#f3f4f8",      # inset panels
    "border": "#d0d7de",       # 1px card border, rx=10
    "blue": "#3d59a1",         # accent primary (headings, key numbers)
    "purple": "#7847bd",       # accent secondary
    "teal": "#0f766e",         # accent positive/highlight
    "green": "#587539",        # accent green
    "orange": "#b15c00",       # accent warm highlights
    "red": "#c64343",          # accent red
    "cyan": "#0369a1",         # accent cyan
    "text": "#24292f",         # text primary
    "muted": "#6e7781",        # text muted
}

# Mutable palette (used by generators at render time)
PALETTE = PALETTE_DARK.copy()

# Typography
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif"
MONO = "'Cascadia Code', 'Fira Code', monospace"


def apply_theme(name: str) -> None:
    """
    Apply a theme by updating the module-level PALETTE dict.

    Args:
        name: Theme name ('dark' or 'light')
    """
    global PALETTE
    if name == "dark":
        PALETTE.clear()
        PALETTE.update(PALETTE_DARK)
    elif name == "light":
        PALETTE.clear()
        PALETTE.update(PALETTE_LIGHT)
    else:
        raise ValueError(f"Unknown theme: {name}. Use 'dark' or 'light'.")


def esc(s):
    """XML escape a string for safe SVG text insertion."""
    if not isinstance(s, str):
        s = str(s)
    return (
        s.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
        .replace("'", "&apos;")
    )


def card_frame(width, height):
    """
    Generate SVG card frame with standard chrome.
    Returns opening SVG tag + background rect. Caller must close with </svg>.

    Args:
        width: Card width in pixels
        height: Card height in pixels

    Returns:
        str: Opening SVG + background elements
    """
    svg_open = f'''<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">
<rect x="0.5" y="0.5" width="{width-1}" height="{height-1}" rx="10" fill="{PALETTE['bg']}" stroke="{PALETTE['border']}" stroke-width="1"/>'''
    return svg_open


def styles(css):
    """
    Wrap CSS string in <style> tags.

    Args:
        css: CSS string (no need to include <style> tags)

    Returns:
        str: <style>...</style> element
    """
    return f"<style>{css}</style>"


def title_row(icon_d, title, x=22, y=30):
    """
    Generate a title row with icon + text.

    Args:
        icon_d: SVG path d attribute for icon (24x24 simple-icons format)
        title: Title text
        x: X position of icon (default 22)
        y: Y position of icon/text (default 30)

    Returns:
        str: SVG fragment with icon + title text
    """
    # Icon is 24x24, positioned at (x, y-12) so baseline aligns with text
    icon_y = y - 12
    text_x = x + 32  # Icon (24) + 8px gap

    fragment = f'''<g>
<path d="{icon_d}" fill="{PALETTE['blue']}" transform="translate({x},{icon_y})" width="24" height="24"/>
<text x="{text_x}" y="{y}" font-family="{FONT}" font-size="16" font-weight="600" fill="{PALETTE['blue']}">{esc(title)}</text>
</g>'''
    return fragment


if __name__ == "__main__":
    import argparse
    import os

    parser = argparse.ArgumentParser(description="Theme demo generator")
    parser.add_argument(
        "--out",
        type=str,
        default="/tmp/claude-1000/-home-omkar-kadam-Desktop-github-profile/212468f3-83d5-459e-9ea6-085862b2b933/scratchpad/theme_demo.svg",
        help="Output SVG path",
    )
    args = parser.parse_args()

    # Create demo SVG
    width, height = 400, 250

    # Simple star icon path (24x24)
    star_icon = "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"

    # CSS for fade-in animation
    css = """
@keyframes fadeInUp {
  from {
    transform: translateY(6px);
    opacity: 0;
  }
  to {
    transform: translateY(0);
    opacity: 1;
  }
}
g {
  animation: fadeInUp 0.6s ease-out forwards;
}
g:nth-child(2) {
  animation-delay: 80ms;
}
g:nth-child(3) {
  animation-delay: 160ms;
}
"""

    svg_content = card_frame(width, height)
    svg_content += "\n" + styles(css)
    svg_content += "\n" + title_row(star_icon, "Theme Demo")

    # Add sample text
    svg_content += f'\n<text x="22" y="80" font-family="{FONT}" font-size="13" fill="{PALETTE["text"]}">Professional card design</text>'
    svg_content += f'\n<text x="22" y="105" font-family="{FONT}" font-size="13" fill="{PALETTE["muted"]}">With muted secondary text</text>'

    # Add sample number
    svg_content += f'\n<text x="22" y="145" font-family="{FONT}" font-size="28" font-weight="700" fill="{PALETTE["blue"]}">1,234</text>'
    svg_content += f'\n<text x="22" y="170" font-family="{FONT}" font-size="12" fill="{PALETTE["muted"]}">Key metric label</text>'

    svg_content += "\n</svg>"

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
        print(f"✓ XML validation passed")
    except Exception as e:
        print(f"✗ XML validation failed: {e}")
        exit(1)

    # Write SVG
    with open(args.out, "w") as f:
        f.write(svg_content)

    print(f"✓ Demo SVG written to {args.out}")

def get_brand_hex(brand_hex: str) -> str:
    """
    Get brand color with light-theme fallback for white/light colors.
    On light theme, pure white or very light colors are replaced with
    their true brand hex to avoid white-on-white rendering.

    Args:
        brand_hex: Brand color hex (without #)

    Returns:
        Hex color code (without #) appropriate for current theme
    """
    # On dark theme, use brand hex as-is
    if PALETTE == PALETTE_DARK:
        return brand_hex

    # On light theme, check if color is white/light and needs fallback
    brand_hex_lower = brand_hex.lower()

    # Map of white/light display colors to their true brand hexes
    light_color_map = {
        "ffffff": "000000",  # White -> Black (for apps like X, Next.js)
        "cccccc": "666666",  # Light gray -> Medium gray
        "c0caf5": "3d59a1",  # Theme's light text -> Light blue
    }

    if brand_hex_lower in light_color_map:
        return light_color_map[brand_hex_lower]

    return brand_hex


def text_width(s: str, font_size: float) -> float:
    """Per-character width estimate for the Segoe UI-ish system stack.

    Em-width factors by glyph class; slightly generous so chip pills
    never clip their labels.
    """
    narrow = set("iljft.,:;'|!")
    wide = set("mwMW@")
    total = 0.0
    for ch in s:
        if ch in narrow:
            total += 0.32
        elif ch in wide:
            total += 0.92
        elif ch.isupper() or ch.isdigit():
            total += 0.68
        elif ch == " ":
            total += 0.34
        else:
            total += 0.56
    return total * font_size
