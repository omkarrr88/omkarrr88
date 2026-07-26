#!/usr/bin/env python3
"""
GitHub user data loader: real mode via GitHub API (urllib, optional token for GraphQL),
mock mode for testing/CI fallback.

Contract:
  load(mock=False) -> {
    "user": {"name", "login", "followers", "created_at"},
    "stats": {"stars", "commits_total", "commits_year", "prs", "prs_merged", "issues", "contributed_to", "contributions_year"},
    "calendar": [{"date": "YYYY-MM-DD", "count": int}, ...],  # >= 365 entries, oldest first, ends today
    "streak": {"current", "longest", "total", "current_range", "longest_range"},
    "languages": [{"name", "color", "pct"}, ...]  # up to 8, pct floats summing ~100
  }
"""

import os
import json
import math
import time
import urllib.request
import urllib.error
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional

# Built-in language color map (fallback)
LANGUAGE_COLORS = {
    "Python": "3572A5",
    "TypeScript": "3178c6",
    "JavaScript": "f1e05a",
    "Java": "b07219",
    "HTML": "e34c26",
    "CSS": "563d7c",
    "Jupyter Notebook": "DA5B0B",
    "C++": "f34b7d",
    "Solidity": "AA6746",
    "PHP": "4F5D95",
    "Shell": "89e051",
    "Dart": "00B4AB",
}

DEFAULT_COLOR = "7aa2f7"


def _make_request(url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
    """Make a GET request and return response body as string, or None on error."""
    try:
        req = urllib.request.Request(url)
        if headers:
            for key, value in headers.items():
                req.add_header(key, value)
        with urllib.request.urlopen(req, timeout=10) as response:
            return response.read().decode('utf-8')
    except (urllib.error.URLError, urllib.error.HTTPError, Exception) as e:
        print(f"[data.py] Request failed for {url}: {e}")
        return None


def _graphql_request(query: str, token: str) -> Optional[Dict[str, Any]]:
    """Make a GraphQL request to GitHub API with token."""
    url = "https://api.github.com/graphql"
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json",
    }
    body = json.dumps({"query": query}).encode('utf-8')
    try:
        req = urllib.request.Request(url, data=body, headers=headers, method='POST')
        with urllib.request.urlopen(req, timeout=10) as response:
            return json.loads(response.read().decode('utf-8'))
    except (urllib.error.URLError, urllib.error.HTTPError, json.JSONDecodeError, Exception) as e:
        print(f"[data.py] GraphQL request failed: {e}")
        return None


def _get_user_info(login: str) -> Optional[Dict[str, Any]]:
    """Fetch user info from REST API (public, no auth required)."""
    url = f"https://api.github.com/users/{login}"
    response = _make_request(url)
    if response:
        try:
            return json.loads(response)
        except json.JSONDecodeError:
            pass
    return None


def _get_starred_repos_count(login: str, token: Optional[str] = None) -> int:
    """Count starred repos. GraphQL if token, else REST."""
    if token:
        query = f"""
        query {{
          user(login: "{login}") {{
            starredRepositories {{
              totalCount
            }}
          }}
        }}
        """
        result = _graphql_request(query, token)
        if result and "data" in result:
            try:
                return result["data"]["user"]["starredRepositories"]["totalCount"]
            except (KeyError, TypeError):
                pass
    else:
        # REST: starred_url doesn't give us count directly; search API is unreliable.
        # Fallback to 0 for unauthenticated.
        pass
    return 0


def _get_owned_repos(login: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """Fetch all owned (non-fork) repos. GraphQL if token, else REST paginated."""
    repos = []
    if token:
        # GraphQL: fetch all repos with languages
        query = f"""
        query {{
          user(login: "{login}") {{
            repositories(first: 100, ownerAffiliations: OWNER, isFork: false) {{
              nodes {{
                name
                stargazerCount
                languages(first: 10) {{
                  edges {{
                    node {{
                      name
                    }}
                    size
                  }}
                }}
              }}
              pageInfo {{
                hasNextPage
                endCursor
              }}
            }}
          }}
        }}
        """
        result = _graphql_request(query, token)
        if result and "data" in result:
            try:
                repos_data = result["data"]["user"]["repositories"]["nodes"]
                repos.extend(repos_data if repos_data else [])
            except (KeyError, TypeError):
                pass
    else:
        # REST: public repos endpoint
        page = 1
        while True:
            url = f"https://api.github.com/users/{login}/repos?per_page=100&page={page}&type=owner"
            response = _make_request(url)
            if not response:
                break
            try:
                batch = json.loads(response)
                if not isinstance(batch, list) or len(batch) == 0:
                    break
                repos.extend(batch)
                page += 1
            except json.JSONDecodeError:
                break
    return repos


# Languages that dominate byte counts without reflecting actual development work
# (deploy scripts, resume sources) — excluded so the top-8 stays representative.
IGNORED_LANGUAGES = {"Shell", "TeX", "BibTeX Style"}


def _aggregate_language_bytes(repos: List[Dict[str, Any]]) -> Dict[str, int]:
    """Sum bytes by language across repos."""
    lang_bytes = {}
    for repo in repos:
        if "languages" in repo and repo["languages"]:
            edges = repo["languages"].get("edges", [])
            for edge in edges:
                if "node" in edge and "size" in edge:
                    lang_name = edge["node"].get("name", "Unknown")
                    if lang_name in IGNORED_LANGUAGES:
                        continue
                    size = edge["size"]
                    lang_bytes[lang_name] = lang_bytes.get(lang_name, 0) + size
        # REST API repos don't have language breakdowns; would need separate call per repo
        # For now, skip REST language parsing (too costly without bulk endpoint)
    return lang_bytes


def _compute_streak_from_calendar(calendar: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Compute current streak, longest streak, and total contributions from calendar.
    calendar: sorted oldest -> newest, ends today or yesterday.
    """
    if not calendar:
        return {
            "current": 0,
            "longest": 0,
            "total": 0,
            "current_range": "",
            "longest_range": "",
        }

    today = datetime.now().date()
    calendar_dict = {d["date"]: d["count"] for d in calendar}

    # Current streak: consecutive days with count > 0 ending today or yesterday
    current_streak = 0
    current_start = None
    current_end = None
    check_date = today
    # no contribution yet today shouldn't end the streak — start from yesterday
    if calendar_dict.get(today.isoformat(), 0) == 0:
        check_date = today - timedelta(days=1)
    while check_date.isoformat() in calendar_dict:
        if calendar_dict[check_date.isoformat()] > 0:
            current_streak += 1
            if current_end is None:
                current_end = check_date
            current_start = check_date
        else:
            break
        check_date -= timedelta(days=1)

    # Longest streak: scan through calendar and track consecutive contribution days
    longest_streak = 0
    longest_start = None
    longest_end = None
    streak_start = None
    streak_end = None

    for entry in calendar:
        date_str = entry["date"]
        count = entry["count"]

        if count > 0:
            if streak_start is None:
                streak_start = date_str
            streak_end = date_str
        else:
            if streak_start is not None:
                streak_len = (datetime.fromisoformat(streak_end) - datetime.fromisoformat(streak_start)).days + 1
                if streak_len > longest_streak:
                    longest_streak = streak_len
                    longest_start = streak_start
                    longest_end = streak_end
                streak_start = None
                streak_end = None

    # Handle unclosed streak at end of calendar
    if streak_start is not None:
        streak_len = (datetime.fromisoformat(streak_end) - datetime.fromisoformat(streak_start)).days + 1
        if streak_len > longest_streak:
            longest_streak = streak_len
            longest_start = streak_start
            longest_end = streak_end

    current_range = ""
    if current_start and current_end:
        # If the current streak spans multiple days, show range; otherwise just the day
        if current_start == current_end:
            current_range = current_start.strftime('%b %d')
        else:
            current_range = f"{current_start.strftime('%b %d')} - {current_end.strftime('%b %d')}"

    longest_range = ""
    if longest_start and longest_end:
        longest_range = f"{datetime.fromisoformat(longest_start).strftime('%b %d')} - {datetime.fromisoformat(longest_end).strftime('%b %d')}"

    total = sum(d.get("count", 0) for d in calendar)

    return {
        "current": current_streak,
        "longest": longest_streak,
        "total": total,
        "current_range": current_range,
        "longest_range": longest_range,
    }


def _get_contributions_calendar(login: str, token: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Fetch contribution calendar for all years from user creation to today.
    Returns list of {date, count} sorted oldest first.
    """
    if not token:
        return []

    # GraphQL contributionsCollection per year
    # Calculate years from user creation to today
    user_info = _get_user_info(login)
    if not user_info or "created_at" not in user_info:
        return []

    created_date = datetime.fromisoformat(user_info["created_at"].replace('Z', '+00:00')).date()
    today = datetime.now().date()

    calendar = []
    for year in range(created_date.year, today.year + 1):
        from_date = f"{year}-01-01T00:00:00Z"
        # clamp the current year's window to today so no future days come back
        year_end = min(datetime(year, 12, 31).date(), today)
        to_date = f"{year_end.isoformat()}T23:59:59Z"
        query = f"""
        query {{
          user(login: "{login}") {{
            contributionsCollection(from: "{from_date}", to: "{to_date}") {{
              contributionCalendar {{
                totalContributions
                weeks {{
                  contributionDays {{
                    date
                    contributionCount
                  }}
                }}
              }}
            }}
          }}
        }}
        """
        # A silently-missing year once shipped a wrong total (1,014 vs 1,478)
        # to the profile: retry each year, and FAIL LOUD if a year never
        # loads — stale-but-correct committed SVGs beat fresh-but-wrong ones.
        year_days = None
        for attempt in range(3):
            result = _graphql_request(query, token)
            if result and "data" in result:
                try:
                    weeks = result["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
                    year_days = [
                        {"date": day["date"], "count": day["contributionCount"]}
                        for week in weeks
                        for day in week.get("contributionDays", [])
                    ]
                    break
                except (KeyError, TypeError):
                    year_days = None
            time.sleep(1 + attempt)
        if year_days is None:
            raise RuntimeError(f"contribution calendar fetch failed for {year} after 3 attempts")
        calendar.extend(year_days)

    calendar.sort(key=lambda x: x["date"])
    # drop any future-dated days the API may return for the current year
    cutoff = today.isoformat()
    return [c for c in calendar if c["date"] <= cutoff]


def _get_all_contributions_stats(login: str, token: Optional[str] = None) -> Dict[str, int]:
    """
    Fetch total commits, PRs, issues, and contributed repos.
    Requires token for accurate data.
    """
    stats = {
        "commits_total": 0,
        "commits_year": 0,
        "prs": 0,
        "prs_merged": 0,
        "issues": 0,
        "contributed_to": 0,
    }

    if not token:
        return stats

    # Use search API to count commits by login (not author, since we need all contributions)
    # Note: GitHub search has 1000 result limit, so large counts may be capped
    try:
        commit_url = f"https://api.github.com/search/commits?q=author:{login}&per_page=1"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.clojure-preview+json"}
        response = _make_request(commit_url, headers=headers)
        if response:
            data = json.loads(response)
            if "total_count" in data:
                stats["commits_total"] = min(data["total_count"], 32767)  # Cap at practical limit
    except Exception as e:
        print(f"[data.py] Failed to fetch commits: {e}")

    # This year's commits
    year_start = f"{datetime.now().year}-01-01"
    try:
        commit_year_url = f"https://api.github.com/search/commits?q=author:{login}+committer-date:>={year_start}&per_page=1"
        headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github.clojure-preview+json"}
        response = _make_request(commit_year_url, headers=headers)
        if response:
            data = json.loads(response)
            if "total_count" in data:
                stats["commits_year"] = min(data["total_count"], 32767)
    except Exception as e:
        print(f"[data.py] Failed to fetch commits_year: {e}")

    # PRs and issues via GraphQL
    query = f"""
    query {{
      user(login: "{login}") {{
        pullRequests(first: 1) {{
          totalCount
        }}
        issues(first: 1) {{
          totalCount
        }}
      }}
    }}
    """
    result = _graphql_request(query, token)
    if result and "data" in result:
        try:
            stats["prs"] = result["data"]["user"]["pullRequests"]["totalCount"]
            stats["issues"] = result["data"]["user"]["issues"]["totalCount"]
        except (KeyError, TypeError):
            pass

    # Merged PRs (more complex; requires search)
    try:
        merged_url = f"https://api.github.com/search/issues?q=is:pr+author:{login}+is:merged&per_page=1"
        headers = {"Authorization": f"Bearer {token}"}
        response = _make_request(merged_url, headers=headers)
        if response:
            data = json.loads(response)
            if "total_count" in data:
                stats["prs_merged"] = min(data["total_count"], 32767)
    except Exception as e:
        print(f"[data.py] Failed to fetch merged PRs: {e}")

    # Contributed repos (count distinct repos user has contributed to, excluding owned)
    query_contrib = f"""
    query {{
      user(login: "{login}") {{
        repositories(first: 100, isFork: false, affiliations: OWNER) {{
          totalCount
        }}
      }}
    }}
    """
    result_contrib = _graphql_request(query_contrib, token)
    # Approximation: can't easily count all repos contributed to without scanning all PRs
    # Use owned repos as proxy
    if result_contrib and "data" in result_contrib:
        try:
            stats["contributed_to"] = result_contrib["data"]["user"]["repositories"]["totalCount"]
        except (KeyError, TypeError):
            pass

    return stats


def _make_mock_calendar() -> List[Dict[str, Any]]:
    """
    Generate a realistic mock contribution calendar:
    - 400+ days ending today
    - Realistic density (most days 0-3, occasional spikes 5-15)
    - Current streak of 5 days
    - Longest streak somewhere in the past (23 days)
    """
    today = datetime.now().date()
    start = today - timedelta(days=400)
    calendar = []

    # Add longest streak (23 days, ~100 days ago)
    longest_start = today - timedelta(days=150)
    for i in range(23):
        d = longest_start + timedelta(days=i)
        calendar.append({"date": d.isoformat(), "count": 3 + (i % 5)})

    # Add other random days
    import random
    random.seed(42)  # Deterministic for testing
    for i in range(401):
        d = start + timedelta(days=i)
        if not any(c["date"] == d.isoformat() for c in calendar):
            r = random.random()
            if r < 0.3:
                count = 0
            elif r < 0.7:
                count = random.randint(1, 3)
            elif r < 0.9:
                count = random.randint(4, 8)
            else:
                count = random.randint(9, 15)
            calendar.append({"date": d.isoformat(), "count": count})

    # Add current streak (5 days ending today)
    for i in range(5):
        d = today - timedelta(days=4 - i)
        if not any(c["date"] == d.isoformat() for c in calendar):
            calendar.append({"date": d.isoformat(), "count": 2 + i})

    calendar.sort(key=lambda x: x["date"])
    return calendar


def _get_project_stars(repo_path: str) -> Optional[int]:
    """
    Fetch star count for a single repository via REST API.
    Public repos work unauthenticated; uses GITHUB_TOKEN if available.
    Returns None on failure.
    """
    url = f"https://api.github.com/repos/{repo_path}"
    headers = {}
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"

    response = _make_request(url, headers=headers if headers else None)
    if response:
        try:
            data = json.loads(response)
            return data.get("stargazers_count", None)
        except json.JSONDecodeError:
            pass
    return None


def _get_all_project_stars() -> Dict[str, Optional[int]]:
    """
    Fetch star counts for all 6 projects.
    Returns dict mapping project key to star count (None if fetch failed).
    """
    project_repos = {
        "chakravyuh": "UjjwalPardeshi/Chakravyuh",
        "smart-puc": "omkarrr88/Smart_PUC",
        "v2v": "omkarrr88/V2V",
        "movie-recommender": "omkarrr88/movie-recommendation-system",
        "vayunetra": "omkarrr88/VayuNetra",
        "fitness-tracker": "omkarrr88/Fitness-Tracker",
    }

    stars = {}
    for key, repo_path in project_repos.items():
        stars[key] = _get_project_stars(repo_path)

    return stars


def load(mock: bool = False) -> Dict[str, Any]:
    """
    Load GitHub user data for omkarrr88.

    Args:
        mock: If True, return deterministic fixture. If False, fetch real data.

    Returns:
        Dict with user, stats, calendar, streak, languages, project_stars.
        On any error, returns fallback mock data (never hard fails).
    """
    login = "omkarrr88"
    token = os.getenv("GITHUB_TOKEN")

    if mock:
        # Full deterministic fixture
        today = datetime.now().date()
        calendar = _make_mock_calendar()

        return {
            "user": {
                "name": "Omkar Kadam",
                "login": login,
                "followers": 42,
                "public_repos": 17,
                "created_at": "2015-08-15T10:30:00Z",
            },
            "stats": {
                "stars": 128,
                "commits_total": 1247,
                "commits_year": 312,
                "prs": 54,
                "prs_merged": 48,
                "issues": 19,
                "contributed_to": 17,
                "contributions_year": 487,
            },
            "calendar": calendar,
            "streak": _compute_streak_from_calendar(calendar),
            "languages": [
                {"name": "Python", "color": "3572A5", "pct": 32.5},
                {"name": "TypeScript", "color": "3178c6", "pct": 18.2},
                {"name": "JavaScript", "color": "f1e05a", "pct": 15.0},
                {"name": "Java", "color": "b07219", "pct": 8.5},
                {"name": "HTML", "color": "e34c26", "pct": 6.8},
                {"name": "CSS", "color": "563d7c", "pct": 5.2},
                {"name": "Jupyter Notebook", "color": "DA5B0B", "pct": 7.3},
                {"name": "Shell", "color": "89e051", "pct": 6.5},
            ],
            "project_stars": {
                "chakravyuh": 12,
                "smart-puc": 8,
                "v2v": 5,
                "movie-recommender": 3,
                "vayunetra": 2,
                "fitness-tracker": 4,
            },
        }

    # Real mode: fetch from GitHub API
    result = {
        "user": {},
        "stats": {},
        "calendar": [],
        "streak": {"current": 0, "longest": 0, "total": 0, "current_range": "", "longest_range": ""},
        "languages": [],
        "project_stars": {},
    }

    # Fetch user info (public, no auth required)
    user_info = _get_user_info(login)
    if user_info:
        result["user"] = {
            "name": user_info.get("name", login),
            "login": login,
            "followers": user_info.get("followers", 0),
            "public_repos": user_info.get("public_repos", 0),
            "created_at": user_info.get("created_at", ""),
        }
    else:
        # Fallback to mock user if fetch fails
        result["user"] = {
            "name": login,
            "login": login,
            "followers": 0,
            "created_at": "",
        }

    # Fetch stats (mostly requires token)
    stats = _get_all_contributions_stats(login, token)
    stars = _get_starred_repos_count(login, token)
    stats["stars"] = stars
    stats["contributions_year"] = stats.get("commits_year", 0)  # Approximation
    result["stats"] = stats

    # Fetch calendar and compute streaks (requires token)
    if token:
        calendar = _get_contributions_calendar(login, token)
        if calendar:
            result["calendar"] = calendar
            result["streak"] = _compute_streak_from_calendar(calendar)

    # Fetch languages (requires repos, token preferred)
    repos = _get_owned_repos(login, token)
    if repos:
        lang_bytes = _aggregate_language_bytes(repos)
        if lang_bytes:
            total_bytes = sum(lang_bytes.values())
            langs_sorted = sorted(lang_bytes.items(), key=lambda x: x[1], reverse=True)[:8]
            for lang_name, byte_count in langs_sorted:
                pct = (byte_count / total_bytes * 100) if total_bytes > 0 else 0
                if pct < 1.0:
                    continue  # sub-1% rows render as empty bars
                color = LANGUAGE_COLORS.get(lang_name, DEFAULT_COLOR)
                result["languages"].append({
                    "name": lang_name,
                    "color": color,
                    "pct": round(pct, 1),
                })

    # Mock calendar ONLY for token-less local runs. With a token, the fetch
    # either succeeds or raises — mock data must never reach the live profile.
    if not result["calendar"] and not token:
        mock_calendar = _make_mock_calendar()
        result["calendar"] = mock_calendar
        result["streak"] = _compute_streak_from_calendar(mock_calendar)

    if not result["languages"]:
        # No languages fetched; add mock fallback
        result["languages"] = [
            {"name": "Python", "color": "3572A5", "pct": 32.5},
            {"name": "TypeScript", "color": "3178c6", "pct": 18.2},
            {"name": "JavaScript", "color": "f1e05a", "pct": 15.0},
            {"name": "Java", "color": "b07219", "pct": 8.5},
            {"name": "HTML", "color": "e34c26", "pct": 6.8},
            {"name": "CSS", "color": "563d7c", "pct": 5.2},
            {"name": "Jupyter Notebook", "color": "DA5B0B", "pct": 7.3},
            {"name": "Shell", "color": "89e051", "pct": 6.5},
        ]

    # Fetch project star counts (works unauthenticated for public repos)
    result["project_stars"] = _get_all_project_stars()

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Load GitHub user data")
    parser.add_argument("--mock", action="store_true", help="Use mock data instead of API")
    parser.add_argument("--out", type=str, help="Output file path (default: stdout)")
    args = parser.parse_args()

    data = load(mock=args.mock)

    # Print summary JSON
    output = json.dumps(data, indent=2)
    if args.out:
        with open(args.out, 'w') as f:
            f.write(output)
        print(f"Wrote to {args.out}")
    else:
        print(output)
