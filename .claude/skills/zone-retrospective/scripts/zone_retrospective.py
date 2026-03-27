#!/usr/bin/env python3
"""Deterministic automation for zone-retrospective skill phases."""

from __future__ import annotations

import argparse
import datetime
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

SENTINEL = "###ZONE-RETRO-RESULT###"


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


def git(args: List[str], cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command, capturing output."""
    cmd = ["git"] + args
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _current_branch(cwd: str) -> str:
    """Return the current branch name."""
    return git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).stdout.strip()


def git_push_with_retry(
    push_args: List[str],
    cwd: str,
    max_retries: int = 5,
) -> subprocess.CompletedProcess:
    """Push to remote, retrying with pull --rebase on behind-remote rejection."""
    for attempt in range(max_retries + 1):
        result = git(["push"] + push_args, cwd=cwd, check=False)
        if result.returncode == 0:
            return result

        stderr_lower = result.stderr.strip().lower()
        is_behind = (
            ("rejected" in stderr_lower and "behind" in stderr_lower)
            or "non-fast-forward" in stderr_lower
        )

        if not is_behind or attempt >= max_retries:
            raise subprocess.CalledProcessError(
                result.returncode, result.args, result.stdout, result.stderr
            )

        branch = _current_branch(cwd)
        rebase = git(["pull", "--rebase", "origin", branch], cwd=cwd, check=False)

        if rebase.returncode != 0:
            git(["rebase", "--abort"], cwd=cwd, check=False)
            merge = git(["pull", "--no-rebase", "origin", branch], cwd=cwd, check=False)

            if merge.returncode != 0:
                git(["merge", "--abort"], cwd=cwd, check=False)
                raise subprocess.CalledProcessError(
                    merge.returncode, merge.args, merge.stdout,
                    f"Both rebase and merge failed: {merge.stderr.strip()}",
                )

        time.sleep(0.5 * (attempt + 1))

    raise RuntimeError("git_push_with_retry: unexpected fall-through")


def emit_json(data: Dict[str, Any]) -> None:
    """Print JSON to stdout."""
    print(json.dumps(data, indent=2))


def die(message: str, code: int = 1) -> None:
    """Print error to stderr and exit."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def _load_items(repo_root: Path):
    """Load jira-key-map.yaml and return (active_project_key, items list)."""
    map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "jira-key-map.yaml"
    data = read_yaml(map_path)
    active_project_key = data.get("active_project_key")
    if not active_project_key:
        die("active_project_key not found in jira-key-map.yaml")
    items = data.get("projects", {}).get(active_project_key, {}).get("items", [])
    return active_project_key, items


def _story_slug(bmad_id: str, bmad_title: str) -> str:
    """Compute the sprint-status.yaml key for a story."""
    return bmad_id.replace(".", "-") + "-" + slugify(bmad_title)


# ---------------------------------------------------------------------------
# sync-superrepo (Phase 0)
# ---------------------------------------------------------------------------

def cmd_sync_superrepo(args: argparse.Namespace) -> int:
    """Phase 0: Pull latest super-repo branch before starting work."""
    cwd = str(Path(args.repo_root).resolve())
    branch = _current_branch(cwd)

    git(["fetch", "origin"], cwd=cwd)
    result = git(["pull", "--rebase", "origin", branch], cwd=cwd, check=False)

    if result.returncode != 0:
        git(["rebase", "--abort"], cwd=cwd, check=False)
        result = git(["pull", "--no-rebase", "origin", branch], cwd=cwd, check=False)

        if result.returncode != 0:
            git(["merge", "--abort"], cwd=cwd, check=False)
            die(f"Failed to sync super-repo branch '{branch}': {result.stderr.strip()}")

    emit_json({"action": "synced", "branch": branch})
    return 0


# ---------------------------------------------------------------------------
# resolve-epic (Phase 1)
# ---------------------------------------------------------------------------

def cmd_resolve_epic(args: argparse.Namespace) -> int:
    """Phase 1: Find epic, verify all stories done, check for existing analysis."""
    repo_root = Path(args.repo_root).resolve()
    epic_jira_key = args.jira_key

    _, items = _load_items(repo_root)

    # Find the epic
    epic = None
    for item in items:
        if item.get("jira_key") == epic_jira_key and item.get("bmad_type") == "epic":
            epic = item
            break

    if epic is None:
        die(f"KEY_NOT_FOUND: Epic '{epic_jira_key}' not found in jira-key-map.yaml")

    epic_bmad_id = str(epic["bmad_id"])
    epic_title = str(epic["bmad_title"])
    epic_slug = epic_bmad_id.replace(".", "-")

    # Find all stories for this epic
    stories = [
        item for item in items
        if item.get("parent_jira_key") == epic_jira_key and item.get("bmad_type") == "story"
    ]

    if not stories:
        die(f"EPIC_NOT_COMPLETE: No stories found for epic '{epic_jira_key}'")

    # Load sprint-status.yaml
    sprint_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    if not sprint_path.exists():
        die("SPRINT_STATUS_MISSING: sprint-status.yaml not found")

    sprint_data = read_yaml(sprint_path)
    dev_status = sprint_data.get("development_status", {})

    # Verify all stories done
    incomplete: List[str] = []
    story_file_paths: List[str] = []
    impl_dir = repo_root / "_bmad-output" / "implementation-artifacts"

    for story in stories:
        s_bmad_id = str(story["bmad_id"])
        s_title = str(story["bmad_title"])
        slug = _story_slug(s_bmad_id, s_title)
        status = dev_status.get(slug)
        if status != "done":
            incomplete.append(f"{story.get('jira_key')} ({slug}): {status!r}")
        story_path = impl_dir / "stories" / f"{slug}.md"
        story_file_paths.append(str(story_path))

    if incomplete:
        die(f"EPIC_NOT_COMPLETE: The following stories are not done: {'; '.join(incomplete)}")

    # Check if analysis already exists
    existing = list(impl_dir.glob(f"epic-{epic_slug}-retro-analysis-*.md"))
    if existing:
        emit_json({
            "action": "ANALYSIS_ALREADY_EXISTS",
            "epic_jira_key": epic_jira_key,
            "epic_bmad_id": epic_bmad_id,
            "epic_slug": epic_slug,
            "epic_title": epic_title,
            "analysis_file": str(existing[0]),
            "status": "0",
        })
        return 0

    # Find previous retro path (previous epic's retro analysis file)
    prev_retro_path: Optional[str] = None
    try:
        current_id = int(float(epic_bmad_id))
        if current_id > 1:
            prev_id = current_id - 1
            prev_candidates = list(impl_dir.glob(f"epic-{prev_id}-retro-analysis-*.md"))
            if prev_candidates:
                prev_retro_path = str(prev_candidates[0])
    except (ValueError, TypeError):
        pass

    # Find next epic bmad_id
    next_epic_bmad_id: Optional[str] = None
    try:
        current_id = int(float(epic_bmad_id))
        for item in items:
            if item.get("bmad_type") == "epic":
                try:
                    if int(float(str(item["bmad_id"]))) == current_id + 1:
                        next_epic_bmad_id = str(item["bmad_id"])
                        break
                except (ValueError, TypeError):
                    pass
    except (ValueError, TypeError):
        pass

    # Compute analysis output path
    date_str = datetime.date.today().isoformat()
    analysis_file = str(impl_dir / f"epic-{epic_slug}-retro-analysis-{date_str}.md")

    emit_json({
        "epic_jira_key": epic_jira_key,
        "epic_bmad_id": epic_bmad_id,
        "epic_title": epic_title,
        "epic_slug": epic_slug,
        "story_file_paths": story_file_paths,
        "analysis_file": analysis_file,
        "prev_retro_path": prev_retro_path,
        "next_epic_bmad_id": next_epic_bmad_id,
        "implementation_artifacts": str(impl_dir),
    })
    return 0


# ---------------------------------------------------------------------------
# check-epic-complete (triggered from human-review orchestrators)
# ---------------------------------------------------------------------------

def cmd_check_epic_complete(args: argparse.Namespace) -> int:
    """Given a story Jira key, check if all epic stories are done and not yet analysed."""
    repo_root = Path(args.repo_root).resolve()
    jira_key = args.jira_key  # story key

    try:
        _, items = _load_items(repo_root)
    except SystemExit:
        emit_json({"epic_complete": False})
        return 0

    # Find the story's parent epic
    parent_jira_key: Optional[str] = None
    for item in items:
        if item.get("jira_key") == jira_key and item.get("bmad_type") == "story":
            parent_jira_key = item.get("parent_jira_key")
            break

    if not parent_jira_key:
        emit_json({"epic_complete": False})
        return 0

    # Find the epic's bmad_id
    epic_bmad_id: Optional[str] = None
    for item in items:
        if item.get("jira_key") == parent_jira_key and item.get("bmad_type") == "epic":
            epic_bmad_id = str(item["bmad_id"])
            break

    if not epic_bmad_id:
        emit_json({"epic_complete": False})
        return 0

    epic_slug = epic_bmad_id.replace(".", "-")

    # Find all stories for this epic
    stories = [
        item for item in items
        if item.get("parent_jira_key") == parent_jira_key and item.get("bmad_type") == "story"
    ]

    if not stories:
        emit_json({"epic_complete": False})
        return 0

    # Load sprint-status.yaml
    sprint_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    if not sprint_path.exists():
        emit_json({"epic_complete": False})
        return 0

    try:
        sprint_data = read_yaml(sprint_path)
    except SystemExit:
        emit_json({"epic_complete": False})
        return 0

    dev_status = sprint_data.get("development_status", {})

    # Check all stories done
    all_done = all(
        dev_status.get(_story_slug(str(s["bmad_id"]), str(s["bmad_title"]))) == "done"
        for s in stories
    )

    # Check if already analyzed or pending
    impl_dir = repo_root / "_bmad-output" / "implementation-artifacts"
    retro_status = dev_status.get(f"epic-{epic_slug}-retro-analysis")
    file_exists = bool(list(impl_dir.glob(f"epic-{epic_slug}-retro-analysis-*.md")))
    already_analyzed = (retro_status in ("done", "pending")) or file_exists

    emit_json({
        "epic_complete": all_done,
        "epic_jira_key": parent_jira_key,
        "epic_bmad_id": epic_bmad_id,
        "already_analyzed": already_analyzed,
    })
    return 0


# ---------------------------------------------------------------------------
# mark-analysis-pending / mark-analysis-done (Phases 2 and 5)
# ---------------------------------------------------------------------------

def _update_retro_analysis_status(repo_root: Path, epic_bmad_id: str, status: str) -> int:
    """Update epic-N-retro-analysis status in sprint-status.yaml using ruamel.yaml."""
    try:
        from ruamel.yaml import YAML  # type: ignore
    except ImportError:
        # Fallback to plain yaml if ruamel not installed
        print("warning: ruamel.yaml not available, falling back to plain yaml edit", file=sys.stderr)
        return _update_retro_analysis_status_plain(repo_root, epic_bmad_id, status)

    sprint_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    if not sprint_path.exists():
        die("SPRINT_STATUS_MISSING: sprint-status.yaml not found")

    ryaml = YAML()
    ryaml.preserve_quotes = True
    ryaml.width = 4096  # prevent line-wrapping

    with sprint_path.open("r", encoding="utf-8") as fh:
        doc = ryaml.load(fh)

    epic_slug = str(epic_bmad_id).replace(".", "-")
    key = f"epic-{epic_slug}-retro-analysis"

    dev_status = doc.get("development_status")
    if dev_status is None:
        die("development_status key not found in sprint-status.yaml")

    dev_status[key] = status

    with sprint_path.open("w", encoding="utf-8") as fh:
        ryaml.dump(doc, fh)

    emit_json({"action": "updated", "key": key, "status": status})
    return 0


def _update_retro_analysis_status_plain(repo_root: Path, epic_bmad_id: str, status: str) -> int:
    """Plain yaml fallback for updating sprint-status.yaml."""
    sprint_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    if not sprint_path.exists():
        die("SPRINT_STATUS_MISSING: sprint-status.yaml not found")

    content = sprint_path.read_text(encoding="utf-8")
    epic_slug = str(epic_bmad_id).replace(".", "-")
    key = f"epic-{epic_slug}-retro-analysis"

    # Try to update existing entry
    pattern = re.compile(rf"^(\s+{re.escape(key)}:\s*)(\S+)$", re.MULTILINE)
    if pattern.search(content):
        content = pattern.sub(rf"\g<1>{status}", content)
    else:
        # Append after the last epic-N line in development_status
        epic_pattern = re.compile(rf"^(\s+epic-{epic_slug}[^:]*:\s*\S+)$", re.MULTILINE)
        matches = list(epic_pattern.finditer(content))
        if matches:
            last_match = matches[-1]
            insert_pos = last_match.end()
            content = content[:insert_pos] + f"\n  {key}: {status}" + content[insert_pos:]
        else:
            # Append to development_status block
            content = content.rstrip() + f"\n  {key}: {status}\n"

    sprint_path.write_text(content, encoding="utf-8")
    emit_json({"action": "updated", "key": key, "status": status})
    return 0


def cmd_mark_analysis_pending(args: argparse.Namespace) -> int:
    """Phase 2: Add epic-N-retro-analysis: pending to sprint-status.yaml."""
    return _update_retro_analysis_status(
        Path(args.repo_root).resolve(),
        args.epic_bmad_id,
        "pending",
    )


def cmd_mark_analysis_done(args: argparse.Namespace) -> int:
    """Phase 5: Set epic-N-retro-analysis: done in sprint-status.yaml."""
    return _update_retro_analysis_status(
        Path(args.repo_root).resolve(),
        args.epic_bmad_id,
        "done",
    )


# ---------------------------------------------------------------------------
# commit-superrepo (Phase 4 and Phase 5 follow-up)
# ---------------------------------------------------------------------------

def cmd_commit_superrepo(args: argparse.Namespace) -> int:
    """Stage _bmad-output/ only and commit + push super-repo."""
    repo_root = Path(args.repo_root).resolve()
    jira_key = args.jira_key
    title = args.title
    cwd = str(repo_root)

    commit_msg = f"{jira_key}: {title} - retro analysis complete"

    # Stage _bmad-output/
    git(["add", "_bmad-output/"], cwd=cwd, check=False)

    # Unstage any modules/ paths (safety guard)
    git(["reset", "HEAD", "modules/"], cwd=cwd, check=False)

    # Check if anything is staged
    diff_result = git(["diff", "--cached", "--name-only"], cwd=cwd, check=False)
    staged = diff_result.stdout.strip()

    if not staged:
        emit_json({
            "action": "skipped",
            "reason": "no staged changes in _bmad-output/",
            "commit_hash": None,
            "branch": None,
            "pushed": False,
        })
        return 0

    try:
        git(["config", "user.name", "Zone AI Agent"], cwd=cwd, check=False)
        git(["config", "user.email", "ai@zonenetwork.com"], cwd=cwd, check=False)
        git(["commit", "-m", commit_msg], cwd=cwd)
        log_result = git(["rev-parse", "HEAD"], cwd=cwd)
        commit_hash = log_result.stdout.strip()

        branch_result = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd)
        branch = branch_result.stdout.strip()

        git_push_with_retry(["origin", "HEAD"], cwd=cwd)

        emit_json({
            "action": "committed_and_pushed",
            "commit_hash": commit_hash,
            "branch": branch,
            "pushed": True,
        })
    except subprocess.CalledProcessError as exc:
        emit_json({
            "action": "error",
            "error": exc.stderr.strip() or exc.stdout.strip(),
            "commit_hash": None,
            "branch": None,
            "pushed": False,
        })
        return 1

    return 0


# ---------------------------------------------------------------------------
# status (Phase 6)
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    """Phase 6: Check analysis status and emit sentinel JSON."""
    repo_root = Path(args.repo_root).resolve()
    epic_jira_key = args.jira_key

    epic_bmad_id_arg = getattr(args, "epic_bmad_id", None)
    if epic_bmad_id_arg:
        epic_bmad_id = str(epic_bmad_id_arg)
    else:
        # Resolve epic_bmad_id from jira_key
        _, items = _load_items(repo_root)
        epic = None
        for item in items:
            if item.get("jira_key") == epic_jira_key and item.get("bmad_type") == "epic":
                epic = item
                break
        if epic is None:
            die(f"Epic '{epic_jira_key}' not found in jira-key-map.yaml")
        epic_bmad_id = str(epic["bmad_id"])

    epic_slug = epic_bmad_id.replace(".", "-")

    impl_dir = repo_root / "_bmad-output" / "implementation-artifacts"
    existing = list(impl_dir.glob(f"epic-{epic_slug}-retro-analysis-*.md"))

    # Check sprint-status.yaml
    sprint_path = impl_dir / "sprint-status.yaml"
    retro_status = None
    if sprint_path.exists():
        try:
            sprint_data = read_yaml(sprint_path)
            dev_status = sprint_data.get("development_status", {})
            retro_status = dev_status.get(f"epic-{epic_slug}-retro-analysis")
        except SystemExit:
            pass

    analysis_done = retro_status == "done" and bool(existing)
    status_val = "0" if analysis_done else "1"
    analysis_file = str(existing[0]) if existing else ""

    result = json.dumps({
        "status": status_val,
        "epic_key": epic_jira_key,
        "analysis_file": analysis_file,
    })
    print(f"{SENTINEL}{result}{SENTINEL}")
    return 0


# ---------------------------------------------------------------------------
# main — argparse dispatcher
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic automation for zone-retrospective skill phases."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # sync-superrepo
    p_sync = subparsers.add_parser("sync-superrepo", help="Phase 0: Pull latest super-repo branch")
    p_sync.add_argument("--repo-root", default=".", help="Repository root directory")

    # resolve-epic
    p_resolve = subparsers.add_parser("resolve-epic", help="Phase 1: Resolve epic and verify all stories done")
    p_resolve.add_argument("--jira-key", required=True, help="Epic Jira key (e.g. CLSDLC-1)")
    p_resolve.add_argument("--repo-root", default=".", help="Repository root directory")

    # check-epic-complete
    p_check = subparsers.add_parser("check-epic-complete", help="Check if all stories in an epic are done (given a story key)")
    p_check.add_argument("--jira-key", required=True, help="Story Jira key (e.g. CLSDLC-101)")
    p_check.add_argument("--repo-root", default=".", help="Repository root directory")

    # mark-analysis-pending
    p_pending = subparsers.add_parser("mark-analysis-pending", help="Phase 2: Set epic retro-analysis status to pending")
    p_pending.add_argument("--epic-bmad-id", required=True, help="Epic BMAD ID (e.g. 1)")
    p_pending.add_argument("--repo-root", default=".", help="Repository root directory")

    # mark-analysis-done
    p_done = subparsers.add_parser("mark-analysis-done", help="Phase 5: Set epic retro-analysis status to done")
    p_done.add_argument("--epic-bmad-id", required=True, help="Epic BMAD ID (e.g. 1)")
    p_done.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-superrepo
    p_commit = subparsers.add_parser("commit-superrepo", help="Phase 4: Commit and push super-repo _bmad-output/ changes")
    p_commit.add_argument("--epic-bmad-id", required=True, help="Epic BMAD ID (e.g. 1)")
    p_commit.add_argument("--jira-key", required=True, help="Epic Jira key")
    p_commit.add_argument("--title", required=True, help="Epic title for commit message")
    p_commit.add_argument("--repo-root", default=".", help="Repository root directory")

    # status
    p_status = subparsers.add_parser("status", help="Phase 6: Output status sentinel")
    p_status.add_argument("--epic-bmad-id", default=None, help="Epic BMAD ID (e.g. 1); resolved from --jira-key if omitted")
    p_status.add_argument("--jira-key", required=True, help="Epic Jira key")
    p_status.add_argument("--repo-root", default=".", help="Repository root directory")

    parsed = parser.parse_args()

    dispatch = {
        "sync-superrepo": cmd_sync_superrepo,
        "resolve-epic": cmd_resolve_epic,
        "check-epic-complete": cmd_check_epic_complete,
        "mark-analysis-pending": cmd_mark_analysis_pending,
        "mark-analysis-done": cmd_mark_analysis_done,
        "commit-superrepo": cmd_commit_superrepo,
        "status": cmd_status,
    }

    handler = dispatch.get(parsed.command)
    if handler is None:
        die(f"Unknown command: {parsed.command}")

    return handler(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
