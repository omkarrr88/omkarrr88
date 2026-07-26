#!/usr/bin/env python3
"""
Activity visualization generator for GitHub profile.
Generates a 920x240 contribution activity area chart for the last 26 weeks.
"""

import argparse
import json
import math
import os
import xml.dom.minidom
from datetime import datetime, timedelta
from typing import Dict, List, Any, Tuple

from theme import PALETTE, FONT, MONO, card_frame, styles, title_row, esc
from data import load


# SVG chart dimensions and margins
CHART_WIDTH = 920
CHART_HEIGHT = 240
MARGIN_LEFT = 60
MARGIN_RIGHT = 20
MARGIN_TOP = 60
MARGIN_BOTTOM = 40
PLOT_WIDTH = CHART_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_HEIGHT = CHART_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM


def aggregate_to_weeks(calendar: List[Dict[str, Any]]) -> List[Tuple[str, int]]:
    """
    Aggregate calendar data to weekly contributions.
    Returns list of (week_start_date, total_count) for last 26 weeks.
    """
    if not calendar:
        return []

    # Get today's date and find 26 weeks back
    today = datetime.now().date()
    weeks_back = today - timedelta(weeks=26)

    # Convert calendar to dict for fast lookup
    cal_dict = {d["date"]: d["count"] for d in calendar}

    # Aggregate by week (Sunday to Saturday)
    weeks = []
    current_date = weeks_back

    while current_date <= today:
        # Start of week (Monday)
        week_start = current_date
        week_end = week_start + timedelta(days=6)

        # Sum contributions for this week
        week_total = 0
        check_date = week_start
        while check_date <= week_end and check_date <= today:
            date_str = check_date.isoformat()
            if date_str in cal_dict:
                week_total += cal_dict[date_str]
            check_date += timedelta(days=1)

        weeks.append((week_start.isoformat(), week_total))
        current_date = week_end + timedelta(days=1)

    return weeks


def get_month_boundaries(weeks: List[Tuple[str, int]]) -> Dict[str, int]:
    """
    Get month boundaries for x-axis labels.
    Returns dict of {month_name: week_index_for_first_occurrence}.
    """
    boundaries = {}

    for idx, (date_str, _) in enumerate(weeks):
        date_obj = datetime.fromisoformat(date_str).date()
        month_key = date_obj.strftime("%b")  # "Jan", "Feb", etc.

        # Record first occurrence of each month
        if month_key not in boundaries:
            boundaries[month_key] = idx

    return boundaries


def scale_value(value: int, min_val: int, max_val: int, height: float) -> float:
    """Scale a value to SVG y-coordinate (inverted for SVG)."""
    if max_val == min_val:
        return height / 2
    scaled = (value - min_val) / (max_val - min_val)
    return height * (1 - scaled)  # Inverted for SVG


def cubic_spline_points(
    values: List[int], width: float, height: float, min_val: int, max_val: int
) -> List[Tuple[float, float]]:
    """
    Generate cubic spline points for smooth area chart.
    Returns list of (x, y) coordinate tuples.
    """
    n = len(values)
    if n < 2:
        return []

    points = []
    x_step = width / (n - 1) if n > 1 else 0

    for i, val in enumerate(values):
        x = i * x_step
        y = scale_value(val, min_val, max_val, height)
        points.append((x, y))

    return points


def generate_cubic_path(points: List[Tuple[float, float]]) -> str:
    """
    Generate SVG path from points using straight lines.
    Simple and reliable rendering across all SVG renderers.
    """
    if len(points) < 2:
        return ""

    path_parts = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]

    # Connect points with straight lines (still looks smooth with many points)
    for i in range(1, len(points)):
        x, y = points[i]
        path_parts.append(f"L {x:.1f} {y:.1f}")

    return " ".join(path_parts)


def render(data: Dict[str, Any], output_path: str) -> None:
    """
    Render activity SVG (orchestrator interface).

    Args:
        data: Shared data dict from data.load()
        output_path: Path to write SVG file
    """
    generate_svg(data, output_path)


def generate_svg(data: Dict[str, Any], output_path: str) -> None:
    """Generate activity chart SVG and write to file."""

    # Extract calendar and aggregate to weeks
    calendar = data.get("calendar", [])
    weeks = aggregate_to_weeks(calendar)

    if not weeks:
        # Fallback: create empty chart
        weeks = [(datetime.now().date().isoformat(), 0) for _ in range(26)]

    # Extract values
    values = [count for _, count in weeks]
    min_val = min(values) if values else 0
    max_val = max(values) if values else 1

    # Ensure we have a range for visualization
    if max_val == min_val:
        max_val = max_val + 1

    # Generate cubic spline points
    points = cubic_spline_points(values, PLOT_WIDTH, PLOT_HEIGHT, min_val, max_val)

    # Generate area path (line + bottom closure)
    line_path = generate_cubic_path(points)
    if points:
        area_path = (
            line_path
            + f" L {points[-1][0]:.1f} {PLOT_HEIGHT:.1f}"
            + f" L {points[0][0]:.1f} {PLOT_HEIGHT:.1f}"
            + " Z"
        )
    else:
        area_path = ""

    # Find peak week (true max, not the range-adjusted max_val)
    peak_value = max(values) if values else 0
    peak_idx = values.index(peak_value) if values else 0
    peak_x = (
        peak_idx * (PLOT_WIDTH / (len(values) - 1)) if len(values) > 1 else PLOT_WIDTH / 2
    )
    peak_y = scale_value(peak_value, min_val, max_val, PLOT_HEIGHT)

    # Get month boundaries
    month_boundaries = get_month_boundaries(weeks)

    # Start building SVG
    svg_content = card_frame(CHART_WIDTH, CHART_HEIGHT)

    # CSS animations - simplified for better compatibility
    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.chart-container {
  animation: fadeIn 0.6s ease-out forwards;
}
"""

    svg_content += "\n" + styles(css)

    # Add title row
    # Simple chart icon (ascending bars)
    chart_icon = "M2 18h4v-8H2v8zm6-11h4V3h-4v4zm6 0h4V5h-4v2z"
    svg_content += "\n" + title_row(chart_icon, "Contribution Activity", x=22, y=30)

    # Main chart group
    svg_content += '\n<g class="chart-container" transform="translate({},{})">'.format(
        MARGIN_LEFT, MARGIN_TOP
    )

    # Draw horizontal gridlines
    num_gridlines = 4
    for i in range(num_gridlines + 1):
        y = (i / num_gridlines) * PLOT_HEIGHT
        svg_content += (
            f'\n  <line x1="0" y1="{y:.1f}" x2="{PLOT_WIDTH:.1f}" y2="{y:.1f}" '
            f'stroke="{PALETTE["border"]}" stroke-width="1" opacity="0.5"/>'
        )

        # Y-axis label
        label_value = int(max_val - (i / num_gridlines) * (max_val - min_val))
        svg_content += (
            f'\n  <text x="-10" y="{y + 4:.1f}" font-family="{FONT}" font-size="11" '
            f'fill="{PALETTE["muted"]}" text-anchor="end">{label_value}</text>'
        )


    # Draw area path with solid fill (gradient removed for better compatibility)
    if area_path:
        svg_content += (
            f'\n  <path d="{area_path}" fill="{PALETTE["blue"]}" '
            f'fill-opacity="0.15" stroke="none"/>'
        )

        # Draw line on top of area
        svg_content += (
            f'\n  <path id="activity-line" d="{line_path}" '
            f'stroke="{PALETTE["blue"]}" stroke-width="2" fill="none" '
            f'stroke-linecap="round" stroke-linejoin="round"/>'
        )

        # Live pulse: a glowing dot rides the contribution line forever
        # (SMIL animateMotion — attribute-based, safe alongside CSS rules)
        svg_content += (
            f'\n  <circle r="6" fill="{PALETTE["purple"]}" opacity="0.25">'
            f'\n    <animateMotion dur="8s" repeatCount="indefinite"><mpath href="#activity-line"/></animateMotion>'
            f'\n  </circle>'
            f'\n  <circle r="3" fill="{PALETTE["purple"]}">'
            f'\n    <animateMotion dur="8s" repeatCount="indefinite"><mpath href="#activity-line"/></animateMotion>'
            f'\n  </circle>'
        )

    # Draw dots for each week
    for i, (_, value) in enumerate(weeks):
        if i < len(points):
            x, y = points[i]
            svg_content += (
                f'\n  <circle cx="{x:.1f}" cy="{y:.1f}" r="3" '
                f'fill="{PALETTE["purple"]}" class="dot dot-{i}"/>'
            )

    # Draw peak week annotation
    if peak_value > 0:
        peak_label_x = peak_x + 15
        peak_label_y = peak_y - 10

        # Peak value tag background
        svg_content += (
            f'\n  <rect x="{peak_label_x - 15:.1f}" y="{peak_label_y - 12:.1f}" '
            f'width="40" height="20" rx="3" fill="{PALETTE["teal"]}" opacity="0.9"/>'
        )

        # Peak value text (using bg color for contrast on teal background)
        svg_content += (
            f'\n  <text x="{peak_label_x + 2:.1f}" y="{peak_label_y:.1f}" '
            f'font-family="{FONT}" font-size="11" font-weight="600" '
            f'fill="{PALETTE["bg"]}" text-anchor="middle">{int(peak_value)}</text>'
        )

    # Draw X-axis month labels
    for month, week_idx in sorted(month_boundaries.items(), key=lambda x: x[1]):
        if week_idx < len(points):
            x = points[week_idx][0]
            svg_content += (
                f'\n  <text x="{x:.1f}" y="{PLOT_HEIGHT + 20:.1f}" '
                f'font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}" '
                f'text-anchor="middle">{month}</text>'
            )

    svg_content += "\n</g>\n</svg>"

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
    except Exception as e:
        print(f"XML validation failed: {e}")
        exit(1)

    # Ensure output directory exists
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    # Write SVG
    with open(output_path, "w") as f:
        f.write(svg_content)

    print(f"✓ Activity SVG written to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate activity visualization")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/activity.svg",
        help="Output SVG path",
    )
    args = parser.parse_args()

    # Load data
    data = load(mock=args.mock)

    # Generate SVG
    generate_svg(data, args.out)

    # Return result JSON
    result = {
        "module": "activity",
        "files": [args.out],
        "ok": True,
        "visual_notes": "Generated 26-week contribution activity chart with smooth area line, weekly dots, gridlines, and peak annotation.",
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
