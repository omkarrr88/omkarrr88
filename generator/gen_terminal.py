#!/usr/bin/env python3
"""
Terminal intro card generator.

A terminal window that "boots" and types the bio: commands type out
character-stepped (CSS clip-path steps), outputs fade in after their
command finishes. Base state is fully visible, all reveals use
animation-fill-mode: backwards — reduced-motion users and non-animating
renderers see the complete terminal.
"""

import argparse
import os
import sys
import xml.dom.minidom
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from theme import PALETTE, FONT, MONO, esc, card_frame, styles

WIDTH = 920
PAD_X = 26
BAR_H = 36
LINE_H = 24
BODY_TOP = BAR_H + 22
TYPE_SECS = 0.7   # per command line
OUT_SECS = 0.15   # per output line


def render(data: dict, out_path: str) -> None:
    generate_terminal(out_path)


def generate_terminal(out_path: str) -> None:
    # (kind, text) — kind: cmd | out | blank
    lines = [
        ("cmd", "whoami"),
        ("out", "omkar-kadam — Full Stack Engineer @ Riamona Luxury & Fashion Brands"),
        ("blank", ""),
        ("cmd", "ls achievements/"),
        ("out", "meta-pytorch-hackathon/   → 7th of 31,000+ teams (Chakravyuh)"),
        ("out", "springer-nature/          → V2V collision-risk paper, in review"),
        ("out", "avishkar-2025/            → research finals, Mumbai University"),
        ("blank", ""),
        ("cmd", "cat stack.txt"),
        ("out", "React · Node.js · Python · PostgreSQL · FastAPI · RAG/LLM apps"),
        ("blank", ""),
        ("cmd", "uptime"),
        ("out", "shipping production systems since Jan 2026 — fully unattended"),
    ]

    height = BODY_TOP + len(lines) * LINE_H + 30

    # Build CSS: staggered delays; commands use char-stepped clip-path typing
    css_rules = [
        "@keyframes typeIn { from { clip-path: inset(0 100% 0 0); } to { clip-path: inset(0 0 0 0); } }",
        "@keyframes fadeIn { from { opacity: 0; } to { opacity: 1; } }",
        "@keyframes blink { 0%, 49% { opacity: 1; } 50%, 100% { opacity: 0; } }",
        ".cursor { animation: blink 1.1s infinite; }",
    ]

    body = ""
    t = 0.4  # boot pause
    y = BODY_TOP
    idx = 0
    for kind, text in lines:
        if kind == "blank":
            y += LINE_H
            continue
        cls = f"l{idx}"
        if kind == "cmd":
            steps = max(len(text), 4)
            css_rules.append(
                f".{cls} {{ animation: typeIn {TYPE_SECS}s steps({steps}, end) backwards; animation-delay: {t:.2f}s; }}"
            )
            body += (
                f'\n<text class="{cls}" x="{PAD_X}" y="{y}" font-family="{MONO}" font-size="14">'
                f'<tspan fill="{PALETTE["green"]}" font-weight="700">$ </tspan>'
                f'<tspan fill="{PALETTE["text"]}">{esc(text)}</tspan></text>'
            )
            t += TYPE_SECS + 0.15
        else:
            css_rules.append(
                f".{cls} {{ animation: fadeIn {OUT_SECS}s ease-out backwards; animation-delay: {t:.2f}s; }}"
            )
            body += (
                f'\n<text class="{cls}" x="{PAD_X}" y="{y}" font-family="{MONO}" font-size="13.5" '
                f'fill="{PALETTE["muted"]}">{esc(text)}</text>'
            )
            t += OUT_SECS + 0.1
        y += LINE_H
        idx += 1

    # Final prompt with blinking cursor, appears last
    css_rules.append(f".lp {{ animation: fadeIn 0.2s ease-out backwards; animation-delay: {t:.2f}s; }}")
    body += (
        f'\n<g class="lp">'
        f'<text x="{PAD_X}" y="{y}" font-family="{MONO}" font-size="14" font-weight="700" fill="{PALETTE["green"]}">$</text>'
        f'<rect class="cursor" x="{PAD_X + 16}" y="{y - 12}" width="8" height="15" fill="{PALETTE["blue"]}"/>'
        f'</g>'
    )

    svg = card_frame(WIDTH, height)
    svg += "\n" + styles("\n".join(css_rules))

    # Window chrome: title bar + traffic lights
    svg += (
        f'\n<path d="M0.5 {BAR_H} L0.5 10 Q0.5 0.5 10 0.5 L{WIDTH - 10} 0.5 '
        f'Q{WIDTH - 0.5} 0.5 {WIDTH - 0.5} 10 L{WIDTH - 0.5} {BAR_H} Z" fill="{PALETTE["bg_deep"]}"/>'
        f'\n<line x1="0.5" y1="{BAR_H}" x2="{WIDTH - 0.5}" y2="{BAR_H}" stroke="{PALETTE["border"]}" stroke-width="1"/>'
        f'\n<circle cx="24" cy="{BAR_H / 2}" r="5.5" fill="{PALETTE["red"]}"/>'
        f'\n<circle cx="44" cy="{BAR_H / 2}" r="5.5" fill="{PALETTE["orange"]}"/>'
        f'\n<circle cx="64" cy="{BAR_H / 2}" r="5.5" fill="{PALETTE["green"]}"/>'
        f'\n<text x="{WIDTH / 2}" y="{BAR_H / 2 + 4}" text-anchor="middle" font-family="{MONO}" '
        f'font-size="12" fill="{PALETTE["muted"]}">omkar@github: ~</text>'
    )
    svg += body
    svg += "\n</svg>"

    xml.dom.minidom.parseString(svg)
    os.makedirs(os.path.dirname(out_path) or ".", exist_ok=True)
    with open(out_path, "w") as f:
        f.write(svg)
    print(f"✓ Terminal card generated: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate terminal intro card SVG")
    parser.add_argument("--mock", action="store_true", help="No data needed; accepted for CLI parity")
    parser.add_argument("--out", type=str, default="profile/terminal.svg")
    args = parser.parse_args()
    generate_terminal(args.out)


if __name__ == "__main__":
    main()
