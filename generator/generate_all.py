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

# Import all generators (they must have render(data, out_path) function)
import gen_header
import gen_stats
import gen_languages
import gen_streak
import gen_activity
import gen_achievements
import gen_connect
import gen_projects
import gen_tech


def render_all(data: Dict[str, Any], out_dir: str = "profile") -> Tuple[int, List[Tuple[str, bool, str]]]:
    """
    Render all cards using pre-loaded data.

    Args:
        data: Shared data dict from data.load()
        out_dir: Base output directory for all SVGs

    Returns:
        Tuple of (exit_code, results_list)
        results_list: List of (card_name, success, message)
        exit_code: 0 if any succeeded, 1 if all failed
    """
    results: List[Tuple[str, bool, str]] = []

    # Ensure output directory exists
    os.makedirs(out_dir, exist_ok=True)

    # Define cards to render: (name, generator_module, function, out_path)
    cards = [
        ("header", gen_header, lambda data, path: gen_header.render(data, path), f"{out_dir}/header.svg"),
        ("stats", gen_stats, lambda data, path: gen_stats.render(data, path), f"{out_dir}/stats.svg"),
        ("languages", gen_languages, lambda data, path: gen_languages.render(data, path), f"{out_dir}/languages.svg"),
        ("streak", gen_streak, lambda data, path: gen_streak.render(data, path), f"{out_dir}/streak.svg"),
        ("activity", gen_activity, lambda data, path: gen_activity.render(data, path), f"{out_dir}/activity.svg"),
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

    print()

    # Render all cards
    exit_code, results = render_all(data, args.out_dir)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
