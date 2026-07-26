#!/usr/bin/env python3
"""
Trophy case card generator for GitHub profile.
Displays: Contributions, Longest Streak, Pull Requests, Commits, Total Stars, Followers.
Six metric tiles with tier achievements (iron/bronze/silver/gold/diamond).
Specs: 920x200, tokyonight design system.
"""

import argparse
import json
import os
import sys
import xml.dom.minidom
from pathlib import Path
from typing import Dict, Any, Tuple

# Add parent directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from theme import PALETTE, FONT, esc, card_frame, styles, title_row, text_width
from data import load as load_data


# Tier colors (theme-independent metals)
TIER_COLORS = {
    "iron": "#6b7089",
    "bronze": "#b87333",
    "silver": "#a8b2c8",
    "gold": "#e0af68",
    "diamond": "#7dcfff",
}

# Tier thresholds for each metric
TIER_THRESHOLDS = {
    "contributions": {"bronze": 100, "silver": 500, "gold": 1000, "diamond": 5000},
    "streak": {"bronze": 7, "silver": 14, "gold": 30, "diamond": 60},
    "prs": {"bronze": 10, "silver": 25, "gold": 50, "diamond": 150},
    "commits": {"bronze": 100, "silver": 500, "gold": 1000, "diamond": 5000},
    "stars": {"bronze": 5, "silver": 15, "gold": 50, "diamond": 150},
    "repos": {"bronze": 5, "silver": 15, "gold": 50, "diamond": 150},
}


def format_number(num: int) -> str:
    """Format large numbers: 1000 -> 1k, 1500 -> 1.5k, etc."""
    if num < 1000:
        return str(num)
    if num < 1_000_000:
        k = num / 1000
        if k == int(k):
            return f"{int(k)}k"
        return f"{k:.1f}k".rstrip("0").rstrip(".")
    m = num / 1_000_000
    if m == int(m):
        return f"{int(m)}M"
    return f"{m:.1f}M".rstrip("0").rstrip(".")


def get_tier(metric_name: str, value: int) -> Tuple[str, int]:
    """
    Determine tier and progress to next tier.
    Returns (tier_name, progress_pct)
    progress_pct: 0-100 toward next tier, 100 if diamond
    """
    thresholds = TIER_THRESHOLDS[metric_name]

    if value >= thresholds["diamond"]:
        return "diamond", 100
    if value >= thresholds["gold"]:
        # Progress toward diamond
        current = thresholds["gold"]
        next_val = thresholds["diamond"]
        pct = min(100, int(((value - current) / (next_val - current)) * 100))
        return "gold", pct
    if value >= thresholds["silver"]:
        # Progress toward gold
        current = thresholds["silver"]
        next_val = thresholds["gold"]
        pct = min(100, int(((value - current) / (next_val - current)) * 100))
        return "silver", pct
    if value >= thresholds["bronze"]:
        # Progress toward silver
        current = thresholds["bronze"]
        next_val = thresholds["silver"]
        pct = min(100, int(((value - current) / (next_val - current)) * 100))
        return "bronze", pct

    # Iron: progress toward bronze
    next_val = thresholds["bronze"]
    pct = min(100, int((value / next_val) * 100)) if next_val > 0 else 0
    return "iron", pct


def medal_glyph(x: float, y: float, color: str, tile_index: int = 0) -> str:
    """
    Generate a simple 24x24 medal glyph (circle + ribbon tails).
    Positioned at (x, y).
    """
    # Simple medal: circle (medal) with two ribbon tails
    # Circle at (12, 12) with radius 8
    # Ribbons: left and right paths
    circle = f'<circle cx="{x + 12}" cy="{y + 12}" r="8" fill="{color}">\n      <animate attributeName="opacity" values="1;0.7;1" dur="3s" begin="{tile_index * 0.4:.1f}s" repeatCount="indefinite"/>\n    </circle>'
    # Left ribbon tail
    left_ribbon = f'<path d="M {x+8} {y+2} L {x+6} {y} L {x+7} {y+6}" fill="{color}"/>'
    # Right ribbon tail
    right_ribbon = f'<path d="M {x+16} {y+2} L {x+18} {y} L {x+17} {y+6}" fill="{color}"/>'
    return f"{circle}\n    {left_ribbon}\n    {right_ribbon}"


def render(data: dict, out_path: str) -> None:
    """
    Render trophy SVG (orchestrator interface).

    Args:
        data: Shared data dict from data.load()
        out_path: Path to write SVG file
    """
    svg_content = generate_trophy_svg(data)

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


def generate_trophy_svg(data: dict) -> str:
    """
    Generate trophy case SVG with 6 metric tiles.

    Args:
        data: dict from data.load() containing user, stats, streak

    Returns:
        SVG string
    """
    width, height = 920, 210

    # Extract data
    streak = data.get("streak", {})
    stats = data.get("stats", {})
    user = data.get("user", {})

    contributions = streak.get("total", 0)
    longest_streak = streak.get("longest", 0)
    prs = stats.get("prs", 0)
    commits = stats.get("commits_total", 0)
    stars = stats.get("stars", 0)
    repos = user.get("public_repos", 0)

    # Metrics: (name, value, label)
    metrics = [
        ("contributions", contributions, "Contributions"),
        ("streak", longest_streak, "Longest Streak"),
        ("prs", prs, "Pull Requests"),
        ("commits", commits, "Commits"),
        ("stars", stars, "Total Stars"),
        ("repos", repos, "Repositories"),
    ]

    # CSS: staggered opacity animation
    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}

.tile {
  animation: fadeIn 0.5s ease-out forwards;
}

.tile-0 { animation-delay: 0ms; }
.tile-1 { animation-delay: 60ms; }
.tile-2 { animation-delay: 120ms; }
.tile-3 { animation-delay: 180ms; }
.tile-4 { animation-delay: 240ms; }
.tile-5 { animation-delay: 300ms; }
"""

    # Start SVG
    svg = card_frame(width, height)
    svg += "\n" + styles(css)

    # Trophy icon for title
    trophy_icon = "M3 2h18v4h-2v2c0 1.1-.9 2-2 2h-2v6h2v2h-12v-2h2v-6h-2c-1.1 0-2-.9-2-2v-2h-2v-4zm8 10h-4v6h4v-6z"
    svg += "\n" + title_row(trophy_icon, "Trophies")

    # Tile dimensions
    inner_width = 876  # 920 - 22*2 padding
    tile_width = inner_width / 6  # ~146px each
    tile_height = 110

    x_start = 22
    y_start = 62

    # Tiers for this snapshot (for return JSON)
    tiers_today = {}

    # Render 6 tiles
    for idx, (metric_name, value, label) in enumerate(metrics):
        x = x_start + (idx * tile_width)
        tier_name, progress_pct = get_tier(metric_name, value)
        tiers_today[metric_name] = tier_name

        # Tile group with animation class
        svg += f'\n  <g class="tile tile-{idx}">'

        # Medal glyph (24px at top center)
        tile_center_x = x + (tile_width / 2)
        medal_x = tile_center_x - 12  # 24px wide, center it
        svg += f"\n    {medal_glyph(medal_x, y_start, TIER_COLORS[tier_name], idx)}"

        # Big value (18px, 700, PALETTE text, centered)
        value_formatted = format_number(value)
        value_y = y_start + 40
        svg += f'\n    <text x="{tile_center_x}" y="{value_y}" font-family="{FONT}" font-size="18" font-weight="700" fill="{PALETTE["text"]}" text-anchor="middle">{esc(value_formatted)}</text>'

        # Metric label (11px, PALETTE muted, centered)
        label_y = value_y + 18
        svg += f'\n    <text x="{tile_center_x}" y="{label_y}" font-family="{FONT}" font-size="11" fill="{PALETTE["muted"]}" text-anchor="middle" text-overflow="ellipsis">{esc(label)}</text>'

        # Tier name chip: background rounded rect + text
        chip_y = label_y + 14
        tier_label = tier_name.upper()
        chip_width = text_width(tier_label, 9) + 6  # 3px padding each side
        chip_x = tile_center_x - (chip_width / 2)
        chip_height = 14
        chip_y_rect = chip_y - 10

        # Chip background (rounded rect, tier-color stroke at 0.35 opacity)
        svg += f'\n    <rect x="{chip_x}" y="{chip_y_rect}" width="{chip_width}" height="{chip_height}" rx="4" fill="{PALETTE["bg_deep"]}" stroke="{TIER_COLORS[tier_name]}" stroke-width="1" opacity="0.7"/>'

        # Chip text (9px, tier color)
        svg += f'\n    <text x="{tile_center_x}" y="{chip_y}" font-family="{FONT}" font-size="9" font-weight="600" fill="{TIER_COLORS[tier_name]}" text-anchor="middle">{esc(tier_label)}</text>'

        # Progress bar (thin bar at bottom of tile)
        bar_y = y_start + tile_height - 4
        bar_height = 3
        bar_width = tile_width - 4  # 2px margin each side
        bar_x = x + 2

        # Track background (PALETTE bg_deep)
        svg += f'\n    <rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" rx="1.5" fill="{PALETTE["bg_deep"]}"/>'

        # Progress fill (tier color)
        progress_width = (bar_width * progress_pct) / 100
        svg += (
            f'\n    <rect x="{bar_x}" y="{bar_y}" width="{progress_width}" height="{bar_height}" rx="1.5" fill="{TIER_COLORS[tier_name]}">'
            f'\n      <animate attributeName="width" from="0" to="{progress_width}" dur="0.9s" begin="{0.3 + idx * 0.12:.2f}s" fill="backwards"/>'
            f'\n    </rect>'
        )

        svg += '\n  </g>'

    # Close SVG
    svg += "\n</svg>"

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate Trophy Case SVG card")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/trophies.svg",
        help="Output SVG file path",
    )
    args = parser.parse_args()

    # Load data
    data = load_data(mock=args.mock)

    # Generate SVG
    svg_content = generate_trophy_svg(data)

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

    print(f"✓ Trophy SVG written to {args.out}")

    # Extract tiers for return JSON
    streak = data.get("streak", {})
    stats = data.get("stats", {})
    user = data.get("user", {})

    metrics = [
        ("contributions", streak.get("total", 0)),
        ("streak", streak.get("longest", 0)),
        ("prs", stats.get("prs", 0)),
        ("commits", stats.get("commits_total", 0)),
        ("stars", stats.get("stars", 0)),
        ("repos", user.get("public_repos", 0)),
    ]

    tiers_today = {}
    for metric_name, value in metrics:
        tier_name, _ = get_tier(metric_name, value)
        tiers_today[metric_name] = tier_name

    # Return JSON
    result = {
        "module": "trophies",
        "ok": True,
        "tiers_today": tiers_today,
        "visual_notes": "6 metric tiles in one row with tier achievements and progress bars"
    }
    print(json.dumps(result, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
