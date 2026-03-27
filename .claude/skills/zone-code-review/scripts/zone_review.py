#!/usr/bin/env python3
"""Deterministic automation for zone-code-review skill phases 1, 2, 4, 4.5, 4.6–4.8, 5."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.request
import urllib.error
from base64 import b64encode
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

SENTINEL = "###ZONE-REVIEW-RESULT###"
MODULE_REF_RE = re.compile(r"modules/([\w.]+)")
UNCHECKED_RE = re.compile(r"- \[ \]")

# ---------------------------------------------------------------------------
# E2E test repo auto-include
# ---------------------------------------------------------------------------
# zoneqa_automation is the single canonical Playwright repo for all E2E and
# API tests across the platform.  It is never referenced directly in story
# task lists (which name source modules), so it must be injected automatically
# whenever a story touches any testable source module.
E2E_TEST_REPO = "zoneqa_automation"
E2E_TRIGGER_MODULES = {
    "zone.zonepay", "zone.pggateway", "zone.zonepaypwa",
    "zone.cardlesstransactionprocessing", "zonepay.settlement",
    "zone.zonepay.notifications", "zone.framework", "zone.framework.v3",
    "zone.clientdashboard", "zone.zonepay.qrrouter",
    "zone.admin.api", "zone.orchestrator",
    "zone.sui.sdk", "zone.sui.indexer", "zone.settlement.sui",
    "zonedc.settlement", "zone.smartcontracts.sui",
}
# Matches "**Issues Found:** [X Critical,] Y High, Z Medium, W Low"
# or      "**Issues Found:** CRITICAL=X, HIGH=Y, MEDIUM=Z, LOW=W"
ISSUES_FOUND_RE = re.compile(
    r"\*\*Issues Found:\*\*\s*"
    r"(?:"
    r"(?:(\d+)\s*Critical,\s*)?(\d+)\s*High,\s*(\d+)\s*Medium,\s*(\d+)\s*Low"
    r"|"
    r"CRITICAL\s*=\s*(\d+),\s*HIGH\s*=\s*(\d+),\s*MEDIUM\s*=\s*(\d+),\s*LOW\s*=\s*(\d+)"
    r")",
    re.IGNORECASE,
)
# Indicates review report was written to story
REVIEW_REPORT_MARKER = "**Issues Found:**"
SKILL_MAP_FILENAME = "submodule-skill-map.yaml"


def _resolve_story_file(jira_key: str, repo_root: Path) -> Path:
    """Resolve a Jira key to its story file path via jira-key-map.yaml."""
    map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "jira-key-map.yaml"
    data = read_yaml(map_path)
    active_project_key = data.get("active_project_key")
    if not active_project_key:
        die("active_project_key not found in jira-key-map.yaml")
    items = data.get("projects", {}).get(active_project_key, {}).get("items", [])
    bmad_id = None
    bmad_title = None
    for item in items:
        if item.get("jira_key") == jira_key and item.get("bmad_type") == "story":
            bmad_id = str(item["bmad_id"])
            bmad_title = str(item["bmad_title"])
            break
    if bmad_id is None:
        die(f"Jira key '{jira_key}' not found as story in jira-key-map.yaml")
    story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)
    return repo_root / "_bmad-output" / "implementation-artifacts" / "stories" / f"{story_key}.md"


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
    """Push to remote, retrying with pull --rebase on behind-remote rejection.

    When multiple agents push to the same branch concurrently, the first
    succeeds but later ones are rejected.  This detects the rejection,
    runs git pull --rebase (with merge fallback), and retries.
    """
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

        # Try rebase first (cleanest history)
        branch = _current_branch(cwd)
        rebase = git(["pull", "--rebase", "origin", branch], cwd=cwd, check=False)

        if rebase.returncode != 0:
            # Abort failed rebase, try merge as fallback
            git(["rebase", "--abort"], cwd=cwd, check=False)
            merge = git(["pull", "--no-rebase", "origin", branch], cwd=cwd, check=False)

            if merge.returncode != 0:
                git(["merge", "--abort"], cwd=cwd, check=False)
                raise subprocess.CalledProcessError(
                    merge.returncode, merge.args, merge.stdout,
                    f"Both rebase and merge failed: {merge.stderr.strip()}",
                )

        time.sleep(0.5 * (attempt + 1))  # linear back-off

    raise RuntimeError("git_push_with_retry: unexpected fall-through")


def emit_json(data: Dict[str, Any]) -> None:
    """Print JSON to stdout."""
    print(json.dumps(data, indent=2))


def die(message: str, code: int = 1) -> None:
    """Print error to stderr and exit."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


# ---------------------------------------------------------------------------
# Domain skill resolution
# ---------------------------------------------------------------------------

def resolve_domain_skills(submodule_names: List[str], repo_root: Path) -> List[Dict[str, Any]]:
    """Map submodule names to domain skills via submodule-skill-map.yaml.

    Returns a deduplicated list of dicts: {skill, path, exists}.
    Gracefully returns [] with a stderr warning if the map file is missing.
    """
    script_dir = Path(__file__).resolve().parent.parent
    map_path = script_dir / SKILL_MAP_FILENAME

    if not map_path.exists():
        print(f"warning: skill map not found: {map_path}", file=sys.stderr)
        return []

    with map_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    mappings = data.get("mappings", {}) if isinstance(data, dict) else {}

    seen: set[str] = set()
    result: List[Dict[str, Any]] = []
    skills_base = repo_root / ".claude" / "skills"

    for name in submodule_names:
        for skill in mappings.get(name, []):
            if skill in seen:
                continue
            seen.add(skill)
            skill_path = skills_base / skill / "SKILL.md"
            result.append({
                "skill": skill,
                "path": str(skill_path),
                "exists": skill_path.exists(),
            })

    return result


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
# resolve (Phase 1)
# ---------------------------------------------------------------------------

def cmd_resolve(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    jira_key = args.jira_key

    map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "jira-key-map.yaml"
    data = read_yaml(map_path)

    active_project_key = data.get("active_project_key")
    if not active_project_key:
        die("active_project_key not found in jira-key-map.yaml")

    projects = data.get("projects", {})
    project = projects.get(active_project_key, {})
    items = project.get("items", [])

    bmad_id = None
    bmad_title = None
    for item in items:
        if item.get("jira_key") == jira_key and item.get("bmad_type") == "story":
            bmad_id = str(item["bmad_id"])
            bmad_title = str(item["bmad_title"])
            break

    if bmad_id is None:
        die(f"Jira key '{jira_key}' not found in jira-key-map.yaml (project={active_project_key})")

    # Look up the parent epic for epic branch resolution
    parent_jira_key = None
    epic_key = None
    epic_branch = None
    for item in items:
        if item.get("jira_key") == jira_key and item.get("bmad_type") == "story":
            parent_jira_key = item.get("parent_jira_key")
            break

    if parent_jira_key:
        for item in items:
            if item.get("bmad_type") == "epic" and item.get("jira_key") == parent_jira_key:
                epic_bmad_id = str(item["bmad_id"]).replace(".", "-")
                epic_key = epic_bmad_id + "-" + slugify(str(item["bmad_title"]))
                epic_branch = f"agent/epic/{parent_jira_key}-{epic_key}"
                break

    # Derive story_key: dots→dashes in bmad_id + '-' + slugify(title)
    story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)
    story_branch = f"agent/story/{jira_key}-{story_key}"

    story_file_path = (
        repo_root
        / "_bmad-output"
        / "implementation-artifacts"
        / "stories"
        / f"{story_key}.md"
    )

    if not story_file_path.exists():
        emit_json({
            "error": f"Story file not found: {story_file_path}",
            "status": "1",
        })
        return 1

    result_data = {
        "bmad_id": bmad_id,
        "bmad_title": bmad_title,
        "story_key": story_key,
        "story_branch": story_branch,
        "story_file_path": str(story_file_path),
        "jira_key": jira_key,
    }
    if epic_branch:
        result_data["epic_branch"] = epic_branch
        result_data["epic_key"] = epic_key
        result_data["parent_jira_key"] = parent_jira_key

    emit_json(result_data)
    return 0


PREWARM_MAX_WORKERS = int(os.environ.get("PREWARM_WORKERS", "4"))


# ---------------------------------------------------------------------------
# prepare-branches (Phase 2)
# ---------------------------------------------------------------------------

def _prepare_one_submodule(name, repo_root, story_branch, checkout_only=False, target_branches=None):
    """Prepare a single submodule: shallow init, targeted fetch, checkout.

    Returns a dict with path, status, created keys.
    """
    sub_path = repo_root / "modules" / name
    entry: Dict[str, Any] = {"path": f"modules/{name}", "status": "ok", "created": False}

    try:
        # Initialize submodule with shallow clone
        git(["submodule", "update", "--init", "--depth", "1", f"modules/{name}"], cwd=str(repo_root))
    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"submodule init failed: {exc.stderr.strip()}"
        return entry

    sub_dir = str(sub_path)
    git(["config", "user.name", "Zone AI Agent"], cwd=sub_dir)
    git(["config", "user.email", "ai@zonenetwork.com"], cwd=sub_dir)

    try:
        # Targeted fetch for specific branches
        if target_branches:
            for branch in target_branches:
                git(["fetch", "origin", branch], cwd=sub_dir, check=False)
        else:
            git(["fetch", "origin"], cwd=sub_dir)
    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"fetch failed: {exc.stderr.strip()}"
        return entry

    if not checkout_only:
        # Deepen for diff context (code review needs history)
        git(["fetch", "origin", "--deepen", "50"], cwd=sub_dir, check=False)

    try:
        # Check if story_branch exists on remote
        ls_result = git(
            ["ls-remote", "--heads", "origin", story_branch],
            cwd=sub_dir,
        )
        remote_exists = bool(ls_result.stdout.strip())

        if remote_exists:
            git(["checkout", story_branch], cwd=sub_dir)
            git(["pull", "origin", story_branch], cwd=sub_dir)
            entry["status"] = "checked_out_remote"
        else:
            # Check if local branch exists
            local_check = git(
                ["rev-parse", "--verify", story_branch],
                cwd=sub_dir,
                check=False,
            )
            if local_check.returncode == 0:
                git(["checkout", story_branch], cwd=sub_dir)
                entry["status"] = "checked_out_local"
            elif checkout_only:
                entry["status"] = "skipped"
                entry["reason"] = "branch not found (checkout-only)"
            else:
                git(["checkout", "-b", story_branch], cwd=sub_dir)
                entry["status"] = "created"
                entry["created"] = True

    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"branch checkout failed: {exc.stderr.strip()}"

    return entry


def cmd_prepare_branches(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    story_branch = args.story_branch
    story_file = Path(args.story_file)
    checkout_only = getattr(args, "checkout_only", False)

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")

    # Extract modules/<name> references, deduplicate, filter to existing dirs
    matches = MODULE_REF_RE.findall(content)
    seen = set()
    submodule_names = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            submodule_names.append(m)

    # Auto-include zoneqa_automation when any testable source module is present.
    # This repo is never cited directly in story task lists (which name source
    # modules), so it must be injected here to ensure E2E/API tests are checked
    # out and reviewed alongside unit/integration tests in source submodules.
    if E2E_TEST_REPO not in seen and seen & E2E_TRIGGER_MODULES:
        seen.add(E2E_TEST_REPO)
        submodule_names.append(E2E_TEST_REPO)

    valid_names = [n for n in submodule_names if (repo_root / "modules" / n).is_dir()]
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=PREWARM_MAX_WORKERS) as pool:
        futures = {
            pool.submit(
                _prepare_one_submodule, name, repo_root,
                story_branch, checkout_only, [story_branch],
            ): name
            for name in valid_names
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Resolve domain skills from successfully checked-out submodules (exclude error and skipped)
    prepared_names = [
        Path(r["path"]).name for r in results
        if r["status"] not in ("error", "skipped")
    ]
    domain_skills = resolve_domain_skills(prepared_names, repo_root)

    # Tag the e2e test repo entry so Phase 3 can identify it for convention-aware review
    for entry in results:
        if Path(entry["path"]).name == E2E_TEST_REPO:
            entry["role"] = "e2e_test_repo"

    emit_json({
        "submodules": results,
        "count": len(results),
        "domain_skills": domain_skills,
    })
    return 0


# ---------------------------------------------------------------------------
# prewarm (Phases 0–2.5)
# ---------------------------------------------------------------------------

def cmd_prewarm(args: argparse.Namespace) -> int:
    """Phases 0-2.5: Sync super-repo, resolve story, prepare branches, load skills.

    Returns exit code:
      0 = success
      1 = resolve failed (story not found)
      2 = no submodules prepared
    """
    repo_root = Path(args.repo_root).resolve()
    jira_key = args.jira_key

    # --- Phase 0: sync super-repo ---
    sync_ns = argparse.Namespace(repo_root=str(repo_root))
    cmd_sync_superrepo(sync_ns)

    # --- Phase 1: resolve ---
    resolve_ns = argparse.Namespace(jira_key=jira_key, repo_root=str(repo_root))
    # Inline resolve logic to capture result data
    map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "jira-key-map.yaml"
    data = read_yaml(map_path)

    active_project_key = data.get("active_project_key")
    if not active_project_key:
        die("active_project_key not found in jira-key-map.yaml")

    projects = data.get("projects", {})
    project = projects.get(active_project_key, {})
    items = project.get("items", [])

    bmad_id = None
    bmad_title = None
    for item in items:
        if item.get("jira_key") == jira_key and item.get("bmad_type") == "story":
            bmad_id = str(item["bmad_id"])
            bmad_title = str(item["bmad_title"])
            break

    if bmad_id is None:
        emit_json({"error": f"Jira key '{jira_key}' not found", "phase": "resolve"})
        return 1

    story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)
    story_branch = f"agent/story/{jira_key}-{story_key}"

    story_file_path = (
        repo_root
        / "_bmad-output"
        / "implementation-artifacts"
        / "stories"
        / f"{story_key}.md"
    )

    if not story_file_path.exists():
        emit_json({"error": f"Story file not found: {story_file_path}", "phase": "resolve"})
        return 1

    # --- Phase 2: prepare-branches with checkout_only=True ---
    content = story_file_path.read_text(encoding="utf-8")
    matches = MODULE_REF_RE.findall(content)
    seen: set = set()
    submodule_names: List[str] = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            submodule_names.append(m)

    # Auto-include zoneqa_automation when any testable source module is present.
    # This repo is never cited directly in story task lists (which name source
    # modules), so it must be injected here to ensure E2E/API tests are checked
    # out and reviewed alongside unit/integration tests in source submodules.
    if E2E_TEST_REPO not in seen and seen & E2E_TRIGGER_MODULES:
        seen.add(E2E_TEST_REPO)
        submodule_names.append(E2E_TEST_REPO)

    valid_names = [n for n in submodule_names if (repo_root / "modules" / n).is_dir()]
    submodule_results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=PREWARM_MAX_WORKERS) as pool:
        futures = {
            pool.submit(
                _prepare_one_submodule, name, repo_root,
                story_branch, True, [story_branch],  # checkout_only=True
            ): name
            for name in valid_names
        }
        for future in as_completed(futures):
            submodule_results.append(future.result())

    # Deeper fetch: --deepen 50 for diff context on checked-out submodules
    for result in submodule_results:
        if result["status"] not in ("error", "skipped"):
            sub_dir = str(repo_root / result["path"])
            git(["fetch", "origin", "--deepen", "50"], cwd=sub_dir, check=False)

    prepared_names = [
        Path(r["path"]).name for r in submodule_results
        if r["status"] not in ("error", "skipped")
    ]

    # Tag the e2e test repo entry so Phase 3 can identify it for convention-aware review
    for entry in submodule_results:
        if Path(entry["path"]).name == E2E_TEST_REPO:
            entry["role"] = "e2e_test_repo"

    if not prepared_names:
        emit_json({
            "error": "No submodules prepared",
            "phase": "prepare-branches",
            "submodules": submodule_results,
        })
        return 2

    # --- Phase 2.5: read domain skill SKILL.md files ---
    domain_skills = resolve_domain_skills(prepared_names, repo_root)
    skills_content_parts: List[str] = []
    for skill_info in domain_skills:
        if skill_info["exists"]:
            skill_path = Path(skill_info["path"])
            try:
                skill_text = skill_path.read_text(encoding="utf-8")
                skills_content_parts.append(
                    f"# {skill_info['skill']}\n\n{skill_text}"
                )
            except Exception:
                pass

    # Write .zone-prewarm-context.json
    context_data = {
        "jira_key": jira_key,
        "bmad_id": bmad_id,
        "bmad_title": bmad_title,
        "story_key": story_key,
        "story_branch": story_branch,
        "story_file_path": str(story_file_path),
        "submodules": submodule_results,
        "domain_skills": domain_skills,
        "prepared_count": len(prepared_names),
    }
    context_path = repo_root / ".zone-prewarm-context.json"
    context_path.write_text(json.dumps(context_data, indent=2), encoding="utf-8")

    # Write .zone-prewarm-skills.md
    skills_path = repo_root / ".zone-prewarm-skills.md"
    skills_md = "\n\n---\n\n".join(skills_content_parts) if skills_content_parts else "# No domain skills loaded\n"
    skills_path.write_text(skills_md, encoding="utf-8")

    emit_json(context_data)
    return 0


# ---------------------------------------------------------------------------
# commit-superrepo (Phase 4)
# ---------------------------------------------------------------------------

def cmd_commit_superrepo(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    jira_key = args.jira_key
    title = args.title
    cwd = str(repo_root)

    commit_msg = f"{jira_key}: {title} - code review report"

    # Stage _bmad-output/
    git(["add", "_bmad-output/"], cwd=cwd, check=False)

    # Unstage any modules/ paths
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
# create-pullrequests (Phase 4.5)
# ---------------------------------------------------------------------------

REMOTE_URL_RE = re.compile(r"git@bitbucket\.org:([^/]+)/(.+?)(?:\.git)?$")


def get_default_branch(submodule_name: str, repo_root: Path) -> str:
    """Get the default branch for a submodule from .gitmodules, fallback to 'development'."""
    try:
        result = git(
            ["config", "-f", ".gitmodules", "--get", f"submodule.modules/{submodule_name}.branch"],
            cwd=str(repo_root),
            check=False,
        )
        branch = result.stdout.strip()
        if result.returncode == 0 and branch:
            return branch
    except Exception:
        pass
    return "development"


def _parse_bb_remote(sub_dir: str) -> Optional[tuple]:
    """Extract (workspace, repo_slug) from the submodule's origin remote URL."""
    result = git(["remote", "get-url", "origin"], cwd=sub_dir, check=False)
    if result.returncode != 0:
        return None
    m = REMOTE_URL_RE.match(result.stdout.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _resolve_bb_auth() -> Optional[str]:
    """Resolve Bitbucket auth header. Prefers API token; falls back to app password."""
    # Prefer new API token auth
    bb_email = os.environ.get("BB_EMAIL", "")
    bb_token = os.environ.get("BB_API_TOKEN", "")
    if bb_email and bb_token:
        return "Basic " + b64encode(f"{bb_email}:{bb_token}".encode()).decode()

    # Fall back to legacy app password auth
    bb_user = os.environ.get("BB_USERNAME", "")
    bb_pass = os.environ.get("BB_APP_PASSWORD", "")
    if bb_user and bb_pass:
        print("warning: using legacy BB_USERNAME/BB_APP_PASSWORD; migrate to BB_EMAIL/BB_API_TOKEN before June 2026", file=sys.stderr)
        return "Basic " + b64encode(f"{bb_user}:{bb_pass}".encode()).decode()

    return None


def _build_pr_description(
    story_file: Optional[str],
    jira_key: str,
    story_branch: str,
    epic_branch: str,
) -> str:
    """Build a Markdown PR description from the story file content.

    Falls back to a minimal description if the story file is missing or unreadable.
    Truncates to 64 KB to stay within Bitbucket API limits.
    """
    BB_DESC_LIMIT = 64 * 1024  # 64 KB
    fallback = f"{jira_key}: `{story_branch}` → `{epic_branch}`"

    if not story_file:
        return fallback

    story_path = Path(story_file)
    if not story_path.exists():
        return fallback

    try:
        content = story_path.read_text(encoding="utf-8")
    except Exception:
        return fallback

    # Extract sections by heading
    def _extract_section(text: str, heading_pattern: str) -> Optional[str]:
        """Extract content under a heading until the next heading of same or higher level."""
        pattern = re.compile(
            rf"^(#{1,3})\s+{heading_pattern}\s*$",
            re.MULTILINE | re.IGNORECASE,
        )
        m = pattern.search(text)
        if not m:
            return None
        level = len(m.group(1))
        start = m.end()
        # Find next heading of same or higher level
        next_heading = re.compile(rf"^#{{{1},{level}}}\s+", re.MULTILINE)
        n = next_heading.search(text, start)
        section = text[start:n.start()].strip() if n else text[start:].strip()
        return section if section else None

    story_text = _extract_section(content, r"Story")
    ac_text = _extract_section(content, r"Acceptance Criteria")
    tasks_text = _extract_section(content, r"Tasks\s*/?\s*Subtasks")

    parts: List[str] = [f"## {jira_key}"]

    if story_text:
        parts.append(f"### Story\n{story_text}")
    if ac_text:
        parts.append(f"### Acceptance Criteria\n{ac_text}")
    if tasks_text:
        parts.append(f"### Tasks\n{tasks_text}")

    parts.append(f"---\n`{story_branch}` → `{epic_branch}`")

    description = "\n\n".join(parts)

    if len(description.encode("utf-8")) > BB_DESC_LIMIT:
        # Truncate to fit, leaving room for ellipsis
        while len(description.encode("utf-8")) > BB_DESC_LIMIT - 20:
            description = description[: len(description) - 200]
        description = description.rstrip() + "\n\n…*(truncated)*"

    return description


def _bb_create_pr(
    workspace: str,
    repo_slug: str,
    title: str,
    source_branch: str,
    dest_branch: str,
    auth_header: str,
    description: str = "",
) -> Dict[str, Any]:
    """Create a Bitbucket PR via REST API. Returns dict with status info."""
    url = f"https://api.bitbucket.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests"
    payload = json.dumps({
        "title": title,
        "description": description,
        "source": {"branch": {"name": source_branch}},
        "destination": {"branch": {"name": dest_branch}},
        "close_source_branch": False,
    }).encode("utf-8")

    req = urllib.request.Request(
        url,
        data=payload,
        headers={
            "Content-Type": "application/json",
            "Authorization": auth_header,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return {
                "status": "created",
                "pr_url": data.get("links", {}).get("html", {}).get("href", ""),
            }
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        if exc.code == 409:
            return {"status": "already_exists", "pr_url": ""}
        return {"status": "error", "error": f"HTTP {exc.code}: {body}"}
    except Exception as exc:
        return {"status": "error", "error": str(exc)}


def cmd_create_pullrequests(args: argparse.Namespace) -> int:
    """Phase 4.5: Create Bitbucket PRs from story_branch → epic_branch.

    When epic_branch is empty (bug fixes with no parent epic), the target
    branch is resolved per-submodule from .gitmodules (default: 'development').
    """
    repo_root = Path(args.repo_root).resolve()
    story_branch = args.story_branch
    epic_branch = args.epic_branch
    jira_key = args.jira_key
    title = args.title
    use_default = not epic_branch

    auth_header = _resolve_bb_auth()

    if auth_header is None:
        print("warning: Bitbucket credentials not configured (set BB_EMAIL + BB_API_TOKEN, or legacy BB_USERNAME + BB_APP_PASSWORD); skipping PR creation", file=sys.stderr)
        try:
            submodules = json.loads(args.submodules)
        except (json.JSONDecodeError, TypeError):
            submodules = []
        results = [
            {"submodule": s.get("path", "unknown"), "status": "skipped", "reason": "missing BB credentials"}
            for s in submodules
            if s.get("status") in ("checked_out_remote", "checked_out_local")
        ]
        emit_json({
            "action": "pullrequests_created",
            "results": results,
            "created_count": 0,
            "error_count": 0,
            "skipped_count": len(results),
        })
        return 0

    pr_title = f"{jira_key}: {title}"
    story_file = getattr(args, "story_file", None)

    try:
        submodules = json.loads(args.submodules)
    except (json.JSONDecodeError, TypeError):
        die("--submodules must be a valid JSON array")

    qualifying = [
        s for s in submodules
        if s.get("status") in ("checked_out_remote", "checked_out_local")
    ]

    # Build PR description once; use first submodule's resolved target for fallback text
    if use_default and qualifying:
        first_sub_name = qualifying[0].get("path", "").split("/")[-1] if "/" in qualifying[0].get("path", "") else qualifying[0].get("path", "")
        desc_target = get_default_branch(first_sub_name, repo_root)
    else:
        desc_target = epic_branch
    pr_description = _build_pr_description(story_file, jira_key, story_branch, desc_target)

    results = []
    created = 0
    errors = 0
    skipped = 0

    for sub in qualifying:
        sub_path = sub.get("path", "")
        sub_dir = str(repo_root / sub_path)
        entry: Dict[str, Any] = {"submodule": sub_path}

        # Resolve target branch per-submodule when no epic branch
        if use_default:
            sub_name = sub_path.split("/")[-1] if "/" in sub_path else sub_path
            target_branch = get_default_branch(sub_name, repo_root)
        else:
            target_branch = epic_branch

        remote_info = _parse_bb_remote(sub_dir)
        if not remote_info:
            entry["status"] = "skipped"
            entry["reason"] = "could not parse Bitbucket remote URL"
            skipped += 1
            results.append(entry)
            continue

        workspace, repo_slug = remote_info
        pr_result = _bb_create_pr(workspace, repo_slug, pr_title, story_branch, target_branch, auth_header, pr_description)
        entry.update(pr_result)
        entry["target_branch"] = target_branch

        if pr_result["status"] == "created":
            created += 1
        elif pr_result["status"] == "already_exists":
            created += 1  # count as success
        elif pr_result["status"] == "error":
            errors += 1
        else:
            skipped += 1

        results.append(entry)

    emit_json({
        "action": "pullrequests_created",
        "results": results,
        "created_count": created,
        "error_count": errors,
        "skipped_count": skipped,
    })
    return 0


# ---------------------------------------------------------------------------
# attach-story (Phase 4.6)
# ---------------------------------------------------------------------------

def cmd_attach_story(args: argparse.Namespace) -> int:
    """Phase 4.6: Attach story file to Jira issue (best-effort)."""
    jira_key = args.jira_key
    story_file = Path(args.story_file)
    repo_root = Path(args.repo_root).resolve()

    if not story_file.exists():
        print(f"warning: story file not found at {story_file}, skipping attachment", file=sys.stderr)
        emit_json({
            "action": "skipped",
            "reason": "story file not found",
            "jira_key": jira_key,
        })
        return 0

    jira_script = repo_root / ".claude" / "skills" / "jira-agile" / "scripts" / "jira_agile.py"

    if not jira_script.exists():
        print(f"warning: jira_agile.py not found at {jira_script}, skipping attachment", file=sys.stderr)
        emit_json({
            "action": "skipped",
            "reason": "jira_agile.py not found",
            "jira_key": jira_key,
        })
        return 0

    # Derive attachment filename: story_report_{stem}.md
    attachment_filename = f"story_report_{story_file.stem}.md"

    cmd = [
        sys.executable, str(jira_script),
        "attach-file", jira_key, str(story_file),
        "--filename", attachment_filename,
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(
                f"warning: Jira attachment failed (exit {result.returncode}): "
                f"{result.stderr.strip() or result.stdout.strip()}",
                file=sys.stderr,
            )
            emit_json({
                "action": "warning",
                "reason": f"attachment failed: {result.stderr.strip() or result.stdout.strip()}",
                "jira_key": jira_key,
            })
            return 0  # Non-fatal

        emit_json({
            "action": "attached",
            "jira_key": jira_key,
            "file": str(story_file),
            "attachment_filename": attachment_filename,
        })

    except subprocess.TimeoutExpired:
        print("warning: Jira attachment timed out", file=sys.stderr)
        emit_json({
            "action": "warning",
            "reason": "attachment timed out",
            "jira_key": jira_key,
        })
    except Exception as exc:
        print(f"warning: Jira attachment error: {exc}", file=sys.stderr)
        emit_json({
            "action": "warning",
            "reason": str(exc),
            "jira_key": jira_key,
        })

    return 0  # Always non-fatal


# ---------------------------------------------------------------------------
# transition-jira (Phase 4.8)
# ---------------------------------------------------------------------------

def cmd_transition_jira(args: argparse.Namespace) -> int:
    """Phase 4.8: Transition Jira issue to target status (best-effort)."""
    jira_key = args.jira_key
    target_status = args.target_status
    comment = args.comment
    comment_file = args.comment_file
    comment_stdin = args.comment_stdin
    comment_format = args.comment_format
    repo_root = Path(args.repo_root).resolve()

    jira_script = repo_root / ".claude" / "skills" / "jira-agile" / "scripts" / "jira_agile.py"

    if not jira_script.exists():
        print(f"warning: jira_agile.py not found at {jira_script}, skipping Jira transition", file=sys.stderr)
        emit_json({
            "action": "skipped",
            "reason": "jira_agile.py not found",
            "jira_key": jira_key,
        })
        return 0

    cmd = [
        sys.executable, str(jira_script),
        "transition-issue", jira_key, target_status,
    ]
    if comment:
        cmd.extend(["--comment", comment])
    elif comment_file:
        cmd.extend(["--comment-file", comment_file])
    elif comment_stdin:
        cmd.append("--comment-stdin")
    if comment or comment_file or comment_stdin:
        cmd.extend(["--comment-format", comment_format])

    try:
        result = subprocess.run(
            cmd,
            cwd=str(repo_root),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            print(
                f"warning: Jira transition failed (exit {result.returncode}): "
                f"{result.stderr.strip() or result.stdout.strip()}",
                file=sys.stderr,
            )
            emit_json({
                "action": "warning",
                "reason": f"transition failed: {result.stderr.strip() or result.stdout.strip()}",
                "jira_key": jira_key,
            })
            return 0  # Non-fatal

        emit_json({
            "action": "transitioned",
            "jira_key": jira_key,
            "target_status": target_status,
        })

    except subprocess.TimeoutExpired:
        print("warning: Jira transition timed out", file=sys.stderr)
        emit_json({
            "action": "warning",
            "reason": "transition timed out",
            "jira_key": jira_key,
        })
    except Exception as exc:
        print(f"warning: Jira transition error: {exc}", file=sys.stderr)
        emit_json({
            "action": "warning",
            "reason": str(exc),
            "jira_key": jira_key,
        })

    return 0  # Always non-fatal


# ---------------------------------------------------------------------------
# status (Phase 5)
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    """Phase 5: Output status sentinel.

    status="0" (PASS) when review completed and no CRITICAL/HIGH/MEDIUM issues;
    status="1" (FAIL) when unchecked > 0 or review report missing.
    unchecked = CRITICAL + HIGH + MEDIUM count.
    """
    story_file_arg = getattr(args, "story_file", None)
    if story_file_arg:
        story_file = Path(story_file_arg)
    else:
        story_file = _resolve_story_file(args.jira_key, Path(args.repo_root).resolve())

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")

    matches = list(ISSUES_FOUND_RE.finditer(content))
    match = matches[-1] if matches else None
    if match and REVIEW_REPORT_MARKER in content:
        # Format A groups: (1)Critical (2)High (3)Medium (4)Low
        # Format B groups: (5)CRITICAL (6)HIGH (7)MEDIUM (8)LOW
        if match.group(5) is not None:
            # Format B: CRITICAL=X, HIGH=Y, MEDIUM=Z, LOW=W
            critical_count = int(match.group(5))
            high_count = int(match.group(6))
            medium_count = int(match.group(7))
        else:
            # Format A: [X Critical,] Y High, Z Medium, W Low
            critical_count = int(match.group(1) or 0)
            high_count = int(match.group(2))
            medium_count = int(match.group(3))
        unchecked = critical_count + high_count + medium_count
        status = "0" if unchecked == 0 else "1"
    else:
        # Review report not found — review incomplete or failed
        status = "1"
        unchecked = 0

    result = json.dumps({"status": status, "unchecked": unchecked})
    print(f"{SENTINEL}{result}{SENTINEL}")
    return 0


# ---------------------------------------------------------------------------
# main — argparse dispatcher
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic automation for zone-code-review skill phases 1, 2, 4, 5."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # sync-superrepo
    p_sync = subparsers.add_parser("sync-superrepo", help="Phase 0: Pull latest super-repo branch")
    p_sync.add_argument("--repo-root", default=".", help="Repository root directory")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="Phase 1: Resolve Jira key to story")
    p_resolve.add_argument("--jira-key", required=True, help="Jira issue key (e.g. BMAD-152)")
    p_resolve.add_argument("--repo-root", default=".", help="Repository root directory")

    # prepare-branches
    p_branches = subparsers.add_parser("prepare-branches", help="Phase 2: Checkout submodule story branches")
    p_branches.add_argument("--story-file", required=True, help="Path to story markdown file")
    p_branches.add_argument("--story-branch", required=True, help="Branch name for the story")
    p_branches.add_argument("--checkout-only", action="store_true", help="Only checkout existing branches; never create")
    p_branches.add_argument("--repo-root", default=".", help="Repository root directory")

    # prewarm
    p_prewarm = subparsers.add_parser("prewarm", help="Phases 0-2.5: Sync, resolve, prepare, load skills")
    p_prewarm.add_argument("--jira-key", required=True, help="Jira issue key")
    p_prewarm.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-superrepo
    p_commit_super = subparsers.add_parser("commit-superrepo", help="Phase 4: Commit and push super-repo")
    p_commit_super.add_argument("--story-key", required=True, help="Story key identifier")
    p_commit_super.add_argument("--jira-key", required=True, help="Jira issue key")
    p_commit_super.add_argument("--title", required=True, help="BMAD story title for commit message")
    p_commit_super.add_argument("--repo-root", default=".", help="Repository root directory")

    # create-pullrequests
    p_pr = subparsers.add_parser("create-pullrequests", help="Phase 4.5: Create Bitbucket PRs")
    p_pr.add_argument("--story-branch", required=True, help="Source branch for PRs")
    p_pr.add_argument("--epic-branch", default="", help="Destination branch for PRs (empty = submodule default)")
    p_pr.add_argument("--jira-key", required=True, help="Jira issue key for PR title")
    p_pr.add_argument("--title", required=True, help="BMAD title for PR title")
    p_pr.add_argument("--submodules", required=True, help="JSON string of submodule result objects")
    p_pr.add_argument("--story-file", default=None, help="Path to story markdown file (used to build PR description)")
    p_pr.add_argument("--repo-root", default=".", help="Repository root directory")

    # attach-story
    p_attach = subparsers.add_parser("attach-story", help="Phase 4.6: Attach story file to Jira")
    p_attach.add_argument("--jira-key", required=True, help="Jira issue key")
    p_attach.add_argument("--story-file", required=True, help="Path to story markdown file")
    p_attach.add_argument("--repo-root", default=".", help="Repository root directory")

    # transition-jira
    p_transition = subparsers.add_parser("transition-jira", help="Phase 4.8: Transition Jira issue")
    p_transition.add_argument("--jira-key", required=True, help="Jira issue key")
    p_transition.add_argument("--target-status", required=True, help="Target Jira status")
    group = p_transition.add_mutually_exclusive_group()
    group.add_argument("--comment", default=None, help="Optional transition comment")
    group.add_argument("--comment-file", default=None, help="Read transition comment from a file")
    group.add_argument("--comment-stdin", action="store_true", help="Read transition comment from stdin")
    p_transition.add_argument("--comment-format", default="plain", choices=["plain", "markdown"],
                              help="Format of the transition comment content")
    p_transition.add_argument("--repo-root", default=".", help="Repository root directory")

    # status
    p_status = subparsers.add_parser("status", help="Phase 5: Output status sentinel")
    p_status.add_argument("--story-file", default=None, help="Path to story markdown file")
    p_status.add_argument("--jira-key", default=None, help="Jira issue key (fallback resolution when --story-file omitted)")
    p_status.add_argument("--repo-root", default=".", help="Repository root directory")

    parsed = parser.parse_args()

    dispatch = {
        "sync-superrepo": cmd_sync_superrepo,
        "resolve": cmd_resolve,
        "prepare-branches": cmd_prepare_branches,
        "prewarm": cmd_prewarm,
        "commit-superrepo": cmd_commit_superrepo,
        "create-pullrequests": cmd_create_pullrequests,
        "attach-story": cmd_attach_story,
        "transition-jira": cmd_transition_jira,
        "status": cmd_status,
    }

    handler = dispatch.get(parsed.command)
    if handler is None:
        die(f"Unknown command: {parsed.command}")

    return handler(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
