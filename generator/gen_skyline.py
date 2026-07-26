#!/usr/bin/env python3
"""
Contribution Skyline card generator for GitHub profile.
Renders an isometric 3D visualization of the last 52 weeks of contributions.
Specs: 920x260, tokyonight design system with isometric towers.
"""

import argparse
import json
import os
import sys
import xml.dom.minidom
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from theme import PALETTE, FONT, MONO, card_frame, styles, title_row, esc, text_width
from data import load as load_data


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """Convert hex color to RGB tuple."""
    hex_color = hex_color.lstrip("#")
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def rgb_to_hex(rgb: Tuple[int, int, int]) -> str:
    """Convert RGB tuple to hex color."""
    return "#{:02x}{:02x}{:02x}".format(rgb[0], rgb[1], rgb[2])


def shade_color(hex_color: str, bg_color: str, factor: float) -> str:
    """
    Mix a color toward background for depth shading.
    factor=0: original color, factor=1: full bg_color
    """
    fg_rgb = hex_to_rgb(hex_color)
    bg_rgb = hex_to_rgb(bg_color)

    mixed = tuple(
        int(fg_rgb[i] * (1 - factor) + bg_rgb[i] * factor)
        for i in range(3)
    )
    return rgb_to_hex(mixed)


def aggregate_to_weeks(calendar: List[Dict[str, Any]]) -> List[int]:
    """
    Aggregate calendar data to weekly contributions.
    Returns list of 52 weekly totals, ending this week.
    """
    if not calendar:
        return [0] * 52

    # Get today's date and find 52 weeks back
    today = datetime.now().date()

    # Convert calendar to dict for fast lookup
    cal_dict = {d["date"]: d["count"] for d in calendar}

    # Aggregate by week (Monday-Sunday)
    weeks = []
    current_date = today - timedelta(weeks=51)  # 52 weeks back from today

    for _ in range(52):
        week_start = current_date
        week_end = week_start + timedelta(days=6)

        # Sum contributions for this week
        week_total = 0
        check_date = week_start
        while check_date <= week_end:
            date_str = check_date.isoformat()
            if date_str in cal_dict:
                week_total += cal_dict[date_str]
            check_date += timedelta(days=1)

        weeks.append(week_total)
        current_date = week_end + timedelta(days=1)

    return weeks


def get_month_labels(weeks_count: int = 52) -> Dict[int, str]:
    """
    Get month label positions for x-axis.
    Returns dict of {week_index: month_name}.
    """
    today = datetime.now().date()
    labels = {}

    # Track which months we've already labeled
    labeled_months = set()

    for week_idx in range(weeks_count):
        week_start = today - timedelta(weeks=weeks_count - 1 - week_idx)
        month_key = (week_start.year, week_start.month)

        # Label the first week of each month
        if month_key not in labeled_months:
            labels[week_idx] = week_start.strftime("%b")
            labeled_months.add(month_key)

    return labels


def render_isometric_tower(
    x_pos: float,
    y_base: float,
    width: float,
    height: float,
    color: str,
    is_peak: bool = False,
    value: int = 0
) -> str:
    """
    Render an isometric 3D tower (rhombus top + two visible faces).

    Args:
        x_pos: X position of tower base (left edge)
        y_base: Y position of baseline
        width: Tower width in pixels
        height: Tower height in pixels (clamped to min 3px for baseline)
        color: Tower base color (will be shaded for faces)
        is_peak: If True, use orange glow effect instead of shading

    Returns:
        SVG fragment for the tower
    """
    min_height = 3  # Minimum visible height for empty weeks
    if height < min_height:
        height = min_height

    # Isometric projection: 30° angle
    # Tower dimensions
    tower_width = width
    tower_depth = width * 0.6  # Depth is slightly less than width for visual balance
    iso_angle = 30  # degrees

    # Calculate 3D coordinates (using simple isometric projection)
    # Top of tower: front-left, front-right, back-right, back-left
    # Height in isometric view
    iso_height = height * 0.8

    # Tower base (on ground plane)
    base_x = x_pos
    base_y = y_base

    # Front face corners (facing viewer)
    front_left_x = base_x
    front_left_y = base_y
    front_right_x = base_x + tower_width
    front_right_y = base_y

    # Top corners (projected up and back)
    top_left_x = base_x + tower_depth * 0.5
    top_left_y = base_y - iso_height
    top_right_x = base_x + tower_width + tower_depth * 0.5
    top_right_y = base_y - iso_height

    # Back face corners
    back_left_x = base_x + tower_depth * 0.5
    back_left_y = base_y - tower_depth * 0.3
    back_right_x = base_x + tower_width + tower_depth * 0.5
    back_right_y = base_y - tower_depth * 0.3

    svg = '<g class="tower tower-{}">'.format(int(x_pos))

    if is_peak:
        # Peak tower: orange, with a small value label above it (halo circles
        # read as a solid ball in some renderers — a labeled tower is clearer)
        peak_color = PALETTE["orange"]

        label_x = (front_left_x + front_right_x) / 2
        label_y = top_left_y - 8
        if label_y > 46:  # keep clear of the title row when the tower is tall
            svg += f'\n  <text x="{label_x:.1f}" y="{label_y:.1f}" font-family="{FONT}" font-size="11" font-weight="600" fill="{peak_color}" text-anchor="middle">{value}</text>'

        # Front face (mid orange)
        front_color = peak_color
        svg += f'\n  <polygon points="{front_left_x:.1f},{front_left_y:.1f} '
        svg += f'{front_right_x:.1f},{front_right_y:.1f} '
        svg += f'{top_right_x:.1f},{top_right_y:.1f} '
        svg += f'{top_left_x:.1f},{top_left_y:.1f}" '
        svg += f'fill="{front_color}" stroke="{PALETTE["border"]}" stroke-width="0.5" opacity="0.9"/>'

        # Right face (darker orange)
        right_color = shade_color(peak_color, PALETTE["bg"], 0.3)
        svg += f'\n  <polygon points="{front_right_x:.1f},{front_right_y:.1f} '
        svg += f'{back_right_x:.1f},{back_right_y:.1f} '
        svg += f'{top_right_x:.1f},{top_right_y:.1f} '
        svg += f'{top_right_x - tower_depth * 0.5:.1f},{top_right_y + tower_depth * 0.3:.1f}" '
        svg += f'fill="{right_color}" stroke="{PALETTE["border"]}" stroke-width="0.5" opacity="0.85"/>'

        # Top face (lightest orange)
        top_color = shade_color(peak_color, "#ffffff", 0.4)
        svg += f'\n  <polygon points="{top_left_x:.1f},{top_left_y:.1f} '
        svg += f'{top_right_x:.1f},{top_right_y:.1f} '
        svg += f'{top_right_x - tower_depth * 0.5:.1f},{top_right_y + tower_depth * 0.3:.1f} '
        svg += f'{top_left_x - tower_depth * 0.5:.1f},{top_left_y + tower_depth * 0.3:.1f}" '
        svg += f'fill="{top_color}" stroke="{PALETTE["border"]}" stroke-width="0.5" opacity="0.95"/>'
    else:
        # Regular tower: blue with shading
        # Front face (mid shade)
        front_color = shade_color(color, PALETTE["bg"], 0.2)
        svg += f'\n  <polygon points="{front_left_x:.1f},{front_left_y:.1f} '
        svg += f'{front_right_x:.1f},{front_right_y:.1f} '
        svg += f'{top_right_x:.1f},{top_right_y:.1f} '
        svg += f'{top_left_x:.1f},{top_left_y:.1f}" '
        svg += f'fill="{front_color}" stroke="{PALETTE["border"]}" stroke-width="0.5"/>'

        # Right face (darker)
        right_color = shade_color(color, PALETTE["bg"], 0.4)
        svg += f'\n  <polygon points="{front_right_x:.1f},{front_right_y:.1f} '
        svg += f'{back_right_x:.1f},{back_right_y:.1f} '
        svg += f'{top_right_x:.1f},{top_right_y:.1f} '
        svg += f'{top_right_x - tower_depth * 0.5:.1f},{top_right_y + tower_depth * 0.3:.1f}" '
        svg += f'fill="{right_color}" stroke="{PALETTE["border"]}" stroke-width="0.5"/>'

        # Top face (lightest - barely visible)
        top_color = shade_color(color, "#ffffff", 0.5)
        svg += f'\n  <polygon points="{top_left_x:.1f},{top_left_y:.1f} '
        svg += f'{top_right_x:.1f},{top_right_y:.1f} '
        svg += f'{top_right_x - tower_depth * 0.5:.1f},{top_right_y + tower_depth * 0.3:.1f} '
        svg += f'{top_left_x - tower_depth * 0.5:.1f},{top_left_y + tower_depth * 0.3:.1f}" '
        svg += f'fill="{top_color}" stroke="{PALETTE["border"]}" stroke-width="0.5"/>'

    svg += '\n</g>'
    return svg


def render(data: Dict[str, Any], out_path: str) -> None:
    """
    Render skyline SVG (orchestrator interface).

    Args:
        data: Shared data dict from data.load()
        out_path: Path to write SVG file
    """
    svg_content = generate_skyline_svg(data)

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


def generate_skyline_svg(data: Dict[str, Any]) -> str:
    """
    Generate skyline card SVG.

    Args:
        data: dict from data.load() containing calendar

    Returns:
        SVG string
    """
    width, height = 920, 260

    # Extract and aggregate calendar data
    calendar = data.get("calendar", [])
    weeks = aggregate_to_weeks(calendar)

    # Calculate total contributions for caption
    total_contributions = sum(weeks)

    # Normalize weeks to heights
    max_week = max(weeks) if weeks else 1
    if max_week == 0:
        max_week = 1
    max_height = 150  # Maximum tower height in pixels

    # Calculate tower dimensions
    tower_width = 13  # Width of each tower
    spacing = 2  # Space between towers
    tower_step = tower_width + spacing

    # Layout: title at top (30px), chart area below
    title_y = 30
    baseline_y = 210  # Y position of baseline

    # CSS animations: opacity-only staggered fade-in
    css = """
@keyframes fadeInTower {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.tower {
  animation: fadeInTower 0.4s ease-out forwards;
}
"""

    # Add staggered delays for each tower
    for i in range(52):
        delay_ms = i * 20  # 20ms per tower
        css += f"\n.tower-{int(tower_step * i)} {{ animation-delay: {delay_ms}ms; }}"

    # Start SVG
    svg = card_frame(width, height)
    svg += "\n" + styles(css)

    # Title row with city/building icon
    city_icon = "M12 2c-1.1 0-2 .9-2 2v14h4V4c0-1.1-.9-2-2-2zm-4 4c-1.1 0-2 .9-2 2v10h4V8c0-1.1-.9-2-2-2zm8-2c-1.1 0-2 .9-2 2v12h4V4c0-1.1-.9-2-2-2z"
    svg += "\n" + title_row(city_icon, "Contribution Skyline", x=22, y=30)

    # Draw towers
    x_offset = 22
    for week_idx, week_count in enumerate(weeks):
        x_pos = x_offset + week_idx * tower_step

        # Scale height
        tower_height = (week_count / max_week) * max_height if max_week > 0 else 0

        # Check if this is the peak week
        is_peak = week_count == max_week and max_week > 0

        tower_svg = render_isometric_tower(
            x_pos,
            baseline_y,
            tower_width,
            tower_height,
            PALETTE["blue"],
            is_peak=is_peak,
            value=week_count
        )
        svg += "\n" + tower_svg

    # Draw baseline
    baseline_start_x = x_offset
    baseline_end_x = x_offset + 51 * tower_step + tower_width
    svg += f'\n<line x1="{baseline_start_x:.1f}" y1="{baseline_y:.1f}" x2="{baseline_end_x:.1f}" y2="{baseline_y:.1f}" stroke="{PALETTE["border"]}" stroke-width="1"/>'

    # Draw month labels below baseline
    month_labels = get_month_labels(52)
    for week_idx, month_name in month_labels.items():
        x_pos = x_offset + week_idx * tower_step + tower_width / 2
        svg += f'\n<text x="{x_pos:.1f}" y="{baseline_y + 20}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}" text-anchor="middle">{esc(month_name)}</text>'

    # Right-aligned caption — top-right, opposite the title, clear of the
    # month labels along the baseline
    caption = f"{total_contributions:,} contributions · last 52 weeks"
    caption_x = width - 22
    svg += f'\n<text x="{caption_x}" y="36" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}" text-anchor="end">{esc(caption)}</text>'

    # Close SVG
    svg += "\n</svg>"

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate Contribution Skyline SVG card")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/skyline.svg",
        help="Output SVG file path",
    )
    args = parser.parse_args()

    # Load data
    data = load_data(mock=args.mock)

    # Generate SVG
    svg_content = generate_skyline_svg(data)

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

    print(f"✓ Skyline SVG written to {args.out}")

    # Return result JSON
    result = {
        "module": "skyline",
        "files": [args.out],
        "ok": True,
        "visual_notes": "Generated isometric 3D contribution skyline with 52 weekly towers, staggered fade-in animation, peak week in orange with glow, month labels, and contribution caption.",
    }
    print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
