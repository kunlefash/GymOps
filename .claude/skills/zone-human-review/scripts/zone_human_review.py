#!/usr/bin/env python3
"""Deterministic automation for zone-human-review skill: fetch-pr-comments and status commands."""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from base64 import b64encode
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SENTINEL = "###ZONE-HUMAN-REVIEW-RESULT###"

# Matches: - [ ] [Human-Review][CRITICAL/HIGH/MEDIUM] ...
HUMAN_REVIEW_TASK_RE = re.compile(
    r"^- \[ \] \[Human-Review\]\[(CRITICAL|HIGH|MEDIUM)\]",
    re.MULTILINE,
)

# GitHub PR URL pattern
PR_URL_RE = re.compile(
    r"https://github\.org/([^/]+)/([^/]+)/pull-requests/(\d+)"
)


# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

def read_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file; return empty dict if missing or empty."""
    if not path.exists():
        die(f"YAML file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def slugify(text: str) -> str:
    """Lowercase, replace non-alphanumeric with hyphens, collapse, strip."""
    result = text.lower()
    result = re.sub(r"[^a-z0-9]+", "-", result)
    result = re.sub(r"-{2,}", "-", result)
    return result.strip("-")


def _resolve_story_file(story_key: str, repo_root: Path) -> Path:
    """Resolve a story key to its story file path via story-key-map.yaml."""
    map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "story-key-map.yaml"
    data = read_yaml(map_path)
    active_project_key = data.get("active_project_key")
    if not active_project_key:
        die("active_project_key not found in story-key-map.yaml")
    items = data.get("projects", {}).get(active_project_key, {}).get("items", [])
    bmad_id = None
    bmad_title = None
    for item in items:
        if item.get("story_key") == story_key and item.get("bmad_type") == "story":
            bmad_id = str(item["bmad_id"])
            bmad_title = str(item["bmad_title"])
            break
    if bmad_id is None:
        die(f"story key '{story_key}' not found as story in story-key-map.yaml")
    story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)
    return repo_root / "_bmad-output" / "implementation-artifacts" / "stories" / f"{story_key}.md"


def emit_json(data: Dict[str, Any]) -> None:
    """Print JSON to stdout."""
    print(json.dumps(data, indent=2))


def die(message: str, code: int = 1) -> None:
    """Print error JSON to stderr and exit."""
    print(json.dumps({"error": message}), file=sys.stderr)
    sys.exit(code)


def _resolve_bb_auth() -> Optional[str]:
    """Resolve GitHub auth header. Prefers API token; falls back to app password."""
    bb_email = os.environ.get("BB_EMAIL", "")
    bb_token = os.environ.get("BB_API_TOKEN", "")
    if bb_email and bb_token:
        return "Basic " + b64encode(f"{bb_email}:{bb_token}".encode()).decode()

    bb_user = os.environ.get("BB_USERNAME", "")
    bb_pass = os.environ.get("BB_APP_PASSWORD", "")
    if bb_user and bb_pass:
        print(
            "warning: using legacy BB_USERNAME/BB_APP_PASSWORD; "
            "migrate to BB_EMAIL/BB_API_TOKEN before June 2026",
            file=sys.stderr,
        )
        return "Basic " + b64encode(f"{bb_user}:{bb_pass}".encode()).decode()

    return None


def _bb_get(url: str, auth_header: str) -> Any:
    """Perform an authenticated GET to the GitHub API; return parsed JSON."""
    req = urllib.request.Request(
        url,
        headers={
            "Authorization": auth_header,
            "Accept": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code}: {body}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Network error: {exc.reason}") from exc


# ---------------------------------------------------------------------------
# Command: fetch-pr-comments
# ---------------------------------------------------------------------------

def cmd_fetch_pr_comments(args: argparse.Namespace) -> int:
    """Fetch all non-deleted comments from a GitHub PR and emit JSON.

    Auth: BB_EMAIL + BB_API_TOKEN (preferred) or BB_USERNAME + BB_APP_PASSWORD.
    Paginates via the 'next' link until all pages are exhausted.

    Output JSON:
      {
        "workspace": "...", "repo_slug": "...", "pr_id": N,
        "comment_count": N,
        "comments": [
          {
            "id": N,
            "author": "Display Name",
            "content": "...",
            "inline": {"path": "src/Foo.cs", "line": 42},  // null if top-level comment
            "created_on": "..."
          }
        ]
      }
    """
    pr_url = args.pr_url

    # Parse PR URL
    m = PR_URL_RE.match(pr_url.strip())
    if not m:
        die(
            f"Cannot parse PR URL '{pr_url}'. "
            "Expected: https://github.org/{{workspace}}/{{repo_slug}}/pull-requests/{{pr_id}}"
        )

    workspace = m.group(1)
    repo_slug = m.group(2)
    pr_id = int(m.group(3))

    # Resolve auth
    auth_header = _resolve_bb_auth()
    if auth_header is None:
        die(
            "GitHub credentials not configured. "
            "Set BB_EMAIL + BB_API_TOKEN, or BB_USERNAME + BB_APP_PASSWORD."
        )

    # Paginate through all comments
    base_url = (
        f"https://api.github.org/2.0/repositories/"
        f"{workspace}/{repo_slug}/pullrequests/{pr_id}/comments"
        f"?pagelen=100"
    )

    all_comments: List[Dict[str, Any]] = []
    next_url: Optional[str] = base_url

    while next_url:
        try:
            page = _bb_get(next_url, auth_header)
        except RuntimeError as exc:
            die(f"Failed to fetch PR comments: {exc}")

        values = page.get("values", [])
        for raw in values:
            # Skip deleted comments
            if raw.get("deleted", False):
                continue

            # Extract inline context (file path + line)
            inline = raw.get("inline")
            inline_info: Optional[Dict[str, Any]] = None
            if inline:
                inline_info = {
                    "path": inline.get("path"),
                    "line": inline.get("to") or inline.get("from"),
                }

            # Extract author display name
            author_info = raw.get("user") or {}
            author = author_info.get("display_name") or author_info.get("nickname") or "Unknown"

            # Extract comment content
            content_info = raw.get("content") or {}
            content = content_info.get("raw") or content_info.get("markup") or ""

            all_comments.append({
                "id": raw.get("id"),
                "author": author,
                "content": content,
                "inline": inline_info,
                "created_on": raw.get("created_on", ""),
            })

        next_url = page.get("next")

    result = {
        "workspace": workspace,
        "repo_slug": repo_slug,
        "pr_id": pr_id,
        "comment_count": len(all_comments),
        "comments": all_comments,
    }
    emit_json(result)
    return 0


# ---------------------------------------------------------------------------
# Command: status
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    """Read story file and emit the human-review sentinel.

    Scans for:
      - [ ] [Human-Review][CRITICAL] ...
      - [ ] [Human-Review][HIGH] ...
      - [ ] [Human-Review][MEDIUM] ...

    status="0" (PASS) when critical + high + medium == 0.
    status="1" (FAIL) when any unchecked items exist.
    """
    story_file_arg = getattr(args, "story_file", None)
    if story_file_arg:
        story_file = Path(story_file_arg)
    else:
        story_file = _resolve_story_file(args.story_key, Path(args.repo_root).resolve())

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")

    # Only count items within the Human Code Review section
    # Find the section if present
    section_start = content.find("### Human Code Review")
    if section_start == -1:
        # No human review section found — treat as no items
        result = json.dumps({
            "status": "0",
            "comment_count": 0,
            "critical": 0,
            "high": 0,
            "medium": 0,
        })
        print(f"{SENTINEL}{result}{SENTINEL}")
        return 0

    # Find section end (next ### heading or EOF)
    section_text = content[section_start:]
    next_section = re.search(r"\n### ", section_text[4:])  # skip past current ###
    if next_section:
        section_text = section_text[: next_section.start() + 1]

    counts: Dict[str, int] = {"CRITICAL": 0, "HIGH": 0, "MEDIUM": 0}
    for match in HUMAN_REVIEW_TASK_RE.finditer(section_text):
        severity = match.group(1)
        counts[severity] = counts.get(severity, 0) + 1

    critical = counts["CRITICAL"]
    high = counts["HIGH"]
    medium = counts["MEDIUM"]
    comment_count = critical + high + medium
    status = "0" if comment_count == 0 else "1"

    result = json.dumps({
        "status": status,
        "comment_count": comment_count,
        "critical": critical,
        "high": high,
        "medium": medium,
    })
    print(f"{SENTINEL}{result}{SENTINEL}")
    return 0


# ---------------------------------------------------------------------------
# main — argparse dispatcher
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic automation for zone-human-review skill."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # fetch-pr-comments
    p_fetch = subparsers.add_parser(
        "fetch-pr-comments",
        help="Fetch all non-deleted comments from a GitHub PR",
    )
    p_fetch.add_argument(
        "--pr-url",
        required=True,
        help="Full GitHub PR URL (https://github.org/{workspace}/{repo}/pull-requests/{id})",
    )
    p_fetch.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory (unused; kept for CLI consistency)",
    )

    # status
    p_status = subparsers.add_parser(
        "status",
        help="Emit human-review sentinel from story file",
    )
    p_status.add_argument(
        "--story-file",
        default=None,
        help="Path to BMAD story markdown file",
    )
    p_status.add_argument(
        "--story-key",
        default=None,
        help="story key (fallback resolution when --story-file omitted)",
    )
    p_status.add_argument(
        "--repo-root",
        default=".",
        help="Repository root directory",
    )

    parsed = parser.parse_args()

    dispatch = {
        "fetch-pr-comments": cmd_fetch_pr_comments,
        "status": cmd_status,
    }

    handler = dispatch.get(parsed.command)
    if handler is None:
        die(f"Unknown command: {parsed.command}")

    return handler(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
