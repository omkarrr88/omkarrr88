#!/usr/bin/env python3
"""
Connect badges SVG generator for GitHub profile.
Creates 6 social/contact badges with consistent pill design.

Contract:
  Generates 6 badge SVGs (auto width ~170-180px, 42px height):
  - linkedin, x, instagram, portfolio, email, resume
  Each badge: pill shape + brand icon + label
  --mock: Use static mock data (default True)
  --out PATH: Output SVG file path (pattern: profile/connect-{name}.svg)
"""

import argparse
import os
import xml.dom.minidom
from theme import PALETTE, FONT, esc, get_brand_hex
from icons import ICONS


def measure_text_width(text: str, font_size: int = 14) -> float:
    """Rough estimate of text width in pixels."""
    return len(text) * 8.5


def generate_badge(
    name: str,
    label: str,
    icon_key: str,
    icon_hex: str,
    out_path: str,
    use_custom_icon: bool = False,
    custom_icon_d: str = "",
) -> None:
    """
    Generate a single connect badge SVG.

    Args:
        name: Badge key (e.g., "linkedin")
        label: Display label (e.g., "LinkedIn")
        icon_key: Key in ICONS dict (e.g., "linkedin")
        icon_hex: Hex color for icon
        out_path: Output file path
        use_custom_icon: If True, use custom_icon_d instead of ICONS lookup
        custom_icon_d: Custom SVG path d attribute
    """
    # Calculate dimensions
    label_width = measure_text_width(label, 14)
    badge_height = 42
    icon_size = 20
    padding_h = 16
    gap = 6

    badge_width = icon_size + gap + label_width + padding_h * 2

    # Create SVG
    svg = f'<svg width="{int(badge_width)}" height="{badge_height}" viewBox="0 0 {int(badge_width)} {badge_height}" xmlns="http://www.w3.org/2000/svg">\n'

    # CSS for animations
    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
@keyframes shine {
  0% {
    background-position: -100% center;
  }
  100% {
    background-position: 100% center;
  }
}
g {
  animation: fadeIn 0.6s ease-out forwards;
}
"""
    svg += f"<style>{css}</style>\n"

    # Pill background
    svg += f'<rect x="0.5" y="0.5" width="{int(badge_width - 1)}" height="{badge_height - 1}" rx="21" fill="{PALETTE["bg_deep"]}" stroke="{PALETTE["border"]}" stroke-width="1"/>\n'

    # Icon
    icon_x = padding_h
    icon_y = (badge_height - icon_size) / 2

    if use_custom_icon:
        icon_d = custom_icon_d
    else:
        icon = ICONS.get(icon_key, {})
        icon_d = icon.get("d", "")

    if icon_d:
        adjusted_hex = get_brand_hex(icon_hex)
        svg += f'<g transform="translate({icon_x},{icon_y}) scale(0.833)"><path d="{icon_d}" fill="#{adjusted_hex}"/></g>\n'

    # Label text
    text_x = padding_h + icon_size + gap
    text_y = (badge_height + 5) / 2
    svg += f'<text x="{text_x}" y="{text_y}" font-family="{FONT}" font-size="14" font-weight="600" fill="{PALETTE["text"]}">{esc(label)}</text>\n'

    svg += "</svg>"

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg)
    except Exception as e:
        print(f"✗ XML validation failed for {name}: {e}")
        raise

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)

    # Write SVG
    with open(out_path, "w") as f:
        f.write(svg)

    print(f"✓ Connect badge generated: {out_path}")


def render_all(data: dict, base_out_dir: str = "profile") -> None:
    """
    Render all connect badges (orchestrator interface).

    Args:
        data: Shared data dict (unused for connect badges, always static)
        base_out_dir: Base output directory for all badge files
    """
    generate_all_badges(base_out_dir, mock=False)


def generate_all_badges(base_out_dir: str = "profile", mock: bool = True) -> None:
    """Generate all 6 connect badges."""

    # Document icon (custom, for resume)
    document_icon = "M4 2a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V4a2 2 0 0 0-2-2H4zm0 2h16v16H4V4zm2 2v12h12V6H6zm2 2h8v2H8V8zm0 4h8v2H8v-2zm0 4h4v2H8v-2z"

    badges = [
        ("linkedin", "LinkedIn", "linkedin", "0A66C2", False, ""),
        ("x", "X", "x", "000000", False, ""),
        ("instagram", "Instagram", "instagram", "E4405F", False, ""),
        ("portfolio", "Portfolio", "vercel", "7aa2f7", False, ""),
        ("email", "Email", "gmail", "EA4335", False, ""),
        ("resume", "Resume", "", "7aa2f7", True, document_icon),
    ]

    for badge_key, label, icon_key, icon_hex, use_custom, custom_icon in badges:
        out_path = os.path.join(base_out_dir, f"connect-{badge_key}.svg")
        generate_badge(badge_key, label, icon_key, icon_hex, out_path, use_custom, custom_icon)


def main():
    parser = argparse.ArgumentParser(description="Generate connect badge SVGs for GitHub profile")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock data (always True)")
    parser.add_argument(
        "--out",
        type=str,
        default="profile",
        help="Output directory (files named connect-{name}.svg)",
    )

    args = parser.parse_args()

    try:
        generate_all_badges(args.out, args.mock)
        print(f"✓ Successfully created all connect badges in {args.out}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
