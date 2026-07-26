#!/usr/bin/env python3
"""
Growth tracker SVG generator.

Reads profile/history.json (appended daily by generate_all in CI) and renders
sparklines of followers / stars / contributions over time. Until enough
history accumulates it renders a "collecting data" state so the README never
shows a broken or empty card.
"""

import argparse
import json
import os
import xml.dom.minidom
from typing import Any, Dict, List

from theme import PALETTE, FONT, esc, card_frame, styles, title_row

HISTORY_PATH = os.path.join(os.path.dirname(__file__), "..", "profile", "history.json")
MIN_POINTS = 5

WIDTH, HEIGHT = 452, 210
CHART_GLYPH = "M3 17l6-6 4 4 8-8v5h2V4h-8v2h5l-7 7-4-4-8 8z"


def load_history() -> List[Dict[str, Any]]:
    try:
        with open(HISTORY_PATH) as f:
            entries = json.load(f)
        return sorted(entries, key=lambda e: e["date"])
    except Exception:
        return []


def mock_history() -> List[Dict[str, Any]]:
    base = {"followers": 4, "stars": 9, "contributions": 1400}
    out = []
    for i in range(14):
        out.append({
            "date": f"2026-07-{13 + i:02d}",
            "followers": base["followers"] + i // 4,
            "stars": base["stars"] + i // 3,
            "contributions": base["contributions"] + i * 6,
        })
    return out


def sparkline(values: List[int], x: float, y: float, w: float, h: float, color: str) -> str:
    """Polyline sparkline scaled into the given box; flat lines stay visible."""
    vmin, vmax = min(values), max(values)
    spread = (vmax - vmin) or 1
    n = len(values)
    pts = []
    for i, v in enumerate(values):
        px = x + (i / (n - 1)) * w if n > 1 else x + w / 2
        py = y + h - ((v - vmin) / spread) * h
        pts.append(f"{px:.1f},{py:.1f}")
    line = f'<polyline points="{" ".join(pts)}" fill="none" stroke="{color}" stroke-width="1.8" stroke-linejoin="round" stroke-linecap="round"/>'
    lx, ly = pts[-1].split(",")
    dot = f'<circle cx="{lx}" cy="{ly}" r="2.5" fill="{color}"/>'
    return line + dot


def render_card(history: List[Dict[str, Any]]) -> str:
    body = card_frame(WIDTH, HEIGHT)
    body += "\n" + styles(
        "@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }\n"
        ".row { animation: fadeIn 0.6s ease-out backwards; }\n"
        ".row:nth-of-type(2) { animation-delay: 120ms; }\n"
        ".row:nth-of-type(3) { animation-delay: 240ms; }\n"
    )
    body += "\n" + title_row(CHART_GLYPH, "Growth")

    if len(history) < MIN_POINTS:
        since = history[0]["date"] if history else "today"
        days_left = MIN_POINTS - len(history)
        body += (
            f'\n<text x="{WIDTH // 2}" y="100" text-anchor="middle" font-family="{FONT}" '
            f'font-size="13" fill="{PALETTE["text"]}">Collecting data since {esc(since)}</text>'
            f'\n<text x="{WIDTH // 2}" y="122" text-anchor="middle" font-family="{FONT}" '
            f'font-size="11.5" fill="{PALETTE["muted"]}">Charts appear after {days_left} more daily snapshot{"s" if days_left != 1 else ""}</text>'
            f'\n<text x="{WIDTH // 2}" y="158" text-anchor="middle" font-family="{FONT}" '
            f'font-size="11" fill="{PALETTE["muted"]}">{len(history)}/{MIN_POINTS} snapshots recorded</text>'
        )
        return body + "\n</svg>"

    metrics = [
        ("Contributions", "contributions", PALETTE["blue"]),
        ("Stars", "stars", PALETTE["orange"]),
        ("Followers", "followers", PALETTE["teal"]),
    ]
    row_y = 62
    for label, key, color in metrics:
        values = [e.get(key, 0) for e in history]
        delta = values[-1] - values[0]
        delta_txt = f"+{delta}" if delta >= 0 else str(delta)
        body += f'\n<g class="row">'
        body += (
            f'\n<text x="22" y="{row_y + 20}" font-family="{FONT}" font-size="12" '
            f'fill="{PALETTE["muted"]}">{esc(label)}</text>'
        )
        body += "\n" + sparkline(values, 130, row_y + 4, 200, 26, color)
        body += (
            f'\n<text x="{WIDTH - 66}" y="{row_y + 20}" text-anchor="end" font-family="{FONT}" '
            f'font-size="14" font-weight="700" fill="{PALETTE["text"]}">{values[-1]:,}</text>'
            f'\n<text x="{WIDTH - 22}" y="{row_y + 20}" text-anchor="end" font-family="{FONT}" '
            f'font-size="11" font-weight="600" fill="{color}">{esc(delta_txt)}</text>'
        )
        body += "\n</g>"
        row_y += 44

    span = f'{history[0]["date"]} → {history[-1]["date"]}'
    body += (
        f'\n<text x="{WIDTH // 2}" y="{HEIGHT - 14}" text-anchor="middle" font-family="{FONT}" '
        f'font-size="10.5" fill="{PALETTE["muted"]}">{esc(span)}</text>'
    )
    return body + "\n</svg>"


def render(data: dict, out_path: str) -> None:
    """Orchestrator interface. Reads committed history, not the data dict."""
    _write(load_history(), out_path)


def _write(history: List[Dict[str, Any]], out_path: str) -> None:
    svg = render_card(history)
    xml.dom.minidom.parseString(svg)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"✓ Growth card generated: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate growth tracker SVG")
    parser.add_argument("--mock", action="store_true", help="Use mock history")
    parser.add_argument("--out", type=str, default="profile/growth.svg")
    args = parser.parse_args()
    _write(mock_history() if args.mock else load_history(), args.out)


if __name__ == "__main__":
    main()
