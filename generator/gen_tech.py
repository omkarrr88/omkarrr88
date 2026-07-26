#!/usr/bin/env python3
"""
Tech Stack SVG generator for GitHub profile.

Spec-sheet layout: a left column of accent-colored group labels with chip
rows flowing to the right, thin dividers between groups. No in-card title —
the README's section banner carries it.

Contract:
  --mock: Use static mock data (default True)
  --out PATH: Output SVG file path (default profile/tech.svg)
"""

import argparse
import os
import xml.dom.minidom
from typing import Dict, List, Tuple

from theme import PALETTE, FONT, esc, card_frame, styles, text_width
from icons import ICONS

WIDTH = 920
PAD_X = 22
PAD_TOP = 24
PAD_BOTTOM = 24
LABEL_COL_W = 148          # left column reserved for group labels
CHIP_X0 = PAD_X + LABEL_COL_W
CHIP_MAX_X = WIDTH - PAD_X
CHIP_H = 28
CHIP_GAP = 8
ROW_STEP = CHIP_H + CHIP_GAP
GROUP_SPACING = 16         # gap above/below each divider


def chip_width(name: str, has_icon: bool = True) -> float:
    """pad(8) + icon(18) + gap(6) + text + pad(10); text-only chips skip the icon."""
    return (42 if has_icon else 20) + text_width(name, 13.5)


def render_chip(name: str, icon_key: str, display_hex: str, accent: str, x: float, y: float) -> str:
    icon = ICONS.get(icon_key, {}) if icon_key else {}
    icon_d = icon.get("d", "")
    icon_hex = display_hex or icon.get("hex", "999999")
    w = chip_width(name, has_icon=bool(icon_d))

    svg = (
        f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{CHIP_H}" rx="14" '
        f'fill="{PALETTE["bg_deep"]}" stroke="{accent}" stroke-opacity="0.35" stroke-width="1"/>'
    )
    if icon_d:
        svg += (
            f'<g transform="translate({x + 8:.1f},{y + 5:.1f}) scale(0.75)">'
            f'<path d="{icon_d}" fill="#{icon_hex}"/></g>'
        )
    text_x = x + (32 if icon_d else 10)
    svg += (
        f'<text x="{text_x:.1f}" y="{y + 19:.1f}" font-family="{FONT}" font-size="13.5" '
        f'fill="{PALETTE["text"]}">{esc(name)}</text>'
    )
    return svg


def wrap_rows(chips: List[Tuple[str, str, str]]) -> List[List[Tuple[str, str, str]]]:
    """Wrap chips into rows fitting between CHIP_X0 and CHIP_MAX_X."""
    rows: List[List[Tuple[str, str, str]]] = []
    row: List[Tuple[str, str, str]] = []
    x = CHIP_X0
    for chip in chips:
        w = chip_width(chip[0], has_icon=bool(chip[1] and ICONS.get(chip[1], {}).get("d")))
        if row and x + w > CHIP_MAX_X:
            rows.append(row)
            row = [chip]
            x = CHIP_X0 + w + CHIP_GAP
        else:
            row.append(chip)
            x += w + CHIP_GAP
    if row:
        rows.append(row)
    return rows


def render(data: dict, out_path: str) -> None:
    """Render tech SVG (orchestrator interface)."""
    generate_tech(out_path, mock=False)


def generate_tech(out_path: str, mock: bool = True) -> None:
    # (name, icon_key, display_hex) — display_hex "" means use brand hex
    tech_groups: Dict[str, List[Tuple[str, str, str]]] = {
        "Languages": [
            ("Python", "python", ""),
            ("TypeScript", "typescript", ""),
            ("JavaScript", "javascript", ""),
            ("Java", "openjdk", ""),
            ("SQL", "postgresql", ""),
        ],
        "Frontend": [
            ("React", "react", ""),
            ("Next.js", "nextdotjs", ICONS.get("nextdotjs", {}).get("display_hex", "")),
            ("Vite", "vite", ""),
            ("Tailwind CSS", "tailwindcss", ""),
            ("Three.js", "threedotjs", ICONS.get("threedotjs", {}).get("display_hex", "")),
        ],
        "Backend & APIs": [
            ("Node.js", "nodedotjs", ""),
            ("Express", "express", ICONS.get("express", {}).get("display_hex", "")),
            ("NestJS", "nestjs", ""),
            ("Flask", "flask", ICONS.get("flask", {}).get("display_hex", "")),
            ("FastAPI", "fastapi", ""),
            ("GraphQL", "graphql", ""),
            ("REST", None, ""),
            ("WebSockets", None, ""),
            ("JWT", "jsonwebtokens", ICONS.get("jsonwebtokens", {}).get("display_hex", "")),
            ("OAuth", None, ""),
        ],
        "AI Engineering": [
            ("RAG", None, ""),
            ("LLM APIs", None, ""),
            ("MCP", "anthropic", ""),
            ("LangChain", "langchain", ICONS.get("langchain", {}).get("display_hex", "")),
            ("pgvector", None, ""),
        ],
        "ML & Data": [
            ("PyTorch", "pytorch", ""),
            ("TensorFlow", "tensorflow", ""),
            ("Scikit-learn", "scikitlearn", ""),
            ("OpenCV", "opencv", ""),
            ("Pandas", "pandas", ICONS.get("pandas", {}).get("display_hex", "")),
            ("NumPy", "numpy", ICONS.get("numpy", {}).get("display_hex", "")),
            ("Streamlit", "streamlit", ""),
        ],
        "Databases": [
            ("PostgreSQL", "postgresql", ""),
            ("MySQL", "mysql", ""),
            ("MongoDB", "mongodb", ""),
            ("Prisma", "prisma", ICONS.get("prisma", {}).get("display_hex", "")),
            ("Supabase", "supabase", ""),
            ("Redis", "redis", ""),
            ("SQLAlchemy", "sqlalchemy", ""),
        ],
        "Cloud & DevOps": [
            ("Docker", "docker", ""),
            ("AWS", "amazonwebservices", ICONS.get("amazonwebservices", {}).get("display_hex", "")),
            ("Google Cloud", "googlecloud", ""),
            ("Railway", "railway", ICONS.get("railway", {}).get("display_hex", "")),
            ("GitHub Actions", "githubactions", ""),
            ("Git", "git", ""),
        ],
        "Blockchain": [
            ("Solidity", "solidity", ICONS.get("solidity", {}).get("display_hex", "")),
            ("Web3.js", "web3dotjs", ""),
            ("Hardhat", None, ""),
        ],
        "Testing & Monitoring": [
            ("pytest", "pytest", ""),
            ("Vitest", "vitest", ""),
            ("Playwright", "playwright", ""),
            ("Sentry", "sentry", ICONS.get("sentry", {}).get("display_hex", "")),
        ],
    }
    group_accents = {
        "Languages": PALETTE["blue"],
        "Frontend": PALETTE["cyan"],
        "Backend & APIs": PALETTE["purple"],
        "AI Engineering": PALETTE["red"],
        "ML & Data": PALETTE["orange"],
        "Databases": PALETTE["teal"],
        "Cloud & DevOps": PALETTE["green"],
        "Blockchain": PALETTE["orange"],
        "Testing & Monitoring": PALETTE["cyan"],
    }

    body = ""
    y = PAD_TOP
    names = list(tech_groups.keys())
    for gi, group in enumerate(names):
        chips = tech_groups[group]
        accent = group_accents[group]
        rows = wrap_rows(chips)
        block_h = len(rows) * ROW_STEP - CHIP_GAP

        body += f'\n<g class="grp" style="animation-delay: {gi * 120}ms;">'

        # Label column: accent dot + uppercase label, vertically centered.
        # Long labels split at " & " onto two lines to stay inside the column.
        label_cy = y + block_h / 2
        label = group.upper()
        est_w = text_width(label, 11) + len(label) * 1.5  # letter-spacing
        if est_w > LABEL_COL_W - 50 and " & " in label:
            head, tail = label.split(" & ", 1)
            lines = [head, "& " + tail]
        else:
            lines = [label]
        body += f'\n<circle cx="{PAD_X + 4}" cy="{label_cy - 4:.1f}" r="3" fill="{accent}"/>'
        if len(lines) == 1:
            body += (
                f'\n<text x="{PAD_X + 14}" y="{label_cy:.1f}" font-family="{FONT}" font-size="11" '
                f'font-weight="700" letter-spacing="1.5" fill="{accent}">{esc(lines[0])}</text>'
            )
        else:
            body += (
                f'\n<text x="{PAD_X + 14}" y="{label_cy - 7:.1f}" font-family="{FONT}" font-size="11" '
                f'font-weight="700" letter-spacing="1.5" fill="{accent}">{esc(lines[0])}</text>'
                f'\n<text x="{PAD_X + 14}" y="{label_cy + 8:.1f}" font-family="{FONT}" font-size="11" '
                f'font-weight="700" letter-spacing="1.5" fill="{accent}">{esc(lines[1])}</text>'
            )

        # Chip rows
        ry = y
        for row in rows:
            x = CHIP_X0
            for name, icon_key, display_hex in row:
                body += "\n" + render_chip(name, icon_key, display_hex, accent, x, ry)
                x += chip_width(name, has_icon=bool(icon_key and ICONS.get(icon_key, {}).get("d"))) + CHIP_GAP
            ry += ROW_STEP
        body += "\n</g>"

        y += block_h
        if gi < len(names) - 1:
            y += GROUP_SPACING
            body += (
                f'\n<line x1="{PAD_X}" y1="{y:.1f}" x2="{WIDTH - PAD_X}" y2="{y:.1f}" '
                f'stroke="{PALETTE["border"]}" stroke-width="1" opacity="0.6"/>'
            )
            y += GROUP_SPACING

    total_height = int(y + PAD_BOTTOM)

    css = """
@keyframes fadeIn {
  from { opacity: 0; }
  to { opacity: 1; }
}
.grp {
    animation: fadeIn 0.6s ease-out backwards;
}
"""
    svg_content = card_frame(WIDTH, total_height) + "\n" + styles(css) + body + "\n</svg>"

    xml.dom.minidom.parseString(svg_content)

    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)
    with open(out_path, "w") as f:
        f.write(svg_content)
    print(f"✓ Tech stack SVG generated: {out_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate tech stack SVG for GitHub profile")
    parser.add_argument("--mock", action="store_true", default=True, help="Use mock data (always True)")
    parser.add_argument("--out", type=str, default="profile/tech.svg", help="Output SVG file path")
    args = parser.parse_args()
    generate_tech(args.out, args.mock)


if __name__ == "__main__":
    main()
