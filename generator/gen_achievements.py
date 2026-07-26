#!/usr/bin/env python3
"""
Achievements card generator for GitHub profile.
Displays 3 distinctive achievements with glyphs and descriptions.
Specs: 452x210, tokyonight design system.
"""

import argparse
import os
import sys
import xml.dom.minidom
from pathlib import Path

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from theme import PALETTE, FONT, esc, card_frame, styles, title_row


def render(data: dict, out_path: str) -> None:
    """
    Render achievements SVG (orchestrator interface).

    Args:
        data: Shared data dict (unused for achievements, always static)
        out_path: Path to write SVG file
    """
    svg_content = generate_achievements_svg(mock=False)

    # Validate XML
    try:
        import xml.dom.minidom
        xml.dom.minidom.parseString(svg_content)
    except Exception as e:
        raise RuntimeError(f"XML validation failed: {e}")

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)

    # Write SVG
    with open(out_path, "w") as f:
        f.write(svg_content)


def generate_achievements_svg(mock: bool = False) -> str:
    """
    Generate achievements card SVG.

    Returns:
        SVG string
    """
    width, height = 452, 210

    # CSS animations: fade-in-up for rows, soft glow pulse for chip glyphs
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

@keyframes pulseGlow {
  0%, 100% {
    filter: drop-shadow(0 0 3px rgba(255, 255, 255, 0.2));
  }
  50% {
    filter: drop-shadow(0 0 6px rgba(255, 255, 255, 0.4));
  }
}

g.achievement-row {
  animation: fadeInUp 0.6s ease-out forwards;
}

g.achievement-row:nth-of-type(2) {
  animation-delay: 80ms;
}

g.achievement-row:nth-of-type(3) {
  animation-delay: 160ms;
}

g.achievement-row:nth-of-type(4) {
  animation-delay: 240ms;
}

g.achievement-glyph {
  animation: pulseGlow 2s ease-in-out infinite;
}
"""

    # Start SVG
    svg = card_frame(width, height)
    svg += "\n" + styles(css)

    # Title row: trophy icon + "Achievements"
    trophy_icon = "M12 2l-1 2h-4v2h10V4h-4l-1-2zm0 4v4c-2 0-4 2-4 4s2 4 4 4 4-2 4-4 -2-4-4-4zm-2 8h4v2h-4z"
    svg += "\n" + title_row(trophy_icon, "Achievements")

    # Achievement data: (glyph_color, title, detail)
    achievements = [
        (
            PALETTE["orange"],
            "7th of 31,000+ teams",
            "Meta PyTorch Hackathon - Chakravyuh",
        ),
        (
            PALETTE["cyan"],
            "Springer Nature (in review)",
            "V2V collision-risk research - Discover IoT",
        ),
        (
            PALETTE["green"],
            "Avishkar 2025 Finalist",
            "Research Competition - Mumbai University",
        ),
    ]

    # Render achievement rows
    row_height = 48
    start_y = 62

    for idx, (glyph_color, title, detail) in enumerate(achievements):
        y = start_y + (idx * row_height)

        # Achievement row group with staggered animation
        svg += f'\n<g class="achievement-row">'

        # Chip background (rounded rect with bg_deep color)
        chip_x = 22
        chip_y = y - 16
        chip_size = 32
        svg += f'\n<rect x="{chip_x}" y="{chip_y}" width="{chip_size}" height="{chip_size}" rx="8" fill="{PALETTE["bg_deep"]}" stroke="{PALETTE["border"]}" stroke-width="1"/>'

        # Glyph as SVG group inside chip
        svg += f'\n<g class="achievement-glyph" style="color: {glyph_color};">'

        # Render glyph using simple geometric shapes (more reliable than paths)
        if idx == 0:  # Trophy - orange
            # Simple trophy: rectangle base + two handles + cup
            svg += f'\n<rect x="{chip_x + 6}" y="{chip_y + 12}" width="20" height="4" rx="1" fill="{glyph_color}"/>'  # Base
            svg += f'\n<rect x="{chip_x + 8}" y="{chip_y + 4}" width="16" height="8" rx="2" fill="none" stroke="{glyph_color}" stroke-width="1.5"/>'  # Cup
            svg += f'\n<circle cx="{chip_x + 6}" cy="{chip_y + 6}" r="2" fill="{glyph_color}"/>'  # Left handle
            svg += f'\n<circle cx="{chip_x + 26}" cy="{chip_y + 6}" r="2" fill="{glyph_color}"/>'  # Right handle
        elif idx == 1:  # Scroll/Document - cyan
            # Simple document: rectangle outline + three lines
            svg += f'\n<rect x="{chip_x + 7}" y="{chip_y + 4}" width="18" height="22" rx="1" fill="none" stroke="{glyph_color}" stroke-width="1.5"/>'
            svg += f'\n<line x1="{chip_x + 11}" y1="{chip_y + 10}" x2="{chip_x + 21}" y2="{chip_y + 10}" stroke="{glyph_color}" stroke-width="1"/>'
            svg += f'\n<line x1="{chip_x + 11}" y1="{chip_y + 16}" x2="{chip_x + 21}" y2="{chip_y + 16}" stroke="{glyph_color}" stroke-width="1"/>'
            svg += f'\n<line x1="{chip_x + 11}" y1="{chip_y + 22}" x2="{chip_x + 21}" y2="{chip_y + 22}" stroke="{glyph_color}" stroke-width="1"/>'
        else:  # Medal - green, use star shape
            svg += f'\n<path d="M {chip_x + 16} {chip_y + 4} L {chip_x + 18} {chip_y + 12} L {chip_x + 26} {chip_y + 12} L {chip_x + 20} {chip_y + 17} L {chip_x + 22} {chip_y + 25} L {chip_x + 16} {chip_y + 20} L {chip_x + 10} {chip_y + 25} L {chip_x + 12} {chip_y + 17} L {chip_x + 6} {chip_y + 12} L {chip_x + 14} {chip_y + 12} Z" fill="{glyph_color}"/>'

        svg += f'\n</g>'

        # Text: title (600 weight, text color) + detail (12px, muted)
        text_x = chip_x + chip_size + 12  # 22 + 32 + 12 = 66
        title_y = y - 3

        svg += f'\n<text x="{text_x}" y="{title_y}" font-family="{FONT}" font-size="13" font-weight="600" fill="{PALETTE["text"]}">{esc(title)}</text>'

        detail_y = title_y + 14
        svg += f'\n<text x="{text_x}" y="{detail_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}">{esc(detail)}</text>'

        svg += f'\n</g>'

    # Close SVG
    svg += "\n</svg>"

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate Achievements SVG card")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data (not applicable for achievements, always static)",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/achievements.svg",
        help="Output SVG file path",
    )
    args = parser.parse_args()

    # Generate SVG (achievements are static, no data loading needed)
    svg_content = generate_achievements_svg()

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
        print("✓ XML validation passed")
    except Exception as e:
        print(f"✗ XML validation failed: {e}")
        return 1

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.out) if os.path.dirname(args.out) else ".", exist_ok=True)

    # Write SVG
    with open(args.out, "w") as f:
        f.write(svg_content)

    print(f"✓ Achievements SVG written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
