#!/usr/bin/env python3
"""
GitHub Stats card generator.
Displays: Total Stars, Commits, PRs, Issues, Contributed To (left column),
and a decorative follower ring (right side).
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
from icons import ICONS


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
    Render stats SVG (orchestrator interface).

    Args:
        data: Shared data dict from data.load()
        out_path: Path to write SVG file
    """
    svg_content = generate_stats_svg(data)

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


def generate_stats_svg(data: dict) -> str:
    """
    Generate stats SVG card.

    Args:
        data: dict from data.load() containing user, stats, calendar, streak, languages

    Returns:
        SVG string
    """
    width, height = 452, 210

    # Extract stats
    stats = data.get("stats", {})
    user = data.get("user", {})

    stars = stats.get("stars", 0)
    commits = stats.get("commits_total", 0)
    prs = stats.get("prs", 0)
    repos = user.get("public_repos", 0)
    contributed_to = stats.get("contributed_to", 0)
    followers = user.get("followers", 0)

    # Stat rows: icon, label, formatted value
    stat_rows = [
        ("⭐", "Total Stars", format_number(stars)),
        ("🔨", "Commits", format_number(commits)),
        ("📝", "Pull Requests", format_number(prs)),
        ("📦", "Repositories", format_number(repos)),
        ("🤝", "Contributed To", format_number(contributed_to)),
    ]

    # CSS animations
    # Animations use transform-only (no opacity) for static SVG compatibility
    # When viewed in a browser, rows slide up and values scale up on load
    css = """
@keyframes slideUp {
  from { transform: translateY(6px); }
  to { transform: translateY(0); }
}

@keyframes popIn {
  from { transform: scale(0.85); }
  to { transform: scale(1); }
}

.stat-row {
  animation: slideUp 0.5s ease-out forwards;
}
.stat-row:nth-child(1) { animation-delay: 80ms; }
.stat-row:nth-child(2) { animation-delay: 160ms; }
.stat-row:nth-child(3) { animation-delay: 240ms; }
.stat-row:nth-child(4) { animation-delay: 320ms; }
.stat-row:nth-child(5) { animation-delay: 400ms; }

.stat-value {
  animation: popIn 0.4s ease-out forwards;
  transform-origin: center;
}
.stat-row:nth-child(1) .stat-value { animation-delay: 140ms; }
.stat-row:nth-child(2) .stat-value { animation-delay: 220ms; }
.stat-row:nth-child(3) .stat-value { animation-delay: 300ms; }
.stat-row:nth-child(4) .stat-value { animation-delay: 380ms; }
.stat-row:nth-child(5) .stat-value { animation-delay: 460ms; }

.follower-ring {
  animation: slideUp 0.6s ease-out forwards;
  animation-delay: 600ms;
}

.follower-count {
  animation: popIn 0.5s ease-out forwards;
  animation-delay: 700ms;
}
"""

    # Start SVG
    svg = card_frame(width, height)
    svg += "\n" + styles(css)

    # Title row with icon
    star_icon = ICONS.get("python", {}).get("d", "")  # Fallback; we'll use a simple star
    simple_star = "M12 2l3.09 6.26L22 9.27l-5 4.87 1.18 6.88L12 17.77l-6.18 3.25L7 14.14 2 9.27l6.91-1.01L12 2z"
    svg += "\n" + title_row(simple_star, "GitHub Stats")

    # Left column: stat rows
    # Layout: icon circle | label | value
    x_left = 22
    y_start = 62
    row_height = 27

    for idx, (emoji, label, value) in enumerate(stat_rows):
        y = y_start + (idx * row_height)

        # Calculate animation delays
        row_delay_ms = 80 + (idx * 80)
        value_delay_ms = 140 + (idx * 80)

        # Row group with inline animation
        svg += f'\n<g style="animation: slideUp 0.5s ease-out forwards; animation-delay: {row_delay_ms}ms;">'

        # Icon circle
        icon_colors = [PALETTE["blue"], PALETTE["purple"], PALETTE["teal"], PALETTE["orange"], PALETTE["red"]]
        icon_color = icon_colors[idx % len(icon_colors)]
        svg += f'\n<circle cx="{x_left + 6}" cy="{y}" r="4" fill="{icon_color}"/>'

        # Label (left-aligned, max width to prevent overlap with values)
        svg += f'\n<text x="{x_left + 18}" y="{y + 4}" font-family="{FONT}" font-size="11" fill="{PALETTE["text"]}">{esc(label)}</text>'

        # Value (right-aligned in left section, with scale animation)
        svg += f'\n<text style="animation: popIn 0.4s ease-out forwards; animation-delay: {value_delay_ms}ms; transform-origin: right;" x="165" y="{y + 4}" font-family="{MONO}" font-size="13" font-weight="700" fill="{PALETTE["blue"]}" text-anchor="end">{esc(value)}</text>'

        # Divider line (if not last row)
        if idx < len(stat_rows) - 1:
            svg += f'\n<line x1="{x_left}" y1="{y + 13}" x2="175" y2="{y + 13}" stroke="{PALETTE["border"]}" stroke-width="0.5" opacity="0.6"/>'

        svg += '\n</g>'

    # Right side: decorative ring with followers
    ring_cx = 355
    ring_cy = 105
    ring_r = 50
    ring_radius = 42

    # Gradient for the ring stroke (blue to purple)
    svg += f'''
<defs>
<linearGradient id="ringGradient" x1="0%" y1="0%" x2="100%" y2="100%">
<stop offset="0%" stop-color="{PALETTE["blue"]}" />
<stop offset="100%" stop-color="{PALETTE["purple"]}" />
</linearGradient>
</defs>'''

    # Ring background circle (subtle)
    svg += f'\n<circle cx="{ring_cx}" cy="{ring_cy}" r="{ring_r}" fill="none" stroke="{PALETTE["border"]}" stroke-width="1" opacity="0.3"/>'

    # Ring stroke (animated with gradient)
    circumference = 2 * 3.14159 * ring_radius
    svg += f'\n<circle style="animation: slideUp 0.6s ease-out forwards; animation-delay: 600ms;" cx="{ring_cx}" cy="{ring_cy}" r="{ring_radius}" fill="none" stroke="url(#ringGradient)" stroke-width="3.5" stroke-linecap="round" opacity="0.9"/>'

    # Follower count (center text)
    svg += f'\n<text style="animation: popIn 0.5s ease-out forwards; animation-delay: 700ms; transform-origin: center;" x="{ring_cx}" y="{ring_cy - 3}" font-family="{FONT}" font-size="26" font-weight="700" fill="{PALETTE["blue"]}" text-anchor="middle">{esc(format_number(followers))}</text>'

    # "Followers" label (center text, below count)
    svg += f'\n<text style="animation: slideUp 0.5s ease-out forwards; animation-delay: 600ms;" x="{ring_cx}" y="{ring_cy + 14}" font-family="{FONT}" font-size="10" fill="{PALETTE["muted"]}" text-anchor="middle" letter-spacing="0.5">Followers</text>'

    # Close SVG
    svg += "\n</svg>"

    return svg


def main():
    parser = argparse.ArgumentParser(description="Generate GitHub Stats SVG card")
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API",
    )
    parser.add_argument(
        "--out",
        type=str,
        default="/tmp/claude-1000/-home-omkar-kadam-Desktop-github-profile/212468f3-83d5-459e-9ea6-085862b2b933/scratchpad/stats.svg",
        help="Output SVG file path",
    )
    args = parser.parse_args()

    # Load data
    data = load_data(mock=args.mock)

    # Generate SVG
    svg_content = generate_stats_svg(data)

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
        print("✓ XML validation passed")
    except Exception as e:
        print(f"✗ XML validation failed: {e}")
        return 1

    # Ensure output directory exists
    os.makedirs(os.path.dirname(args.out), exist_ok=True)

    # Write SVG
    with open(args.out, "w") as f:
        f.write(svg_content)

    print(f"✓ Stats SVG written to {args.out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
