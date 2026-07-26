#!/usr/bin/env python3
"""
Contribution Streak card generator for GitHub profile.
Displays: Total Contributions (left), Current Streak with flame ring (center),
Longest Streak (right).
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


def format_number(num: int) -> str:
    """Format large numbers: 1000 -> 1k, 1500 -> 1.5k, etc."""
    if num < 1000:
        return str(num)
    if num < 1_000_000:
        k = num / 1000
        if k == int(k):
            return f"{int(k)}k"
        return f"{k:.1f}k".rstrip('0').rstrip('.')
    m = num / 1_000_000
    if m == int(m):
        return f"{int(m)}M"
    return f"{m:.1f}M".rstrip('0').rstrip('.')


def render(data: dict, out_path: str) -> None:
    """
    Render streak SVG (orchestrator interface).

    Args:
        data: Shared data dict from data.load()
        out_path: Path to write SVG file
    """
    svg_content = generate_streak_svg(data)

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


def generate_streak_svg(data: dict) -> str:
    """
    Generate streak card SVG.

    Args:
        data: dict from data.load() containing user, stats, calendar, streak, languages

    Returns:
        SVG string
    """
    width, height = 452, 210

    # Extract data
    streak = data.get("streak", {})
    stats = data.get("stats", {})

    total_contributions = streak.get("total", 0)
    contributions_year = stats.get("contributions_year", 0)
    current_streak = streak.get("current", 0)
    current_range = streak.get("current_range", "")
    longest_streak = streak.get("longest", 0)
    longest_range = streak.get("longest_range", "")

    # CSS animations: pulse glow for flame ring
    # Animations are browser-only; static rendering shows the final state
    css = """
@keyframes pulseGlow {
  0%, 100% {
    filter: drop-shadow(0 0 4px rgba(255, 158, 100, 0.6));
  }
  50% {
    filter: drop-shadow(0 0 8px rgba(255, 158, 100, 0.9));
  }
}

.flame-ring {
  animation: pulseGlow 2s ease-in-out infinite;
}
"""

    # Start SVG
    svg = card_frame(width, height)
    svg += "\n" + styles(css)

    # Simple streak/flame icon (path)
    flame_icon = "M12 2c0 0 1 3 1 5 0 2-1 4-1 6 0 4 2 6 2 8 0 2-1 3-2 4 0 1-1 2-2 2s-2-1-2-2c-1-1-2-2-2-4 0-2 2-4 2-8 0-2-1-4-1-6 0-2 1-5 1-5h2z"

    svg += "\n" + title_row(flame_icon, "Contribution Streak")

    # Three columns: Total (left), Current (center), Longest (right)
    # Column widths: ~130px each, with dividers
    col_width = 130
    col_y_start = 62

    # --- COLUMN 1: TOTAL CONTRIBUTIONS ---
    x_col1 = 22
    y_col1_num = col_y_start + 30
    # No group wrapper for better static rendering

    # Big number
    svg += f'\n<text x="{x_col1}" y="{y_col1_num}" font-family="{FONT}" font-size="32" font-weight="700" fill="{PALETTE["blue"]}">{esc(format_number(total_contributions))}</text>'

    # Label under the big number (mirrors "Longest streak" on the right)
    svg += f'\n<text x="{x_col1}" y="{y_col1_num + 22}" font-family="{FONT}" font-size="12" fill="{PALETTE["muted"]}">Total contributions</text>'

    # Contributions this year (two positioned texts — no tspan reliance)
    svg += f'\n<text x="{x_col1}" y="{y_col1_num + 42}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}">Last year:</text>'
    svg += f'\n<text x="{x_col1 + 58}" y="{y_col1_num + 42}" font-family="{FONT}" font-size="13" font-weight="600" fill="{PALETTE["text"]}">{esc(format_number(contributions_year))}</text>'

    # Divider 1 (vertical line)
    svg += f'\n<line x1="160" y1="72" x2="160" y2="180" stroke="{PALETTE["border"]}" stroke-width="1" opacity="0.5"/>'

    # --- COLUMN 2: CURRENT STREAK (CENTER) ---
    x_center = 226  # Center of column (178 + 65/2)
    center_y = 105

    # Flame ring background (decorative circle)
    ring_radius = 38
    svg += f'\n<circle cx="{x_center}" cy="{center_y}" r="{ring_radius}" fill="none" stroke="{PALETTE["border"]}" stroke-width="1" opacity="0.2"/>'

    # Animated flame ring (orange stroke with pulse glow)
    # Start visible for static rendering (no stroke-dasharray initial state for PNG)
    svg += (
        f'\n<circle class="flame-ring" cx="{x_center}" cy="{center_y}" r="{ring_radius}" fill="none" stroke="{PALETTE["orange"]}" stroke-width="3" stroke-linecap="round">'
        f'\n  <animate attributeName="stroke-opacity" values="1;0.72;0.95;0.65;1;0.85;1" dur="2.6s" repeatCount="indefinite"/>'
        f'\n</circle>'
    )

    # Current streak number inside ring
    svg += f'\n<text x="{x_center}" y="{center_y + 10}" font-family="{FONT}" font-size="32" font-weight="700" fill="{PALETTE["orange"]}" text-anchor="middle">{esc(current_streak)}</text>'

    # Label below ring
    svg += f'\n<text x="{x_center}" y="{center_y + 65}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}" text-anchor="middle">Current Streak</text>'

    # Date range below label
    svg += f'\n<text x="{x_center}" y="{center_y + 82}" font-family="{FONT}" font-size="10" fill="{PALETTE["text"]}" text-anchor="middle">{esc(current_range)}</text>'

    # Divider 2 (vertical line)
    svg += f'\n<line x1="294" y1="72" x2="294" y2="180" stroke="{PALETTE["border"]}" stroke-width="1" opacity="0.5"/>'

    # --- COLUMN 3: LONGEST STREAK ---
    x_col3 = 312
    y_col3_num = col_y_start + 30
    # No group wrapper for better static rendering

    # Big number
    svg += f'\n<text x="{x_col3}" y="{y_col3_num}" font-family="{FONT}" font-size="32" font-weight="700" fill="{PALETTE["blue"]}">{esc(format_number(longest_streak))}</text>'

    # Subtitle: "Longest streak"
    svg += f'\n<text x="{x_col3}" y="{y_col3_num + 25}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}">Longest streak</text>'

    # Date range
    svg += f'\n<text x="{x_col3}" y="{y_col3_num + 40}" font-family="{FONT}" font-size="10" fill="{PALETTE["text"]}">{esc(longest_range)}</text>'

    # Close SVG
    svg += "\n</svg>"

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate Contribution Streak SVG card")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/streak.svg",
        help="Output SVG file path",
    )
    args = parser.parse_args()

    # Load data
    data = load_data(mock=args.mock)

    # Generate SVG
    svg_content = generate_streak_svg(data)

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

    print(f"✓ Streak SVG written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
