#!/usr/bin/env python3
"""
Projects SVG generator for GitHub profile.
Creates individual project cards with consistent design.

Contract:
  Generates 6 project cards (452x150 each):
  - chakravyuh, smart-puc, v2v, movie-recommender, face-attendance, fitness-tracker
  Each card: accent bar + name + description (wrapped) + tech chips
  --mock: Use static mock data (default True)
  --out PATH: Output SVG file path (pattern: profile/project-{name}.svg)
"""

import argparse
import os
import xml.dom.minidom
from typing import List, Tuple
from theme import PALETTE, FONT, MONO, esc, card_frame, styles, text_width as theme_text_width
from icons import ICONS


def wrap_text(text: str, max_width: int = 62, font_size: float = 12.5) -> List[str]:
    """Wrap text to fit max width in characters. Returns list of lines."""
    words = text.split()
    lines = []
    current_line = []
    current_length = 0

    for word in words:
        word_len = len(word)
        if current_length + word_len + 1 <= max_width:
            current_line.append(word)
            current_length += word_len + 1
        else:
            if current_line:
                lines.append(" ".join(current_line))
            current_line = [word]
            current_length = word_len

    if current_line:
        lines.append(" ".join(current_line))

    if len(lines) > 2:  # truncate with ellipsis rather than cutting silently
        lines = [lines[0], lines[1].rstrip(".,;") + "…"]
    return lines


def render_tech_chips(
    chips: List[Tuple[str, str, str]],  # (name, icon_key, is_text_chip)
    x: int,
    y: int,
    max_chips: int = 3,
) -> Tuple[str, int]:
    """
    Render mini tech chips (up to 3).
    Returns (svg_string, max_x_used).
    """
    svg = ""
    current_x = x
    chip_height = 18
    padding = 6

    for i, (name, icon_key, is_text) in enumerate(chips[:max_chips]):
        if is_text:
            # Text-only chip (no icon)
            text_width = theme_text_width(name, 11) + padding * 2
            svg += f'<rect x="{current_x}" y="{y}" width="{text_width}" height="{chip_height}" rx="9" fill="{PALETTE["bg_deep"]}" stroke="{PALETTE["border"]}" stroke-width="0.5"/>'
            text_x = current_x + padding
            text_y = y + 13
            svg += f'<text x="{text_x}" y="{text_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["text"]}">{esc(name)}</text>'
            current_x += text_width + 6  # 6px gap
        else:
            # Icon + text chip
            icon = ICONS.get(icon_key, {})
            icon_d = icon.get("d", "")
            icon_hex = icon.get("hex", "999999")

            text_width = theme_text_width(name, 11) + 20  # icon (12px) + gap (2px) + text + padding
            chip_width = 12 + 2 + text_width + padding

            svg += f'<rect x="{current_x}" y="{y}" width="{chip_width}" height="{chip_height}" rx="9" fill="{PALETTE["bg_deep"]}" stroke="{PALETTE["border"]}" stroke-width="0.5"/>'

            # Icon (12x12)
            if icon_d:
                icon_x = current_x + padding
                icon_y = y + 3
                svg += f'<g transform="translate({icon_x},{icon_y}) scale(0.5)"><path d="{icon_d}" fill="#{icon_hex}"/></g>'

            # Text
            text_x = current_x + 12 + 2 + padding
            text_y = y + 13
            svg += f'<text x="{text_x}" y="{text_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["text"]}">{esc(name)}</text>'

            current_x += chip_width + 6  # 6px gap

    return svg, current_x


def generate_project_card(
    name: str,
    title: str,
    description: str,
    tech_chips: List[Tuple[str, str, bool]],  # (name, icon_key, is_text)
    accent_color: str,
    out_path: str,
) -> None:
    """
    Generate a single project card SVG.

    Args:
        name: Project slug/key (e.g., "chakravyuh")
        title: Project display name
        description: Project description (will be wrapped)
        tech_chips: List of (name, icon_key, is_text_chip)
        accent_color: Hex color for left accent bar
        out_path: Output file path
    """
    width, height = 452, 150

    # Create SVG
    svg_content = card_frame(width, height)

    # CSS animations
    # Opacity-only: transform keyframes would override the transform
    # attributes that position the mini chip icons (collapsing them to 0,0).
    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
g {
  animation: fadeIn 0.6s ease-out forwards;
}
"""
    svg_content += "\n" + styles(css)

    # Left accent bar (4px)
    svg_content += f'\n<rect x="0.5" y="0.5" width="4" height="{height - 1}" fill="#{accent_color}" rx="10" ry="0"/>'

    # Wrapping content group
    svg_content += '\n<g>'

    # Title (16px, 600 weight, accent color)
    svg_content += f'\n<text x="22" y="38" font-family="{FONT}" font-size="16" font-weight="600" fill="#{accent_color}">{esc(title)}</text>'

    # Description (wrapped, 12.5px, text color)
    description_lines = wrap_text(description, max_width=62)
    for i, line in enumerate(description_lines):
        y_offset = 58 + (i * 16)
        svg_content += f'\n<text x="22" y="{y_offset}" font-family="{FONT}" font-size="12.5" fill="{PALETTE["text"]}">{esc(line)}</text>'

    # Tech chips at bottom (max 3)
    if tech_chips:
        chips_svg, _ = render_tech_chips(tech_chips, 22, height - 28)
        svg_content += f"\n{chips_svg}"

    svg_content += '\n</g>'

    svg_content += "\n</svg>"

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
    except Exception as e:
        print(f"✗ XML validation failed for {name}: {e}")
        raise

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)

    # Write SVG
    with open(out_path, "w") as f:
        f.write(svg_content)

    print(f"✓ Project card generated: {out_path}")


def render_all(data: dict, base_out_dir: str = "profile") -> None:
    """
    Render all project cards (orchestrator interface).

    Args:
        data: Shared data dict (unused for projects, always static)
        base_out_dir: Base output directory for all project files
    """
    generate_all_projects(base_out_dir, mock=False)


def generate_all_projects(base_out_dir: str = "profile", mock: bool = True) -> None:
    """Generate all 6 project cards."""

    projects = [
        (
            "chakravyuh",
            "Chakravyuh",
            "Multi-agent RL environment for UPI fraud detection. 7th of 31,000+ teams at the Meta PyTorch Hackathon.",
            [("PyTorch", "pytorch", False), ("FastAPI", "fastapi", False), ("LoRA", "python", True)],
            "7aa2f7",  # blue
        ),
        (
            "smart-puc",
            "Smart PUC",
            "Blockchain vehicle-emission monitoring with signed OBD telemetry, on-chain records and NFT certificates.",
            [("Solidity", "solidity", False), ("FastAPI", "fastapi", False), ("Web3.py", "python", True)],
            "bb9af7",  # purple
        ),
        (
            "v2v",
            "V2V Communication",
            "Vehicle-to-vehicle blind-spot detection and accident prevention. Paper under review at Springer Nature.",
            [("Python", "python", False), ("IoT", "python", True), ("Simulation", "python", True)],
            "73daca",  # teal
        ),
        (
            "movie-recommender",
            "Movie Recommender",
            "Collaborative-filtering recommender with NLTK sentiment analysis. React front-end, Flask back-end.",
            [("Python", "python", False), ("Flask", "flask", False), ("React", "react", False)],
            "ff9e64",  # orange
        ),
        (
            "face-attendance",
            "Face Recognition Attendance",
            "Marks attendance from a camera feed with face recognition; records in MySQL, exported reports.",
            [("OpenCV", "opencv", False), ("Python", "python", False), ("MySQL", "mysql", False)],
            "9ece6a",  # green
        ),
        (
            "fitness-tracker",
            "Fitness Tracker",
            "Diet, sleep and workout logging with BMI calculator and Chart.js progress analytics.",
            [("JavaScript", "javascript", False), ("Chart.js", "javascript", True), ("HTML5", "javascript", True)],
            "7dcfff",  # cyan
        ),
    ]

    for project_key, title, desc, chips, color in projects:
        out_path = os.path.join(base_out_dir, f"project-{project_key}.svg")
        generate_project_card(project_key, title, desc, chips, color, out_path)


def main():
    parser = argparse.ArgumentParser(description="Generate project card SVGs for GitHub profile")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock data (always True)")
    parser.add_argument(
        "--out",
        type=str,
        default="profile",
        help="Output directory (files named project-{name}.svg)",
    )

    args = parser.parse_args()

    try:
        generate_all_projects(args.out, args.mock)
        print(f"✓ Successfully created all project cards in {args.out}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
