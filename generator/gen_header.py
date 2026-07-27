#!/usr/bin/env python3
"""
Header SVG generator for GitHub profile.
Creates an animated hero section with typing effect for role titles.

Contract:
  --mock: Use static mock data (default True)
  --out PATH: Output SVG file path (default profile/header.svg)
"""

import argparse
import os
import xml.dom.minidom
from datetime import datetime

from theme import PALETTE, FONT, MONO, esc

def render(data: dict, out_path: str) -> None:
    """
    Render header SVG (orchestrator interface).

    Args:
        data: Shared data dict (unused for header, always static)
        out_path: Path to write SVG file
    """
    generate_header(out_path, mock=False, include_animations=True)


def generate_header(out_path: str, mock: bool = True, include_animations: bool = True) -> None:
    """
    Generate header SVG with animated typing effect.

    Args:
        out_path: Path to write SVG file
        mock: Whether to use mock data (ignored for header, always static)
        include_animations: Whether to include CSS animations (set to False for static rendering)
    """

    width, height = 920, 160

    # Typing phrases (4 phrases, ~3s each + 1.2s pause per phrase)
    # Plain characters only — esc() is applied at render time.
    phrases = [
        "Full Stack Engineer @ Riamona",
        "7th of 31,000+ - Meta PyTorch Hackathon",
        "React | Node | Python | PostgreSQL",
        "ML Enthusiast & Automation Builder",
        "IT Engineer - Mumbai University '26"
    ]

    # Calculate animation timing
    # 4 phrases, each needs time to type + pause + delete
    # Estimate: 30-50 chars max is ~1.5-2.5s typing, 1.2s pause, ~1.5-2.5s delete
    # Total per phrase: ~4-6s. With 4 phrases: 16-24s. Let's go 12s total (3s per phrase)

    phrase_duration = 3  # seconds per phrase
    total_duration = phrase_duration * len(phrases)

    # Calculate animation timing for each phrase
    type_duration = 1.2  # seconds to type out
    pause_duration = 0.8  # seconds to pause
    delete_duration = 1.0  # seconds to delete

    # Create CSS for animations
    css_lines = []

    if include_animations:
        css_lines.extend([
            "@keyframes fadeInUp {",
            "  from {",
            "    transform: translateY(6px);",
            "    opacity: 0;",
            "  }",
            "  to {",
            "    transform: translateY(0);",
            "    opacity: 1;",
            "  }",
            "}",
            "",
            "@keyframes blink {",
            "  0%, 49% { opacity: 1; }",
            "  50%, 100% { opacity: 0; }",
            "}",
            "",
            "@keyframes pulse {",
            "  0%, 100% { opacity: 1; }",
            "  50% { opacity: 0.6; }",
            "}",
            "",
        ])

        # Generate opacity animations for each phrase
        for i in range(len(phrases)):
            start_pct = int((i * phrase_duration / total_duration) * 100)
            type_pct = int(((i * phrase_duration + type_duration) / total_duration) * 100)
            pause_pct = int(((i * phrase_duration + type_duration + pause_duration) / total_duration) * 100)
            delete_pct = int(((i * phrase_duration + type_duration + pause_duration + delete_duration) / total_duration) * 100)

            css_lines.extend([
                f"@keyframes type-{i} {{",
                f"  0% {{ opacity: 0; }}",
                f"  {start_pct}% {{ opacity: 0; }}",
                f"  {type_pct}% {{ opacity: 1; }}",
                f"  {pause_pct}% {{ opacity: 1; }}",
                f"  {delete_pct}% {{ opacity: 0; }}",
                f"  100% {{ opacity: 0; }}",
                "}",
                ""
            ])

    if include_animations:
        css_lines.extend([
            ".cursor { animation: blink 1s infinite; }",
            ".pulse-dot { animation: pulse 2s infinite; }",
        ])

        # Add animation rules for each phrase text
        for i in range(len(phrases)):
            css_lines.append(f".phrase-{i} {{ animation: type-{i} {total_duration}s linear infinite; }}")
    else:
        # Minimal CSS for static rendering
        css_lines.extend([
            ".cursor { opacity: 1; }",
            ".pulse-dot { opacity: 1; }",
        ])

    css = "\n".join(css_lines)

    # Build SVG
    svg_parts = [
        f'<svg width="{width}" height="{height}" viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg">',
        f"<style>{css}</style>",
    ]

    # Defs for gradients (using PALETTE colors)
    svg_parts.append(f"""<defs>
<linearGradient id="nameGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" style="stop-color:{PALETTE["blue"]};stop-opacity:0.6" />
  <stop offset="100%" style="stop-color:{PALETTE["purple"]};stop-opacity:0.6" />
</linearGradient>
</defs>""")

    # Decorative code glyphs on the sides (subtle, muted)
    svg_parts.append(f'<text x="18" y="48" font-family="{MONO}" font-size="20" font-weight="400" fill="{PALETTE["border"]}" opacity="0.6">&lt;/&gt;</text>')
    svg_parts.append(f'<text x="{width - 48}" y="48" font-family="{MONO}" font-size="20" font-weight="400" fill="{PALETTE["border"]}" opacity="0.6">{{}}</text>')

    # Everything centered on the card's vertical axis
    cx = width // 2

    # Main name headline "Omkar Kadam"
    svg_parts.append(f'<text x="{cx}" y="50" text-anchor="middle" font-family="{FONT}" font-size="32" font-weight="700" fill="{PALETTE["blue"]}">Omkar Kadam</text>')

    # Gradient underline under name (centered)
    svg_parts.append(f'<rect x="{cx - 140}" y="58" width="280" height="3" fill="url(#nameGradient)" rx="1.5"/>')

    # Phrases with typing animation. Each phrase lives in its own <g> whose
    # opacity is animated by its class; the cursor sits inside the group so it
    # appears right after that phrase's text and blinks independently.
    # NOTE: inline style only sets the initial state — CSS animations override
    # inline declarations, but "animation: none" inline would NOT be
    # overridable by class rules (that bug froze the cycle on phrase 0).
    mono_char_w = 7.8  # approx advance width of 13px monospace
    if include_animations:
        for i, phrase in enumerate(phrases):
            initial_opacity = "1" if i == 0 else "0"
            half_w = len(phrase) * mono_char_w / 2
            cursor_x = cx + half_w + 6
            svg_parts.append(f'<g class="phrase-{i}" style="opacity: {initial_opacity};">')
            svg_parts.append(f'<text x="{cx}" y="105" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="400" fill="{PALETTE["cyan"]}">{esc(phrase)}</text>')
            svg_parts.append(f'<rect x="{cursor_x:.0f}" y="92" width="2.5" height="17" fill="{PALETTE["blue"]}" class="cursor"/>')
            svg_parts.append('</g>')
    else:
        # Static rendering: only show first phrase
        svg_parts.append(f'<text x="{cx}" y="105" text-anchor="middle" font-family="{MONO}" font-size="13" font-weight="400" fill="{PALETTE["cyan"]}">{esc(phrases[0])}</text>')

    # Bottom meta line, centered: pulsing green dot + availability + location.
    # Separate positioned elements — no tspan advance-width reliance.
    svg_parts.append(f'<circle cx="{cx - 132}" cy="136" r="3.5" fill="{PALETTE["green"]}" class="pulse-dot"/>')
    svg_parts.append(f'<text x="{cx - 122}" y="140" font-family="{FONT}" font-size="11" font-weight="500" fill="{PALETTE["text"]}">Available for work</text>')
    svg_parts.append(f'<line x1="{cx - 10}" y1="128" x2="{cx - 10}" y2="140" stroke="{PALETTE["border"]}" stroke-width="1"/>')
    svg_parts.append(f'<text x="{cx + 2}" y="140" font-family="{FONT}" font-size="11" font-weight="400" fill="{PALETTE["text"]}">📍 Navi Mumbai, India</text>')

    svg_parts.append('</svg>')

    svg_content = "\n".join(svg_parts)

    # Validate XML
    try:
        xml.dom.minidom.parseString(svg_content)
    except Exception as e:
        print(f"✗ XML validation failed: {e}")
        raise

    # Ensure output directory exists
    os.makedirs(os.path.dirname(out_path) if os.path.dirname(out_path) else ".", exist_ok=True)

    # Write SVG
    with open(out_path, "w") as f:
        f.write(svg_content)

    print(f"✓ Header SVG generated: {out_path}")


def main():
    parser = argparse.ArgumentParser(
        description="Generate animated header SVG for GitHub profile"
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        default=True,
        help="Use mock data (always true for header, ignored)"
    )
    parser.add_argument(
        "--out",
        type=str,
        default="profile/header.svg",
        help="Output SVG file path"
    )
    parser.add_argument(
        "--no-animations",
        action="store_true",
        default=False,
        help="Disable CSS animations for static rendering"
    )

    args = parser.parse_args()

    try:
        generate_header(args.out, args.mock, include_animations=not args.no_animations)
        print(f"✓ Successfully created {args.out}")
    except Exception as e:
        print(f"✗ Error: {e}")
        exit(1)


if __name__ == "__main__":
    main()
