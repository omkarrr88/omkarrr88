#!/usr/bin/env python3
"""
Weekly Rhythm card generator for GitHub profile.
Displays: Contribution distribution across weekdays (Mon-Sun) as vertical bars.
Most active day highlighted in orange.
Specs: 452x210, tokyonight design system.
"""

import argparse
import os
import sys
import xml.dom.minidom
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, Any, List

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from theme import PALETTE, FONT, esc, card_frame, styles, title_row, text_width
from data import load as load_data


def get_weekday_contributions(calendar: List[Dict[str, Any]]) -> Dict[int, int]:
    """
    Sum contributions per weekday from the last 182 days (26 weeks).

    Args:
        calendar: List of {date, count} entries from data.load()

    Returns:
        Dict mapping weekday (0=Monday, 6=Sunday) to total count
    """
    # Extract last 182 days
    today = datetime.now().date()
    cutoff_date = today - timedelta(days=181)  # 182 days including today

    calendar_dict = {}
    for entry in calendar:
        entry_date = datetime.fromisoformat(entry["date"]).date()
        if entry_date >= cutoff_date:
            calendar_dict[entry["date"]] = entry.get("count", 0)

    # Sum by weekday: Monday=0, Sunday=6
    weekday_counts = {i: 0 for i in range(7)}

    for date_str, count in calendar_dict.items():
        entry_date = datetime.fromisoformat(date_str).date()
        weekday = entry_date.weekday()  # 0=Monday, 6=Sunday
        weekday_counts[weekday] += count

    return weekday_counts


def render(data: dict, out_path: str) -> None:
    """
    Render weekday rhythm SVG (orchestrator interface).

    Args:
        data: Shared data dict from data.load()
        out_path: Path to write SVG file
    """
    svg_content = generate_weekday_svg(data)

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


def generate_weekday_svg(data: dict) -> str:
    """
    Generate weekly rhythm card SVG.

    Args:
        data: dict from data.load() containing calendar

    Returns:
        SVG string
    """
    width, height = 452, 210

    # Extract calendar data
    calendar = data.get("calendar", [])
    weekday_counts = get_weekday_contributions(calendar)

    # Find max count (for scaling)
    max_count = max(weekday_counts.values()) if weekday_counts else 1
    if max_count == 0:
        max_count = 1  # Prevent division by zero

    # Find day with most contributions
    most_active_day = max(weekday_counts.items(), key=lambda x: x[1])[0]

    # Weekday labels
    weekday_labels = ["M", "T", "W", "T", "F", "S", "S"]
    weekday_names = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

    # CSS animations: opacity fade-in for bars
    css = """
@keyframes fadeIn {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}

.bar {
  animation: fadeIn 0.8s ease-out forwards;
}
"""

    # Start SVG
    svg = card_frame(width, height)
    svg += "\n" + styles(css)

    # Calendar icon (simple grid pattern)
    calendar_icon = "M19 3h-1V1h-2v2H8V1H6v2H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm0 16H5V8h14v11z"

    svg += "\n" + title_row(calendar_icon, "Weekly Rhythm")

    # Layout constants
    inner_width = 408  # Total width - 22px padding on each side
    inner_height = 105  # Max bar height
    bar_width = 48  # Width of each bar (including gap)
    bar_actual_width = 38  # Visual width of bar
    start_x = 22  # Left padding
    bar_y_baseline = 165  # Y position where bars touch
    label_y = 185  # Y position for weekday labels

    # Draw bars
    for day in range(7):
        count = weekday_counts.get(day, 0)

        # Calculate bar height: proportional to count, min 3px
        if count == 0:
            bar_height = 3
        else:
            bar_height = max(3, (count / max_count) * inner_height)

        # Calculate bar x position
        bar_x = start_x + (day * bar_width) + (bar_width - bar_actual_width) / 2
        bar_top = bar_y_baseline - bar_height

        # Determine color: orange for most active, blue otherwise
        bar_color = PALETTE["orange"] if day == most_active_day else PALETTE["blue"]

        # Draw rounded bar (animation handles opacity)
        animation_delay = day * 80
        base_y = bar_top + bar_height
        begin_s = animation_delay / 1000
        svg += (
            f'\n<rect class="bar" style="animation-delay: {animation_delay}ms" x="{bar_x}" y="{bar_top}" width="{bar_actual_width}" height="{bar_height}" rx="3" fill="{bar_color}">'
            f'\n  <animate attributeName="height" from="0" to="{bar_height}" dur="0.7s" begin="{begin_s:.2f}s" fill="freeze"/>'
            f'\n  <animate attributeName="y" from="{base_y}" to="{bar_top}" dur="0.7s" begin="{begin_s:.2f}s" fill="freeze"/>'
            f'\n</rect>'
        )

        # Draw weekday label
        label_x = bar_x + bar_actual_width / 2
        svg += f'\n<text x="{label_x}" y="{label_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}" text-anchor="middle">{esc(weekday_labels[day])}</text>'

        # Draw count above bar for most active day
        if day == most_active_day:
            count_y = bar_top - 8
            svg += f'\n<text x="{label_x}" y="{count_y}" font-family="{FONT}" font-size="11" font-weight="600" fill="{PALETTE["orange"]}" text-anchor="middle">{esc(str(weekday_counts[day]))}</text>'

    # Caption: "Most active: <Weekday>" using two text elements for reliability
    caption_y = 200
    svg += f'\n<text x="22" y="{caption_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}">Most active: </text>'
    # Calculate width of "Most active: " to position weekday name after it
    prefix_width = text_width("Most active: ", 11)
    svg += f'\n<text x="{22 + prefix_width}" y="{caption_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["orange"]}">{esc(weekday_names[most_active_day])}</text>'

    # Close SVG
    svg += "\n</svg>"

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate Weekly Rhythm SVG card")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/weekday.svg",
        help="Output SVG file path",
    )
    args = parser.parse_args()

    # Load data
    data = load_data(mock=args.mock)

    # Generate SVG
    svg_content = generate_weekday_svg(data)

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

    print(f"✓ Weekly Rhythm SVG written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
