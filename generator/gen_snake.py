#!/usr/bin/env python3
"""
Animated contribution snake generator for GitHub profile.
Generates a 920x240 serpentine snake traversing a 52-week x 7-day contribution grid.
Uses SMIL animations for motion and cell "eating" effects.
"""

import argparse
import json
import math
import os
import sys
import xml.dom.minidom
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Tuple

sys.path.insert(0, str(Path(__file__).parent))

from theme import PALETTE, FONT, MONO, card_frame, styles, title_row, esc
from data import load


# SVG dimensions
CARD_WIDTH = 920
CARD_HEIGHT = 172

# Grid dimensions
WEEKS = 52
DAYS = 7

# Cell sizing
CELL_SIZE = 12
CELL_GAP = 3
CELL_RX = 2.5

# Grid positioning (centered in card with margins)
GRID_MARGIN_LEFT = 68
GRID_MARGIN_TOP = 22
GRID_MARGIN_BOTTOM = 40

# Snake parameters
SNAKE_SEGMENTS = 7
SNAKE_HEAD_SCALE = 1.2  # Head slightly larger
SNAKE_ANIMATION_DURATION = 26  # seconds

# Total grid dimensions
GRID_WIDTH = WEEKS * (CELL_SIZE + CELL_GAP) + CELL_GAP
GRID_HEIGHT = DAYS * (CELL_SIZE + CELL_GAP) + CELL_GAP


def hex_mix(color1: str, color2: str, ratio: float) -> str:
    """
    Mix two hex colors (without #).
    ratio: 0 = color1, 1 = color2, 0.5 = midpoint
    """
    # Remove # if present
    c1 = color1.lstrip('#')
    c2 = color2.lstrip('#')

    r1 = int(c1[0:2], 16)
    g1 = int(c1[2:4], 16)
    b1 = int(c1[4:6], 16)

    r2 = int(c2[0:2], 16)
    g2 = int(c2[2:4], 16)
    b2 = int(c2[4:6], 16)

    r = int(r1 + (r2 - r1) * ratio)
    g = int(g1 + (g2 - g1) * ratio)
    b = int(b1 + (b2 - b1) * ratio)

    return f"#{r:02x}{g:02x}{b:02x}"


def get_contribution_color(level: int) -> str:
    """
    Get color for contribution level (0-4).
    0 = bg_deep (empty)
    1-4 = shades of green (quartiles)
    """
    if level == 0:
        return hex_mix(PALETTE['bg_deep'], PALETTE['border'], 0.35)

    # Derive green shades from PALETTE green (toward bg for lower levels)
    palette_green = PALETTE['green']
    palette_bg = PALETTE['bg_deep']

    # Map levels 1-4 to mix ratios
    # Level 1 = light green (40% mix toward bg)
    # Level 4 = full palette green (0% mix)
    ratios = {
        1: 0.4,  # Light
        2: 0.6,  # Medium-light
        3: 0.8,  # Medium-dark
        4: 1.0,  # Full
    }

    ratio = ratios.get(level, 1.0)
    return hex_mix(palette_bg, palette_green, ratio)


def get_contribution_level(count: int, nonzero_counts: List[int]) -> int:
    """
    Map contribution count to level 0-4 based on quartiles of nonzero counts.
    """
    if count == 0:
        return 0

    if not nonzero_counts:
        return 1

    sorted_counts = sorted(nonzero_counts)
    q1 = sorted_counts[len(sorted_counts) // 4]
    q2 = sorted_counts[len(sorted_counts) // 2]
    q3 = sorted_counts[3 * len(sorted_counts) // 4]

    if count <= q1:
        return 1
    elif count <= q2:
        return 2
    elif count <= q3:
        return 3
    else:
        return 4


def get_last_52_weeks(calendar: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Extract last 52 weeks from calendar (oldest first).
    """
    if not calendar:
        return []

    # Get today's date
    today = datetime.now().date()
    weeks_back = today - timedelta(weeks=52)

    # Filter calendar
    result = []
    for entry in calendar:
        date_obj = datetime.fromisoformat(entry['date']).date()
        if date_obj >= weeks_back:
            result.append(entry)

    return result


def calendar_to_grid(calendar: List[Dict[str, Any]]) -> Tuple[List[List[int]], int]:
    """
    Convert calendar to 52x7 grid (weeks x days).
    Returns (grid, total_contributions)
    grid[week][day] = contribution count (oldest week first)
    """
    # Initialize 52x7 grid
    grid = [[0] * DAYS for _ in range(WEEKS)]

    if not calendar:
        return grid, 0

    # Find oldest entry
    if len(calendar) > 0:
        oldest_date = datetime.fromisoformat(calendar[0]['date']).date()
    else:
        oldest_date = datetime.now().date() - timedelta(weeks=52)

    # Start from Sunday of the week containing oldest_date
    # (or Monday, depending on GitHub's convention)
    start_date = oldest_date - timedelta(days=oldest_date.weekday())

    # Build calendar dict for fast lookup
    cal_dict = {entry['date']: entry['count'] for entry in calendar}

    # Fill grid
    total = 0
    current_date = start_date
    for week in range(WEEKS):
        for day in range(DAYS):
            date_str = current_date.isoformat()
            count = cal_dict.get(date_str, 0)
            grid[week][day] = count
            total += count
            current_date += timedelta(days=1)

    return grid, total


def compute_serpentine_path() -> List[Tuple[float, float]]:
    """
    Compute the serpentine path through the grid as a list of center points.
    Path goes: down week 0, right, up week 1, right, down week 2, etc.
    Returns list of (x, y) in SVG coordinates (relative to grid origin).
    """
    path = []

    for week in range(WEEKS):
        if week % 2 == 0:
            # Down: day 0 to 6
            for day in range(DAYS):
                x = GRID_MARGIN_LEFT + week * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2 + CELL_GAP
                y = GRID_MARGIN_TOP + day * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2 + CELL_GAP
                path.append((x, y))
        else:
            # Up: day 6 to 0
            for day in range(DAYS - 1, -1, -1):
                x = GRID_MARGIN_LEFT + week * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2 + CELL_GAP
                y = GRID_MARGIN_TOP + day * (CELL_SIZE + CELL_GAP) + CELL_SIZE / 2 + CELL_GAP
                path.append((x, y))

    return path


def path_to_svg_path(points: List[Tuple[float, float]]) -> str:
    """Convert list of (x, y) points to SVG path d attribute."""
    if not points:
        return ""

    parts = [f"M {points[0][0]:.1f} {points[0][1]:.1f}"]
    for x, y in points[1:]:
        parts.append(f"L {x:.1f} {y:.1f}")

    return " ".join(parts)


def generate_snake_svg(data: Dict[str, Any]) -> str:
    """
    Generate the animated contribution snake SVG.
    """
    # Extract calendar and compute grid
    calendar = data.get('calendar', [])
    last_52 = get_last_52_weeks(calendar)
    grid, total_contributions = calendar_to_grid(last_52)

    # Compute contribution levels
    nonzero_counts = [count for week in grid for count in week if count > 0]
    levels_grid = [[get_contribution_level(grid[w][d], nonzero_counts) for d in range(DAYS)] for w in range(WEEKS)]

    # Compute serpentine path
    serpentine_path = compute_serpentine_path()
    path_d = path_to_svg_path(serpentine_path)

    # CSS animations
    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.grid {
  animation: fadeIn 0.6s ease-out;
}
.snake-segment {
  opacity: 1;
}
"""

    # Start SVG
    svg = card_frame(CARD_WIDTH, CARD_HEIGHT)
    svg += "\n" + styles(css)

    # No title row — the README section banner titles this card.

    # Group for grid and snake. NO transform here — margins are baked into
    # every coordinate (a translate on top of them double-offset the grid).
    svg += '\n<g class="grid">'

    # Draw grid cells
    cell_index = 0
    cell_index_to_pos = {}  # Map cell index to serpentine position index

    for week in range(WEEKS):
        for day in range(DAYS):
            x = GRID_MARGIN_LEFT + week * (CELL_SIZE + CELL_GAP) + CELL_GAP
            y = GRID_MARGIN_TOP + day * (CELL_SIZE + CELL_GAP) + CELL_GAP
            level = levels_grid[week][day]
            color = get_contribution_color(level)

            # Store position in serpentine order
            if week % 2 == 0:
                serpentine_idx = week * DAYS + day
            else:
                serpentine_idx = week * DAYS + (DAYS - 1 - day)
            cell_index_to_pos[cell_index] = serpentine_idx

            # Cell rectangle (open tag, not self-closing)
            cell_id = f"cell-{cell_index}"
            svg += f'\n  <rect id="{cell_id}" x="{x:.1f}" y="{y:.1f}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="{CELL_RX}" fill="{color}" stroke="{PALETTE["border"]}" stroke-width="0.5">'

            # Eating animation: opacity dips to 0.15 when snake head passes, restores near end
            # Compute when snake head reaches this cell
            total_path_length = len(serpentine_path)
            if total_path_length > 0:
                pass_fraction = serpentine_idx / total_path_length

                # Eaten cells STAY dim until just before the loop restarts —
                # a brief dip reads as a flicker, not as the snake eating.
                pass_fraction = min(pass_fraction, 0.95)
                key_times = [0, max(0.0, pass_fraction - 0.01), pass_fraction, 0.97, 1]
                values = [1, 1, 0.15, 0.15, 1]

                # Sort and deduplicate keyTimes/values
                paired = list(zip(key_times, values))
                paired.sort(key=lambda x: x[0])
                key_times = [p[0] for p in paired]
                values = [p[1] for p in paired]

                # Ensure unique sorted
                unique_paired = []
                for kt, v in zip(key_times, values):
                    if not unique_paired or unique_paired[-1][0] != kt:
                        unique_paired.append((kt, v))
                    else:
                        unique_paired[-1] = (kt, v)

                key_times = [p[0] for p in unique_paired]
                values = [p[1] for p in unique_paired]

                key_times_str = ";".join(f"{kt:.3f}" for kt in key_times)
                values_str = ";".join(str(v) for v in values)

                svg += f'\n    <animate attributeName="opacity" dur="{SNAKE_ANIMATION_DURATION}s" repeatCount="indefinite" keyTimes="{key_times_str}" values="{values_str}"/>'

            svg += '\n  </rect>'

            cell_index += 1

    # Draw hidden path for snake motion
    svg += f'\n  <path id="serpentine-path" d="{path_d}" fill="none" stroke="none" style="display:none"/>'

    # Draw snake segments (7 of them)
    for segment_idx in range(SNAKE_SEGMENTS):
        # Determine color
        if segment_idx == 0:
            segment_color = PALETTE['orange']  # Head
            segment_size = CELL_SIZE * SNAKE_HEAD_SCALE
        else:
            segment_color = PALETTE['purple']  # Body
            segment_size = CELL_SIZE

        segment_id = f"snake-segment-{segment_idx}"

        # Stagger begin times: -0.15s per segment
        begin_time = -0.15 * segment_idx

        svg += f'\n  <g id="{segment_id}" class="snake-segment">'
        svg += f'\n    <circle class="snake-circle" cx="0" cy="0" r="{segment_size/2:.1f}" fill="{segment_color}"/>'
        svg += f'\n    <animateMotion dur="{SNAKE_ANIMATION_DURATION}s" repeatCount="indefinite" begin="{begin_time}s">'
        svg += f'\n      <mpath href="#serpentine-path"/>'
        svg += f'\n    </animateMotion>'
        svg += f'\n  </g>'

    svg += '\n</g>'

    # Caption: "52 weeks · X contributions"
    caption_x = CARD_WIDTH // 2
    caption_y = GRID_MARGIN_TOP + GRID_HEIGHT + 15
    caption_text = f"52 weeks · {total_contributions:,} contributions"
    svg += f'\n<text x="{caption_x}" y="{caption_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}" text-anchor="middle">{esc(caption_text)}</text>'

    svg += "\n</svg>"

    return svg


def render(data: Dict[str, Any], out_path: str) -> None:
    """
    Render snake SVG (orchestrator interface).
    """
    svg_content = generate_snake_svg(data)

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


def main():
    parser = argparse.ArgumentParser(description="Generate animated contribution snake SVG")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/snake.svg",
        help="Output SVG path",
    )
    args = parser.parse_args()

    # Load data
    data = load(mock=args.mock)

    # Generate SVG
    svg_content = generate_snake_svg(data)

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

    print(f"✓ Snake SVG written to {args.out}")

    # Return result JSON
    result = {
        "module": "snake",
        "ok": True,
        "grid": "52x7",
        "anim": "SMIL",
        "visual_notes": "Generated 52-week contribution snake grid with serpentine animation and cell-eating effect.",
    }
    print(json.dumps(result, indent=2))

    return 0


if __name__ == "__main__":
    sys.exit(main())
