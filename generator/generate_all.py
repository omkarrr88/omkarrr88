#!/usr/bin/env python3
"""
Orchestrator for all GitHub profile card generators.

Loads data once, runs all generators in sequence, handles partial failures gracefully.
Exits nonzero only if ALL cards failed (partial failure: keep going, old svg survives).

Usage:
  python3 generator/generate_all.py --mock              # Use mock data
  python3 generator/generate_all.py                      # Use real GitHub API (requires GITHUB_TOKEN env var)
  python3 generator/generate_all.py --out-dir profile    # Specify output directory
"""

import argparse
import os
import sys
from pathlib import Path
from typing import Dict, Any, List, Tuple

# Add current directory to path for module imports
sys.path.insert(0, str(Path(__file__).parent))

from data import load as load_data
from theme import apply_theme

# Import all generators (they must have render(data, out_path) function)
import gen_header
import gen_stats
import gen_languages
import gen_streak
import gen_weekday
import gen_activity
import gen_achievements
import gen_connect
import gen_projects
import gen_tech
import gen_sections
import gen_trophies
import gen_growth
import gen_terminal
import gen_snake


def render_all(data: Dict[str, Any], out_dir: str = "profile", theme: str = "dark") -> Tuple[int, List[Tuple[str, bool, str]]]:
    """
    Render all cards using pre-loaded data.

    Args:
        data: Shared data dict from data.load()
        out_dir: Base output directory for all SVGs
        theme: Theme name ('dark' or 'light')

    Returns:
        Tuple of (exit_code, results_list)
        results_list: List of (card_name, success, message)
        exit_code: 0 if any succeeded, 1 if all failed
    """
    results: List[Tuple[str, bool, str]] = []

    # Apply theme
    apply_theme(theme)

    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)

    # Define cards to render: (name, generator_module, function, out_path)
    cards = [
        ("header", gen_header, lambda data, path: gen_header.render(data, path), f"{out_dir}/header.svg"),
        ("stats", gen_stats, lambda data, path: gen_stats.render(data, path), f"{out_dir}/stats.svg"),
        ("languages", gen_languages, lambda data, path: gen_languages.render(data, path), f"{out_dir}/languages.svg"),
        ("streak", gen_streak, lambda data, path: gen_streak.render(data, path), f"{out_dir}/streak.svg"),
        ("weekday", gen_weekday, lambda data, path: gen_weekday.render(data, path), f"{out_dir}/weekday.svg"),
        ("trophies", gen_trophies, lambda data, path: gen_trophies.render(data, path), f"{out_dir}/trophies.svg"),
        ("growth", gen_growth, lambda data, path: gen_growth.render(data, path), f"{out_dir}/growth.svg"),
        ("terminal", gen_terminal, lambda data, path: gen_terminal.render(data, path), f"{out_dir}/terminal.svg"),
        ("activity", gen_activity, lambda data, path: gen_activity.render(data, path), f"{out_dir}/activity.svg"),
        ("snake", gen_snake, lambda data, path: gen_snake.render(data, path), f"{out_dir}/snake.svg"),
        ("achievements", gen_achievements, lambda data, path: gen_achievements.render(data, path), f"{out_dir}/achievements.svg"),
    ]

    # Render single-file cards
    for card_name, gen_mod, render_fn, out_path in cards:
        try:
            render_fn(data, out_path)
            results.append((card_name, True, out_path))
            print(f"✓ {card_name:20} → {out_path}")
        except Exception as e:
            results.append((card_name, False, str(e)))
            print(f"✗ {card_name:20} FAILED: {e}")

    # Multi-file cards: connect badges
    try:
        gen_connect.render_all(data, out_dir)
        connect_files = [
            f"{out_dir}/connect-email.svg",
            f"{out_dir}/connect-instagram.svg",
            f"{out_dir}/connect-linkedin.svg",
            f"{out_dir}/connect-portfolio.svg",
            f"{out_dir}/connect-resume.svg",
            f"{out_dir}/connect-x.svg",
        ]
        results.append(("connect", True, f"{len(connect_files)} files"))
        print(f"✓ {'connect':20} → {len(connect_files)} badge files")
    except Exception as e:
        results.append(("connect", False, str(e)))
        print(f"✗ {'connect':20} FAILED: {e}")

    # Multi-file cards: projects
    try:
        gen_projects.render_all(data, out_dir)
        project_files = [
            f"{out_dir}/project-chakravyuh.svg",
            f"{out_dir}/project-v2v.svg",
            f"{out_dir}/project-face-attendance.svg",
            f"{out_dir}/project-movie-recommender.svg",
            f"{out_dir}/project-fitness-tracker.svg",
            f"{out_dir}/project-smart-puc.svg",
        ]
        results.append(("projects", True, f"{len(project_files)} files"))
        print(f"✓ {'projects':20} → {len(project_files)} project files")
    except Exception as e:
        results.append(("projects", False, str(e)))
        print(f"✗ {'projects':20} FAILED: {e}")

    # Single large card: tech
    try:
        gen_tech.render(data, f"{out_dir}/tech.svg")
        results.append(("tech", True, f"{out_dir}/tech.svg"))
        print(f"✓ {'tech':20} → {out_dir}/tech.svg")
    except Exception as e:
        results.append(("tech", False, str(e)))
        print(f"✗ {'tech':20} FAILED: {e}")

    # Multi-file cards: section banners
    try:
        gen_sections.render_all(data, out_dir)
        section_files = [
            f"{out_dir}/section-about.svg",
            f"{out_dir}/section-connect.svg",
            f"{out_dir}/section-tech.svg",
            f"{out_dir}/section-projects.svg",
            f"{out_dir}/section-stats.svg",
            f"{out_dir}/section-snake.svg",
        ]
        results.append(("sections", True, f"{len(section_files)} files"))
        print(f"✓ {'sections':20} → {len(section_files)} section banner files")
    except Exception as e:
        results.append(("sections", False, str(e)))
        print(f"✗ {'sections':20} FAILED: {e}")

    # Summary
    successful = sum(1 for _, success, _ in results if success)
    total = len(results)
    print(f"\n{'='*60}")
    print(f"Summary: {successful}/{total} card groups rendered successfully")

    # Exit code: 0 if any succeeded, 1 only if ALL failed
    exit_code = 0 if successful > 0 else 1
    return exit_code, results


def main():
    parser = argparse.ArgumentParser(
        description="Generate all GitHub profile SVG cards",
        epilog="Data is loaded once and passed to all generators for efficiency."
    )
    parser.add_argument(
        "--mock",
        action="store_true",
        help="Use mock data instead of real GitHub API (useful for testing/CI)"
    )
    parser.add_argument(
        "--out-dir",
        type=str,
        default="profile",
        help="Base output directory for all SVG files (default: profile/)"
    )

    args = parser.parse_args()

    # Load data once
    print(f"Loading GitHub data (mock={args.mock})...")
    try:
        data = load_data(mock=args.mock)
        print(f"✓ Data loaded: user={data.get('user', {}).get('login', '?')}, "
              f"stats={len(data.get('stats', {}))}, "
              f"calendar={len(data.get('calendar', []))}, "
              f"languages={len(data.get('languages', []))}")
    except Exception as e:
        print(f"✗ Failed to load data: {e}")
        return 1


    # Append today's snapshot to the growth history (real runs only; mock
    # runs must stay deterministic and never dirty the repo)
    if not args.mock:
        try:
            import json as _json
            from datetime import datetime as _dt, timezone as _tz
            hist_path = os.path.join(args.out_dir, "history.json")
            try:
                with open(hist_path) as _f:
                    history = _json.load(_f)
            except Exception:
                history = []
            today = _dt.now(_tz.utc).date().isoformat()
            # CI-only: local tokens may lack private-contribution visibility
            # (a local run once recorded 1,014 vs the true 1,478), and only
            # the Actions classic PAT sees the full calendar.
            snapshot_ok = (
                os.environ.get("GITHUB_ACTIONS") == "true"
                and len(data.get("calendar", [])) >= 300
                and data.get("streak", {}).get("total", 0) > 0
            )
            if snapshot_ok and not any(e.get("date") == today for e in history):
                history.append({
                    "date": today,
                    "followers": data.get("user", {}).get("followers", 0),
                    "stars": data.get("stats", {}).get("stars", 0),
                    "contributions": data.get("streak", {}).get("total", 0),
                })
                history.sort(key=lambda e: e["date"])
                with open(hist_path, "w") as _f:
                    _json.dump(history, _f, indent=1)
                print(f"✓ History snapshot appended for {today} ({len(history)} total)")
        except Exception as e:
            print(f"! History append failed (non-fatal): {e}")

    print()

    # Render dark theme (original location: profile/)
    print(f"Rendering dark theme to {args.out_dir}...")
    exit_code_dark, results_dark = render_all(data, args.out_dir, theme="dark")

    print()

    # Render light theme (new location: profile/light/)
    light_out_dir = os.path.join(args.out_dir, "light")
    print(f"Rendering light theme to {light_out_dir}...")
    exit_code_light, results_light = render_all(data, light_out_dir, theme="light")

    # Return 0 only if both succeeded
    exit_code = 0 if (exit_code_dark == 0 and exit_code_light == 0) else 1

    print(f"\n{'='*60}")
    print(f"Dark theme:  {sum(1 for _, s, _ in results_dark if s)}/{len(results_dark)} card groups")
    print(f"Light theme: {sum(1 for _, s, _ in results_light if s)}/{len(results_light)} card groups")

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
