#!/usr/bin/env python3
"""
Section banners SVG generator for GitHub profile.
Creates 6 section header banners with consistent slim design.

Contract:
  Generates 6 banner SVGs (920x56 each):
  - section-about.svg, section-connect.svg, section-tech.svg
  - section-projects.svg, section-stats.svg, section-snake.svg
  Each banner: glyph chip (accent color, rounded) + title + gradient rule
  Transparent background (floats on GitHub's own background)
  --mock: Use static mock data (default True)
  --out PATH: Output directory (files named section-{name}.svg)
"""

import argparse
import os
import xml.dom.minidom
from theme import PALETTE, FONT, esc, styles, text_width as theme_text_width


# Glyph paths (24x24 SVG paths, centered in 0-24 viewBox)
GLYPHS = {
    # Person silhouette — solid shapes only; the previous info-disc glyph
    # relied on evenodd cutouts and rendered as a solid ball
    "about": "M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z",
    "connect": "M9 5c1.654 0 3-1.346 3-3S10.654-1 9-1 6 0.346 6 2 7.346 5 9 5zm6 0c1.654 0 3-1.346 3-3s-1.346-3-3-3-3 1.346-3 3 1.346 3 3 3zM9 8C7.076 8 3 9.009 3 11v3h12v-3c0-1.991-4.076-3-6-3zm6 0c-.06 0-.124.005-.186.01C12.503 8.346 13.697 9.161 14 10.5V14h4v-3c0-1.991-4.076-3-6-3z",  # Link/nodes icon
    "tech": "M19.43 12.98c.04-.32.07-.64.07-.98 0-.34-.03-.66-.07-.98l2.11-1.65c.19-.15.24-.42.12-.64l-2-3.46c-.12-.22-.37-.29-.59-.22l-2.49 1c-.52-.4-1.08-.73-1.69-.98l-.37-2.65c-.04-.24-.24-.41-.48-.41h-3.84c-.24 0-.43.17-.47.41l-.37 2.65c-.61.25-1.17.59-1.69.98l-2.49-1c-.22-.09-.47 0-.59.22l-2 3.46c-.13.22-.07.49.12.64l2.11 1.65c-.04.32-.07.65-.07.98s.03.66.07.98l-2.11 1.65c-.19.15-.24.42-.12.64l2 3.46c.12.22.37.29.59.22l2.49-1c.52.4 1.08.73 1.69.98l.37 2.65c.05.24.24.41.48.41h3.84c.24 0 .44-.17.47-.41l.37-2.65c.61-.25 1.17-.59 1.69-.98l2.49 1c.23.09.48 0 .59-.22l2-3.46c.12-.22.07-.49-.12-.64l-2.11-1.65zM12 15.5c-1.93 0-3.5-1.57-3.5-3.5s1.57-3.5 3.5-3.5 3.5 1.57 3.5 3.5-1.57 3.5-3.5 3.5z",  # Wrench/gear icon
    "projects": "M12 1l3.6 7.26h8.04l-6.52 4.74 2.52 7.94L12 16.5l-6.64 4.44 2.52-7.94-6.52-4.74h8.04L12 1z",  # Rocket (star as placeholder)
    "stats": "M5 9.1h3V19H5zM10.1 5h2.8v14h-2.8zm5.9 5H19v9h-3.1z",  # Bar chart icon
    "snake": "M3 12c1-1 2-1 3-2s1-2 2-3 2-1 3-2 2-1 3 0 1 2 0 3-2 1-3 2-1 2-2 3-2 1-3 2-2 1-3 0-1-2 0-3 2-1 3-2 1-2 2-3 1-2 2-3 2-1 3-2",  # Winding path (simplified)
}

# Accent colors for each section (from PALETTE keys)
SECTION_ACCENTS = {
    "about": "blue",
    "connect": "cyan",
    "tech": "purple",
    "projects": "orange",
    "stats": "teal",
    "snake": "green",
}

# Display titles
SECTION_TITLES = {
    "about": "About Me",
    "connect": "Connect With Me",
    "tech": "Tech Stack",
    "projects": "Featured Projects",
    "stats": "GitHub Stats",
    "snake": "Contribution Snake",
}


def generate_section_banner(
    section_key: str,
    title: str,
    glyph_d: str,
    accent_key: str,
    out_path: str,
) -> None:
    """
    Generate a single section banner SVG.

    Args:
        section_key: Section key (e.g., "about")
        title: Display title (e.g., "About")
        glyph_d: SVG path d attribute (24x24)
        accent_key: Key in PALETTE for accent color
        out_path: Output file path
    """
    width, height = 920, 56
    chip_size = 32  # Glyph chip outer size
    chip_x = 8  # Left padding
    chip_y = (height - chip_size) / 2  # Vertically centered

    # Title text positioned next to chip
    title_x = chip_x + chip_size + 16  # chip + gap
    title_y = height / 2 + 7  # Vertically centered (rough baseline adjustment)

    # Gradient rule starts after title text + gap
    title_width = theme_text_width(title, 20)
    gradient_start_x = title_x + title_width + 20  # title + gap

    # Get accent color from PALETTE
    accent_color = PALETTE[accent_key]

    # Create SVG with transparent background
    svg_content = f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">\n'

    # CSS animations (opacity-only, no transform keyframes)
    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
g {
  animation: fadeIn 0.5s ease-out forwards;
}
"""
    svg_content += styles(css) + "\n"

    # Wrapping content group
    svg_content += '<g>\n'

    # Glyph chip (rounded rect background)
    chip_rx = chip_size / 2  # Fully rounded
    svg_content += f'<rect x="{chip_x}" y="{chip_y}" width="{chip_size}" height="{chip_size}" rx="{chip_rx}" fill="{accent_color}" opacity="0.15"/>\n'

    # Glyph icon (24x24, centered in chip)
    glyph_x = chip_x + (chip_size - 24) / 2
    glyph_y = chip_y + (chip_size - 24) / 2
    svg_content += f'<g transform="translate({glyph_x},{glyph_y})"><path d="{glyph_d}" fill="{accent_color}"/></g>\n'

    # Section title (20px, 700 weight)
    svg_content += f'<text x="{title_x}" y="{title_y}" font-family="{FONT}" font-size="20" font-weight="700" fill="{PALETTE["text"]}">{esc(title)}</text>\n'

    # Gradient rule (accent -> transparent)
    # SVG linearGradient to fade from accent to transparent
    gradient_id = f"rule-gradient-{section_key}"
    svg_content += f'''<defs>
<linearGradient id="{gradient_id}" x1="0%" y1="0%" x2="100%" y2="0%">
<stop offset="0%" style="stop-color:{accent_color};stop-opacity:1" />
<stop offset="100%" style="stop-color:{accent_color};stop-opacity:0" />
</linearGradient>
</defs>
'''

    # Thin horizontal line (1px) vertically centered
    rule_y = height / 2 - 0.5
    rule_height = 1
    rule_width = width - gradient_start_x - 20
    svg_content += f'<rect x="{gradient_start_x}" y="{rule_y}" width="{rule_width}" height="{rule_height}" fill="url(#{gradient_id})"/>\n'

    # Slow light sweep along the rule (SMIL x animation — attribute-based)
    sweep_end = gradient_start_x + rule_width - 60
    svg_content += (
        f'<rect x="{gradient_start_x}" y="{rule_y - 0.5}" width="60" height="2" rx="1" '
        f'fill="{accent_color}" opacity="0.45">\n'
        f'  <animate attributeName="x" from="{gradient_start_x}" to="{sweep_end}" '
        f'dur="4.5s" repeatCount="indefinite"/>\n'
        f'  <animate attributeName="opacity" values="0;0.45;0.45;0" keyTimes="0;0.15;0.75;1" '
        f'dur="4.5s" repeatCount="indefinite"/>\n'
        f'</rect>\n'
    )

    svg_content += '</g>\n'
    svg_content += '</svg>'

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
    except Exception as e:
        print(f"✗ XML validation failed for {section_key}: {e}")
        raise

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)

    # Write SVG
    with open(out_path, "w") as f:
        f.write(svg_content)

    print(f"✓ Section banner generated: {out_path}")


def render_all(data: dict, base_out_dir: str = "profile") -> None:
    """
    Render all section banners (orchestrator interface).

    Args:
        data: Shared data dict (unused for section banners, always static)
        base_out_dir: Base output directory for all banner files
    """
    generate_all_banners(base_out_dir, mock=False)


def generate_all_banners(base_out_dir: str = "profile", mock: bool = True) -> None:
    """Generate all 6 section banners."""

    sections = [
        ("about", SECTION_TITLES["about"], GLYPHS["about"], SECTION_ACCENTS["about"]),
        ("connect", SECTION_TITLES["connect"], GLYPHS["connect"], SECTION_ACCENTS["connect"]),
        ("tech", SECTION_TITLES["tech"], GLYPHS["tech"], SECTION_ACCENTS["tech"]),
        ("projects", SECTION_TITLES["projects"], GLYPHS["projects"], SECTION_ACCENTS["projects"]),
        ("stats", SECTION_TITLES["stats"], GLYPHS["stats"], SECTION_ACCENTS["stats"]),
        ("snake", SECTION_TITLES["snake"], GLYPHS["snake"], SECTION_ACCENTS["snake"]),
    ]

    for section_key, title, glyph_d, accent_key in sections:
        out_path = os.path.join(base_out_dir, f"section-{section_key}.svg")
        generate_section_banner(section_key, title, glyph_d, accent_key, out_path)


def main():
    parser = argparse.ArgumentParser(description="Generate section banner SVGs for GitHub profile")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock data (always True)")
    parser.add_argument(
        "--out",
        type=str,
        default="profile",
        help="Output directory (files named section-{name}.svg)",
    )

    args = parser.parse_args()

    try:
        generate_all_banners(args.out, args.mock)
        print(f"✓ Successfully created all section banners in {args.out}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
