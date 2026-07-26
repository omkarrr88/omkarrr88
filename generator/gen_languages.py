#!/usr/bin/env python3
"""
GitHub Top Languages card generator.
Displays up to 8 languages with animated horizontal bars and a stacked composition strip.
Specs: 452x210, tokyonight design system.
"""

import argparse
import os
import sys
import xml.dom.minidom
from pathlib import Path

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from theme import PALETTE, FONT, MONO, esc, card_frame, styles, title_row
from data import load as load_data


def render(data: dict, out_path: str) -> None:
    """
    Render languages SVG (orchestrator interface).

    Args:
        data: Shared data dict from data.load()
        out_path: Path to write SVG file
    """
    svg_content = generate_languages_svg(data)

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
    except Exception as e:
        raise RuntimeError(f"XML validation failed: {e}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)

    # Write SVG
    with open(out_path, "w") as f:
        f.write(svg_content)


def generate_languages_svg(data: dict) -> str:
    """
    Generate languages SVG card.

    Args:
        data: dict from data.load() containing languages list

    Returns:
        SVG string
    """
    width, height = 452, 210

    # Extract languages (up to 8)
    languages = data.get("languages", [])[:8]

    if not languages:
        languages = [
            {"name": "No languages", "color": "565f89", "pct": 100.0}
        ]

    # CSS animations with inline styles
    css = """
@keyframes slideUp {
  from { transform: translateY(6px); opacity: 0; }
  to { transform: translateY(0); opacity: 1; }
}

@keyframes scaleInBar {
  from { transform: scaleX(0); }
  to { transform: scaleX(1); }
}
"""

    # Start SVG
    svg = card_frame(width, height)
    svg += "\n" + styles(css)

    # Title row with icon (language icon)
    lang_icon = "M20.5 2H3.5C2.12 2 1 3.12 1 4.5v15C1 20.88 2.12 22 3.5 22h17C21.88 22 23 20.88 23 19.5v-15C23 3.12 21.88 2 20.5 2M13 16h-2v-2h2v2m4 0h-2v-2h2v2m3-5H3V5h17v6m-6 2h-2v2h2v-2m4 0h-2v2h2v-2z"
    svg += "\n" + title_row(lang_icon, "Top Languages")

    # Composition strip at top (stacked bar, 100% width)
    strip_y = 50
    strip_height = 11
    strip_x = 22
    strip_width = width - 44  # 22px padding on each side

    total_pct = sum(lang["pct"] for lang in languages)
    if total_pct == 0:
        total_pct = 100

    svg += f'\n<g style="animation: slideUp 0.4s ease-out forwards;">'
    current_x = strip_x
    for lang in languages:
        pct = lang["pct"]
        bar_width = (pct / total_pct) * strip_width
        color = f"#{lang['color']}" if not lang["color"].startswith("#") else lang["color"]
        svg += f'\n<rect x="{current_x}" y="{strip_y}" width="{bar_width}" height="{strip_height}" fill="{color}" rx="2.5"/>'
        current_x += bar_width
    svg += '\n</g>'

    # Language bars (rows below composition strip)
    y_start = 68
    row_height = 16
    bar_width = 145
    bar_height = 6

    for idx, lang in enumerate(languages):
        y = y_start + (idx * row_height)
        row_delay_ms = 100 + (idx * 60)
        bar_delay_ms = 160 + (idx * 60)

        # Row group with inline animation delay
        svg += f'\n<g style="animation: slideUp 0.5s ease-out forwards; animation-delay: {row_delay_ms}ms;">'

        # Language name (left)
        svg += f'\n<text x="{strip_x}" y="{y + 6}" font-family="{FONT}" font-size="12" fill="{PALETTE["text"]}">{esc(lang["name"])}</text>'

        # Animated bar (center-left)
        bar_x = 148
        color = f"#{lang['color']}" if not lang["color"].startswith("#") else lang["color"]
        pct = lang["pct"]
        filled_width = (pct / 100) * bar_width

        # Background bar (unfilled)
        svg += f'\n<rect x="{bar_x}" y="{y + 1}" width="{bar_width}" height="{bar_height}" fill="none" stroke="{PALETTE["border"]}" stroke-width="0.8" rx="2.5" opacity="0.3"/>'

        # Filled bar (animated with inline style)
        svg += f'\n<rect style="animation: scaleInBar 0.6s ease-out forwards; transform-origin: left; animation-delay: {bar_delay_ms}ms;" x="{bar_x}" y="{y + 1}" width="{filled_width}" height="{bar_height}" fill="{color}" rx="2.5"/>'

        # Percentage (right)
        pct_x = bar_x + bar_width + 8
        pct_text = f"{pct:.1f}%".rstrip('0').rstrip('.')
        svg += f'\n<text x="{pct_x}" y="{y + 6}" font-family="{MONO}" font-size="11" fill="{PALETTE["muted"]}" text-anchor="start">{esc(pct_text)}</text>'

        svg += '\n</g>'

    # Close SVG
    svg += "\n</svg>"

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate GitHub Top Languages SVG card")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="/tmp/claude-1000/-home-omkar-kadam-Desktop-github-profile/212468f3-83d5-459e-9ea6-085862b2b933/scratchpad/languages.svg",
        help="Output SVG file path",
    )
    args = parser.parse_args()

    # Load data
    data = load_data(mock=args.mock)

    # Generate SVG
    svg_content = generate_languages_svg(data)

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
        print("✓ XML validation passed")
    except Exception as e:
        print(f"✗ XML validation failed: {e}")
        return 1

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Write SVG
    with open(args.out, "w") as f:
        f.write(svg_content)

    print(f"✓ Languages SVG written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
