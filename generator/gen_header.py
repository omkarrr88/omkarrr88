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

    # Colors from tokyonight palette
    bg = "#1a1b27"
    border = "#2f334d"
    blue = "#7aa2f7"
    purple = "#bb9af7"
    cyan = "#7dcfff"
    text_muted = "#565f89"
    text_muted_readable = "#8a93b2"  # Works on both dark and light
    green = "#9ece6a"

    width, height = 920, 160

    # Typing phrases (4 phrases, ~3s each + 1.2s pause per phrase)
    phrases = [
        "Platform Engineer @ Riamona",
        "Full-Stack Developer - React | Node | Python",
        "ML Enthusiast &amp; Automation Builder",
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

    # Defs for gradients
    svg_parts.append("""<defs>
<linearGradient id="nameGradient" x1="0%" y1="0%" x2="100%" y2="0%">
  <stop offset="0%" style="stop-color:#7aa2f7;stop-opacity:0.6" />
  <stop offset="100%" style="stop-color:#bb9af7;stop-opacity:0.6" />
</linearGradient>
</defs>""")

    # Decorative code glyphs on the sides (subtle, muted)
    svg_parts.append(f'<text x="18" y="48" font-family="{MONO}" font-size="20" font-weight="400" fill="{border}" opacity="0.6">&lt;/&gt;</text>')
    svg_parts.append(f'<text x="{width - 48}" y="48" font-family="{MONO}" font-size="20" font-weight="400" fill="{border}" opacity="0.6">{{}}</text>')

    # Main name headline "Omkar Kadam"
    svg_parts.append(f'<text x="65" y="50" font-family="{FONT}" font-size="32" font-weight="700" fill="{blue}">Omkar Kadam</text>')

    # Gradient underline under name
    svg_parts.append(f'<rect x="65" y="58" width="280" height="3" fill="url(#nameGradient)" rx="1.5"/>')

    # Typing animation container
    svg_parts.append(f'<g class="typing-container">')

    # Phrases with typing animation
    if include_animations:
        # Include all phrases for animation cycling
        for i, phrase in enumerate(phrases):
            initial_opacity = "1" if i == 0 else "0"
            svg_parts.append(f'<text x="65" y="105" font-family="{MONO}" font-size="13" font-weight="400" fill="{cyan}" class="phrase-{i}" style="opacity: {initial_opacity}; animation: none;">{phrase}</text>')
    else:
        # Static rendering: only show first phrase
        svg_parts.append(f'<text x="65" y="105" font-family="{MONO}" font-size="13" font-weight="400" fill="{cyan}">{phrases[0]}</text>')

    # Blinking cursor
    svg_parts.append(f'<rect x="580" y="90" width="2.5" height="18" fill="{blue}" class="cursor"/>')

    svg_parts.append('</g>')

    # Bottom section: Location and availability badge
    # Green pulse dot for "available"
    svg_parts.append(f'<circle cx="65" cy="135" r="3.5" fill="{green}" class="pulse-dot"/>')
    svg_parts.append(f'<text x="75" y="140" font-family="{FONT}" font-size="11" font-weight="500" fill="{text_muted_readable}">Available for work</text>')

    # Location
    svg_parts.append(f'<text x="65" y="155" font-family="{FONT}" font-size="11" font-weight="400" fill="{text_muted_readable}">📍 Navi Mumbai, India</text>')

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


# Font definitions from theme
FONT = "'Segoe UI', Ubuntu, 'Helvetica Neue', sans-serif"
MONO = "'Cascadia Code', 'Fira Code', monospace"


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
