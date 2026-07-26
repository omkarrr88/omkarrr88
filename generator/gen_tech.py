#!/usr/bin/env python3
"""
Tech Stack SVG generator for GitHub profile.
Creates a comprehensive technology stack panel with organized groups.

Contract:
  --mock: Use static mock data (default True)
  --out PATH: Output SVG file path (default profile/tech.svg)
"""

import argparse
import os
import xml.dom.minidom
from typing import List, Tuple, Dict, Any
from theme import PALETTE, FONT, MONO, esc, card_frame, styles, title_row
from icons import ICONS


def measure_text_width(text: str, font_size: int = 13) -> float:
    """Rough estimate of text width in pixels (monospace ~7.2px per char at size 13)."""
    return len(text) * 7.2 * (font_size / 13)


def wrap_chips(
    chips: List[Tuple[str, str, str]],  # (name, icon_key, display_hex)
    max_width: int = 876,
    chip_padding: int = 16,
    gap: int = 8,
) -> List[List[Tuple[str, str, str]]]:
    """
    Wrap chips into rows based on available width.
    Returns list of rows, each row is list of (name, icon_key, display_hex).
    """
    rows = []
    current_row = []
    current_width = 0

    for chip in chips:
        name, icon_key, display_hex = chip
        # Estimate: icon (16px) + gap (4px) + text width + padding (16px) = total
        chip_width = 16 + 4 + measure_text_width(name, 13) + chip_padding

        if current_width + chip_width + gap <= max_width and current_row:
            current_row.append(chip)
            current_width += chip_width + gap
        elif current_row:
            rows.append(current_row)
            current_row = [chip]
            current_width = chip_width
        else:
            current_row = [chip]
            current_width = chip_width

    if current_row:
        rows.append(current_row)

    return rows


def render_chip(name: str, icon_key: str, display_hex: str, x: int, y: int) -> str:
    """Render a single technology chip with icon and label."""
    # Chip dimensions
    chip_height = 24
    chip_padding_h = 8
    text_width = measure_text_width(name, 13)
    chip_width = 16 + 4 + text_width + chip_padding_h

    # Get icon
    icon = ICONS.get(icon_key, {})
    icon_d = icon.get("d", "")
    icon_hex = icon.get("hex", "999999")
    if display_hex and display_hex != icon_hex:
        icon_hex = display_hex

    # Rounded rect background
    svg = f'<rect x="{x}" y="{y}" width="{chip_width}" height="{chip_height}" rx="12" fill="{PALETTE["bg_deep"]}" stroke="{PALETTE["border"]}" stroke-width="1"/>'

    # Icon (16x16, positioned at x+4)
    icon_x = x + 4
    icon_y = y + 4
    if icon_d:
        svg += f'<g transform="translate({icon_x},{icon_y}) scale(0.667)"><path d="{icon_d}" fill="#{icon_hex}"/></g>'

    # Text label
    text_x = x + 16 + 4 + 4  # icon + gap + padding
    text_y = y + 16  # vertical center
    svg += f'<text x="{text_x}" y="{text_y}" font-family="{FONT}" font-size="13" fill="{PALETTE["text"]}">{esc(name)}</text>'

    return svg


def render(data: dict, out_path: str) -> None:
    """
    Render tech SVG (orchestrator interface).

    Args:
        data: Shared data dict (unused for tech, always static)
        out_path: Path to write SVG file
    """
    generate_tech(out_path, mock=False)


def generate_tech(out_path: str, mock: bool = True) -> None:
    """
    Generate tech stack SVG with organized groups.

    Args:
        out_path: Path to write SVG file
        mock: Whether to use mock data (always True, static content)
    """

    # Tech stack organized by category
    tech_groups: Dict[str, List[Tuple[str, str, str]]] = {
        "Languages": [
            ("Python", "python", "3776AB"),
            ("TypeScript", "typescript", "3178C6"),
            ("JavaScript", "javascript", "F7DF1E"),
            ("Java", "openjdk", "437291"),
            ("SQL", "postgresql", "4169E1"),
        ],
        "Frontend": [
            ("React", "react", "61DAFB"),
            ("Next.js", "nextdotjs", "000000"),
            ("Vite", "vite", "646CFF"),
            ("Tailwind CSS", "tailwindcss", "06B6D4"),
        ],
        "Backend & APIs": [
            ("Node.js", "nodedotjs", "5FA04E"),
            ("Express", "express", "000000"),
            ("NestJS", "nestjs", "E0234E"),
            ("Flask", "flask", "000000"),
            ("FastAPI", "fastapi", "009688"),
            ("GraphQL", "graphql", "E10098"),
        ],
        "ML & Data": [
            ("PyTorch", "pytorch", "EE4C2C"),
            ("TensorFlow", "tensorflow", "FF6F00"),
            ("Scikit-learn", "scikitlearn", "F7931E"),
            ("OpenCV", "opencv", "5C3EE8"),
            ("Pandas", "pandas", "150458"),
            ("NumPy", "numpy", "013243"),
        ],
        "Databases & Cloud": [
            ("PostgreSQL", "postgresql", "4169E1"),
            ("MySQL", "mysql", "00758F"),
            ("MongoDB", "mongodb", "13AA52"),
            ("Prisma", "prisma", "2D3748"),
            ("Supabase", "supabase", "3ECF8E"),
            ("Redis", "redis", "DC382D"),
            ("Docker", "docker", "2496ED"),
            ("Railway", "railway", "0B0D0E"),
            ("Google Cloud", "googlecloud", "4285F4"),
            ("Git", "git", "F1502F"),
        ],
    }

    width = 920
    group_gap = 32
    section_gap = 16
    padding_x = 22
    padding_y = 22

    # Calculate total height — must mirror the render loop below exactly:
    # render starts at y=80; each group adds 18+section_gap for its label,
    # 32 per chip row, then (group_gap - section_gap) between groups.
    total_height = 80
    for group_name, chips in tech_groups.items():
        rows = wrap_chips(chips, width - padding_x * 2)
        total_height += 18 + section_gap + len(rows) * 32 + (group_gap - section_gap)
    total_height -= group_gap - section_gap  # no gap after the last group
    total_height += padding_y  # bottom padding

    # Create SVG
    svg_content = card_frame(width, total_height)

    # Add CSS for animations
    # Opacity-only animation: CSS transform keyframes would OVERRIDE the
    # transform attributes that position the icons (collapsing them to 0,0).
    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
g {
  animation: fadeIn 0.6s ease-out forwards;
}
"""
    for i in range(30):  # Support up to 30 groups/rows
        css += f"g:nth-child({i + 3}) {{ animation-delay: {(i - 2) * 80}ms; }}\n"

    svg_content += "\n" + styles(css)

    # Icon for title (circuit board icon using lambda-like shape)
    circuit_icon = "M12 2L4 6v12l8 4 8-4V6l-8-4zm0 2.5L16.5 8v8L12 18 7.5 16V8L12 4.5zm-2 5L12 11l2-1.5v3L12 15l-2-2.5v-3z"

    svg_content += "\n" + title_row(circuit_icon, "Tech Stack", 22, 40)

    # Render groups
    current_y = 80
    group_index = 0

    for group_name, chips in tech_groups.items():
        # Group label
        svg_content += f'\n<text x="{padding_x}" y="{current_y}" font-family="{FONT}" font-size="12" font-weight="600" fill="{PALETTE["muted"]}" text-transform="uppercase" letter-spacing="1">{esc(group_name)}</text>'
        current_y += 18 + section_gap

        # Wrap chips
        rows = wrap_chips(chips, width - padding_x * 2)

        # Render each row
        for row in rows:
            row_x = padding_x
            for name, icon_key, display_hex in row:
                chip_svg = render_chip(name, icon_key, display_hex, row_x, current_y)
                svg_content += f"\n{chip_svg}"

                # Estimate chip width for next position
                chip_width = 16 + 4 + measure_text_width(name, 13) + 8
                row_x += chip_width + 8  # 8px gap between chips

            current_y += 32  # chip height (24) + gap (8)

        current_y += group_gap - section_gap
        group_index += 1

    svg_content += "\n</svg>"

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
    except Exception as e:
        print(f"✗ XML validation failed: {e}")
        raise

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)

    # Write SVG
    with open(out_path, "w") as f:
        f.write(svg_content)

    print(f"✓ Tech stack SVG generated: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate tech stack SVG for GitHub profile")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock data (always True)")
    parser.add_argument("--out", type=str, default="profile/tech.svg", help="Output SVG file path")

    args = parser.parse_args()

    try:
        generate_tech(args.out, args.mock)
        print(f"✓ Successfully created {args.out}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
