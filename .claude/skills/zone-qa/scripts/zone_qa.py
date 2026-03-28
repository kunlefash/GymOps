#!/usr/bin/env python3
"""Deterministic automation for zone-qa skill phases 0, 1, 2, 4, 5, 6."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional, Tuple

import yaml

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

SENTINEL = "###ZONE-QA-RESULT###"
MODULE_REF_RE = re.compile(r"modules/([\w.]+)")
UNCHECKED_RE = re.compile(r"- \[ \]")
SKILL_MAP_FILENAME = "module-skill-map.yaml"
QA_MODE_RE = re.compile(r"qa_mode:\s*(atdd|automation)", re.IGNORECASE)

# ---------------------------------------------------------------------------
# E2E test repo auto-include
# ---------------------------------------------------------------------------
# zoneqa_automation is the single canonical Playwright repo for all E2E and
# API tests across the platform.  It is never referenced directly in story
# task lists (which name source modules), so it must be injected automatically
# whenever a story touches any testable source module.
E2E_TEST_REPO = "tests/e2e"
E2E_TRIGGER_MODULES = {
    "src/app", "src/components", "src/lib",
    "src/services", "src/hooks", "src/stores",
}


def read_yaml(path: Path) -> Dict[str, Any]:
    """Load a YAML file; return empty dict if missing or empty."""
    if not path.exists():
        die(f"YAML file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)
    return data if isinstance(data, dict) else {}


def _resolve_story_file(story_key: str, repo_root: Path) -> Path:
    """Resolve a story key to its story file path via story-key-map.yaml."""
    _, items = jira_map_items(repo_root)
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


def jira_map_items(repo_root: Path) -> Tuple[str, List[Dict[str, Any]]]:
    """Return active project key and flat Jira map items."""
    map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "story-key-map.yaml"
    data = read_yaml(map_path)
    active_project_key = data.get("active_project_key")
    if not active_project_key:
        die("active_project_key not found in story-key-map.yaml")
    projects = data.get("projects", {})
    project = projects.get(active_project_key, {})
    items = project.get("items", [])
    if not isinstance(items, list):
        die("story-key-map.yaml projects.<active>.items must be a list")
    return str(active_project_key), [i for i in items if isinstance(i, dict)]


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


def extract_qa_mode(story_file: Path) -> Optional[str]:
    """Extract qa_mode from story file frontmatter/metadata if present."""
    if not story_file.exists():
        return None
    content = story_file.read_text(encoding="utf-8")
    match = QA_MODE_RE.search(content)
    if match:
        return match.group(1).lower()
    return None


def resolve_qa_mode(story_file: Path, supplied_qa_mode: Optional[str] = None) -> str:
    """Resolve qa_mode with precedence: supplied value > story file > default."""
    if supplied_qa_mode:
        return supplied_qa_mode
    story_qa_mode = extract_qa_mode(story_file)
    if story_qa_mode:
        return story_qa_mode
    return "automation"


# ---------------------------------------------------------------------------
# Domain skill resolution
# ---------------------------------------------------------------------------

def resolve_domain_skills(module_names: List[str], repo_root: Path) -> List[Dict[str, Any]]:
    """Map module names to domain skills via module-skill-map.yaml."""
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

    for name in module_names:
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
    story_key = args.story_key
    active_project_key, items = jira_map_items(repo_root)

    bmad_id = None
    bmad_title = None
    for item in items:
        if item.get("story_key") == story_key and item.get("bmad_type") == "story":
            bmad_id = str(item["bmad_id"])
            bmad_title = str(item["bmad_title"])
            break

    if bmad_id is None:
        die(f"story key '{story_key}' not found in story-key-map.yaml (project={active_project_key})")

    # Look up the parent epic
    parent_story_key = None
    epic_branch = None
    for item in items:
        if item.get("story_key") == story_key and item.get("bmad_type") == "story":
            parent_story_key = item.get("parent_story_key")
            break

    if parent_story_key:
        for item in items:
            if item.get("bmad_type") == "epic" and item.get("story_key") == parent_story_key:
                epic_bmad_id = str(item["bmad_id"]).replace(".", "-")
                epic_key = epic_bmad_id + "-" + slugify(str(item["bmad_title"]))
                epic_branch = f"agent/epic/{parent_story_key}-{epic_key}"
                break

    # Derive story_key
    story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)

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

    # Resolve qa_mode: supplied value > story file > default.
    qa_mode = resolve_qa_mode(story_file_path, args.qa_mode)

    result = {
        "bmad_id": bmad_id,
        "bmad_title": bmad_title,
        "story_key": story_key,
        "story_file_path": str(story_file_path),
        "story_key": story_key,
        "qa_mode": qa_mode,
    }
    if epic_branch:
        result["epic_branch"] = epic_branch
        result["parent_story_key"] = parent_story_key

    # --- Initiative lookup ---
    initiative_branch = None
    sprint_status_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    if sprint_status_path.exists() and parent_story_key:
        sprint_data = read_yaml(sprint_status_path)
        epic_bmad_id = None
        for item in items:
            if item.get("bmad_type") == "epic" and item.get("story_key") == parent_story_key:
                epic_bmad_id = str(item["bmad_id"])
                break
        if epic_bmad_id:
            for init_info in sprint_data.get("initiatives", []):
                epic_ids = [str(e["id"]) for e in init_info.get("epics", []) if isinstance(e, dict)]
                if epic_bmad_id in epic_ids:
                    initiative_branch = init_info.get("branch")
                    break

    if initiative_branch:
        result["initiative_branch"] = initiative_branch

    emit_json(result)
    return 0


# ---------------------------------------------------------------------------
# prepare-branches (Phase 2)
# ---------------------------------------------------------------------------

def get_default_branch(module_name: str, repo_root: Path) -> str:
    """Get the default branch for a module from .gitmodules, fallback to 'development'."""
    try:
        result = git(
            ["config", "-f", ".gitmodules", "--get", f"module.modules/{module_name}.branch"],
            cwd=str(repo_root),
            check=False,
        )
        branch = result.stdout.strip()
        if result.returncode == 0 and branch:
            return branch
    except Exception:
        pass
    return "development"


def ensure_initiative_branch(
    initiative_branch: str, module_name: str, sub_dir: str, repo_root: Path,
) -> str:
    """Ensure the initiative branch exists in the module. Returns status string."""
    ls_result = git(["ls-remote", "--heads", "origin", initiative_branch], cwd=sub_dir)
    if bool(ls_result.stdout.strip()):
        git(["checkout", initiative_branch], cwd=sub_dir)
        git(["pull", "origin", initiative_branch], cwd=sub_dir)
        return "checked_out_remote"

    local_check = git(["rev-parse", "--verify", initiative_branch], cwd=sub_dir, check=False)
    if local_check.returncode == 0:
        git(["checkout", initiative_branch], cwd=sub_dir)
        return "checked_out_local"

    default_branch = get_default_branch(module_name, repo_root)
    git(["checkout", default_branch], cwd=sub_dir)
    git(["pull", "origin", default_branch], cwd=sub_dir)
    git(["checkout", "-b", initiative_branch], cwd=sub_dir)
    git(["push", "-u", "origin", initiative_branch], cwd=sub_dir)
    return "created"


def ensure_epic_branch(
    epic_branch: str, module_name: str, sub_dir: str, repo_root: Path,
    initiative_branch: Optional[str] = None,
) -> str:
    """Ensure the epic branch exists in the module. Returns status string."""
    ls_result = git(["ls-remote", "--heads", "origin", epic_branch], cwd=sub_dir)
    remote_exists = bool(ls_result.stdout.strip())

    if remote_exists:
        git(["checkout", epic_branch], cwd=sub_dir)
        git(["pull", "origin", epic_branch], cwd=sub_dir)
        return "checked_out_remote"

    local_check = git(["rev-parse", "--verify", epic_branch], cwd=sub_dir, check=False)
    if local_check.returncode == 0:
        git(["checkout", epic_branch], cwd=sub_dir)
        return "checked_out_local"

    if initiative_branch:
        base_branch = initiative_branch
    else:
        base_branch = get_default_branch(module_name, repo_root)
    git(["checkout", base_branch], cwd=sub_dir)
    git(["pull", "origin", base_branch], cwd=sub_dir)
    git(["checkout", "-b", epic_branch], cwd=sub_dir)
    git(["push", "-u", "origin", epic_branch], cwd=sub_dir)
    return "created"


PREWARM_MAX_WORKERS = int(os.environ.get("PREWARM_WORKERS", "4"))


def _prepare_one_module(
    name: str,
    repo_root: Path,
    target_branch: str,
    qa_mode: str,
    epic_branch: Optional[str],
    initiative_branch: Optional[str],
    target_branches: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Prepare a single module: init, fetch, checkout/create target branch.

    Args:
        target_branch: the story branch to check out or create.
        qa_mode: "atdd" creates missing branches; "automation" skips if not found.
        target_branches: list of branch names to fetch instead of all refs.
            When None, falls back to full ``git fetch origin``.
    """
    sub_path = repo_root / "modules" / name
    entry: Dict[str, Any] = {"path": f"modules/{name}", "status": "ok", "created": False}

    try:
        git(["module", "update", "--init", "--depth", "1", f"modules/{name}"], cwd=str(repo_root))
    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"module init failed: {exc.stderr.strip()}"
        return entry

    sub_dir = str(sub_path)
    git(["config", "user.name", "GymOps AI Agent"], cwd=sub_dir)
    git(["config", "user.email", "ai@gymops.dev"], cwd=sub_dir)

    try:
        if target_branches:
            git(["fetch", "origin"] + target_branches, cwd=sub_dir, check=False)
        else:
            git(["fetch", "origin"], cwd=sub_dir)
    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"fetch failed: {exc.stderr.strip()}"
        return entry

    try:
        ls_result = git(
            ["ls-remote", "--heads", "origin", target_branch],
            cwd=sub_dir,
        )
        remote_exists = bool(ls_result.stdout.strip())

        if remote_exists:
            git(["checkout", target_branch], cwd=sub_dir)
            git(["pull", "origin", target_branch], cwd=sub_dir)
            entry["status"] = "checked_out_remote"
        else:
            local_check = git(
                ["rev-parse", "--verify", target_branch],
                cwd=sub_dir,
                check=False,
            )
            if local_check.returncode == 0:
                git(["checkout", target_branch], cwd=sub_dir)
                entry["status"] = "checked_out_local"
            elif qa_mode == "atdd":
                # ATDD mode: create new story branches for failing tests
                if initiative_branch:
                    init_status = ensure_initiative_branch(
                        initiative_branch, name, sub_dir, repo_root,
                    )
                    entry["initiative_branch_status"] = init_status

                if epic_branch:
                    epic_status = ensure_epic_branch(
                        epic_branch, name, sub_dir, repo_root,
                        initiative_branch=initiative_branch,
                    )
                    entry["epic_branch_status"] = epic_status

                git(["checkout", "-b", target_branch], cwd=sub_dir)
                entry["status"] = "created"
                entry["created"] = True
            else:
                # automation mode: story branch must already exist
                entry["status"] = "skipped"
                entry["reason"] = f"story branch '{target_branch}' not found (automation mode)"

    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"branch checkout failed: {exc.stderr.strip()}"

    return entry


def cmd_prepare_branches(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    qa_mode = args.qa_mode
    story_key = args.story_key
    story_key = args.story_key
    epic_branch = getattr(args, "epic_branch", None)
    initiative_branch = getattr(args, "initiative_branch", None)
    story_file = Path(args.story_file)

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")

    # Determine branch name based on mode
    # Both ATDD and automation use agent/story/ — ATDD writes failing tests
    # directly on the story branch so zone-dev picks them up automatically.
    target_branch = f"agent/story/{story_key}-{story_key}"

    # Extract modules/<name> references, deduplicate, filter to existing dirs
    matches = MODULE_REF_RE.findall(content)
    seen = set()
    module_names = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            module_names.append(m)

    # Auto-include zoneqa_automation when any testable source module is present.
    # This repo is never cited directly in story task lists (which name source
    # modules), so it must be injected here to ensure E2E/API tests are placed
    # in the canonical Playwright repo rather than inside the source module.
    if E2E_TEST_REPO not in seen and seen & E2E_TRIGGER_MODULES:
        seen.add(E2E_TEST_REPO)
        module_names.append(E2E_TEST_REPO)

    # Build targeted fetch list
    target_branches = [target_branch]
    if epic_branch:
        target_branches.append(epic_branch)
    if initiative_branch:
        target_branches.append(initiative_branch)

    # Filter to existing dirs
    valid_names = [n for n in module_names if (repo_root / "modules" / n).is_dir()]

    # Process modules in parallel
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=PREWARM_MAX_WORKERS) as pool:
        futures = {
            pool.submit(
                _prepare_one_module, name, repo_root,
                target_branch, qa_mode, epic_branch, initiative_branch, target_branches,
            ): name
            for name in valid_names
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Resolve domain skills from successfully prepared modules
    prepared_names = [
        Path(r["path"]).name for r in results if r["status"] not in ("error", "skipped")
    ]
    domain_skills = resolve_domain_skills(prepared_names, repo_root)

    # Tag the e2e test repo entry so Phase 3 can identify it for routing
    for entry in results:
        if Path(entry["path"]).name == E2E_TEST_REPO:
            entry["role"] = "e2e_test_repo"

    emit_json({
        "modules": results,
        "count": len([r for r in results if r["status"] not in ("error", "skipped")]),
        "target_branch": target_branch,
        "qa_mode": qa_mode,
        "domain_skills": domain_skills,
    })
    return 0


# ---------------------------------------------------------------------------
# prewarm (Phases 0-2.5 combined)
# ---------------------------------------------------------------------------

def cmd_prewarm(args: argparse.Namespace) -> int:
    """Run Phases 0-2.5 deterministically and write context files for the agent."""
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key
    supplied_qa_mode = args.qa_mode
    cwd = str(repo_root)

    context: Dict[str, Any] = {
        "prewarm_version": "1.0",
        "prewarm_status": "success",
        "blocker_summary": "",
        "resolve": {},
        "prepare_branches": {},
        "domain_skills_loaded": [],
    }

    def _write_and_exit(status: str, blocker: str, code: int) -> int:
        context["prewarm_status"] = status
        context["blocker_summary"] = blocker
        (repo_root / ".gymops-prewarm-context.json").write_text(
            json.dumps(context, indent=2), encoding="utf-8",
        )
        return code

    # Phase 0: sync super-repo
    try:
        branch = _current_branch(cwd)
        git(["fetch", "origin"], cwd=cwd)
        result = git(["pull", "--rebase", "origin", branch], cwd=cwd, check=False)
        if result.returncode != 0:
            git(["rebase", "--abort"], cwd=cwd, check=False)
            result = git(["pull", "--no-rebase", "origin", branch], cwd=cwd, check=False)
            if result.returncode != 0:
                git(["merge", "--abort"], cwd=cwd, check=False)
                return _write_and_exit("blocked", f"SYNC_FAILED: {result.stderr.strip()}", 1)
    except Exception as exc:
        return _write_and_exit("blocked", f"SYNC_FAILED: {exc}", 1)

    # Phase 1: resolve
    try:
        active_project_key, items = jira_map_items(repo_root)

        bmad_id = bmad_title = None
        for item in items:
            if item.get("story_key") == story_key and item.get("bmad_type") == "story":
                bmad_id = str(item["bmad_id"])
                bmad_title = str(item["bmad_title"])
                break
        if bmad_id is None:
            return _write_and_exit("blocked", f"KEY_NOT_FOUND: story key '{story_key}' not found in story-key-map.yaml", 1)

        parent_story_key = epic_key = epic_branch = None
        for item in items:
            if item.get("story_key") == story_key and item.get("bmad_type") == "story":
                parent_story_key = item.get("parent_story_key")
                break
        if parent_story_key:
            for item in items:
                if item.get("bmad_type") == "epic" and item.get("story_key") == parent_story_key:
                    epic_bmad_id = str(item["bmad_id"]).replace(".", "-")
                    epic_key = epic_bmad_id + "-" + slugify(str(item["bmad_title"]))
                    epic_branch = f"agent/epic/{parent_story_key}-{epic_key}"
                    break

        story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)
        target_branch = f"agent/story/{story_key}-{story_key}"
        story_file_path = repo_root / "_bmad-output" / "implementation-artifacts" / "stories" / f"{story_key}.md"

        if not story_file_path.exists():
            return _write_and_exit("blocked", f"STORY_FILE_MISSING: {story_file_path}", 1)

        # Resolve qa_mode: supplied value > story file > default
        qa_mode = resolve_qa_mode(story_file_path, supplied_qa_mode)

        # Initiative lookup
        initiative_branch = None
        sprint_status_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
        if sprint_status_path.exists() and parent_story_key:
            sprint_data = read_yaml(sprint_status_path)
            epic_bmad_id_raw = None
            for item in items:
                if item.get("bmad_type") == "epic" and item.get("story_key") == parent_story_key:
                    epic_bmad_id_raw = str(item["bmad_id"])
                    break
            if epic_bmad_id_raw:
                for init_info in sprint_data.get("initiatives", []):
                    epic_ids = [str(e["id"]) for e in init_info.get("epics", []) if isinstance(e, dict)]
                    if epic_bmad_id_raw in epic_ids:
                        initiative_branch = init_info.get("branch")
                        break

        resolve_data: Dict[str, Any] = {
            "bmad_id": bmad_id, "bmad_title": bmad_title, "story_key": story_key,
            "target_branch": target_branch, "story_file_path": str(story_file_path),
            "story_key": story_key, "qa_mode": qa_mode,
        }
        if epic_branch:
            resolve_data["epic_key"] = epic_key
            resolve_data["epic_branch"] = epic_branch
            resolve_data["parent_story_key"] = parent_story_key
        if initiative_branch:
            resolve_data["initiative_branch"] = initiative_branch

        context["resolve"] = resolve_data

    except SystemExit:
        return _write_and_exit("blocked", "RESOLVE_FAILED: resolve phase raised SystemExit", 1)
    except Exception as exc:
        return _write_and_exit("blocked", f"RESOLVE_FAILED: {exc}", 1)

    # Phase 2: prepare-branches
    try:
        content = story_file_path.read_text(encoding="utf-8")
        matches = MODULE_REF_RE.findall(content)
        seen: set = set()
        module_names = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                module_names.append(m)

        # Auto-include zoneqa_automation when any testable source module is present.
        # This repo is never cited directly in story task lists (which name source
        # modules), so it must be injected here to ensure E2E/API tests are placed
        # in the canonical Playwright repo rather than inside the source module.
        if E2E_TEST_REPO not in seen and seen & E2E_TRIGGER_MODULES:
            seen.add(E2E_TEST_REPO)
            module_names.append(E2E_TEST_REPO)

        target_branches = [target_branch]
        if epic_branch:
            target_branches.append(epic_branch)
        if initiative_branch:
            target_branches.append(initiative_branch)

        valid_names = [n for n in module_names if (repo_root / "modules" / n).is_dir()]

        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=PREWARM_MAX_WORKERS) as pool:
            futures = {
                pool.submit(
                    _prepare_one_module, name, repo_root,
                    target_branch, qa_mode, epic_branch, initiative_branch, target_branches,
                ): name
                for name in valid_names
            }
            for future in as_completed(futures):
                results.append(future.result())

        prepared_names = [Path(r["path"]).name for r in results if r["status"] not in ("error", "skipped")]
        domain_skills = resolve_domain_skills(prepared_names, repo_root)

        # Tag the e2e test repo entry so Phase 3 can identify it for routing
        for entry in results:
            if Path(entry["path"]).name == E2E_TEST_REPO:
                entry["role"] = "e2e_test_repo"

        has_errors = any(r["status"] == "error" for r in results)
        if not prepared_names:
            context["prepare_branches"] = {"modules": results, "count": 0, "domain_skills": domain_skills}
            return _write_and_exit("blocked", "PREPARE_FAILED: no modules prepared successfully", 1)

        context["prepare_branches"] = {
            "modules": results,
            "count": len(prepared_names),
            "target_branch": target_branch,
            "qa_mode": qa_mode,
            "domain_skills": domain_skills,
        }
        if has_errors:
            context["prewarm_status"] = "partial"

    except Exception as exc:
        return _write_and_exit("blocked", f"PREPARE_FAILED: {exc}", 1)

    # Phase 2.5: read domain skill files
    skills_content_parts: List[str] = []
    loaded_skills: List[str] = []
    for ds in domain_skills:
        if ds.get("exists"):
            try:
                skill_text = Path(ds["path"]).read_text(encoding="utf-8")
                skills_content_parts.append(f"--- SKILL: {ds['skill']} ---\n{skill_text}\n--- END SKILL: {ds['skill']} ---")
                loaded_skills.append(ds["skill"])
            except Exception:
                pass

    context["domain_skills_loaded"] = loaded_skills

    # Write output files
    (repo_root / ".gymops-prewarm-context.json").write_text(
        json.dumps(context, indent=2), encoding="utf-8",
    )
    (repo_root / ".gymops-prewarm-skills.md").write_text(
        "\n\n".join(skills_content_parts), encoding="utf-8",
    )

    emit_json(context)
    return 0 if context["prewarm_status"] == "success" else 2


# ---------------------------------------------------------------------------
# commit-modules (Phase 4)
# ---------------------------------------------------------------------------

def cmd_commit_modules(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key
    title = args.title
    suffix = args.suffix
    qa_mode = args.qa_mode
    story_key = args.story_key

    # Determine branch name based on mode
    # Both ATDD and automation use agent/story/ — ATDD writes failing tests
    # directly on the story branch so zone-dev picks them up automatically.
    target_branch = f"agent/story/{story_key}-{story_key}"

    try:
        modules = json.loads(args.modules)
    except json.JSONDecodeError as exc:
        die(f"Invalid --modules JSON: {exc}")

    commit_msg = f"{story_key}: {title} - {suffix}"
    results = []
    committed_count = 0
    skipped_count = 0

    for sub_path in modules:
        full_path = str(repo_root / sub_path)
        entry: Dict[str, Any] = {"path": sub_path}

        if not os.path.isdir(full_path):
            entry["action"] = "error"
            entry["error"] = f"directory not found: {full_path}"
            results.append(entry)
            continue

        status_result = git(["status", "--porcelain"], cwd=full_path, check=False)
        if not status_result.stdout.strip():
            entry["action"] = "skipped"
            entry["reason"] = "no changes"
            skipped_count += 1
            results.append(entry)
            continue

        try:
            git(["config", "user.name", "GymOps AI Agent"], cwd=full_path)
            git(["config", "user.email", "ai@gymops.dev"], cwd=full_path)
            # Reset CI-regenerated lock files before staging (Run14-H1)
            for lockfile in ("package-lock.json", "yarn.lock"):
                subprocess.run(["git", "checkout", "HEAD", "--", lockfile], cwd=full_path, check=False)
            git(["add", "-A"], cwd=full_path)
            git(["commit", "-m", commit_msg], cwd=full_path)

            log_result = git(["rev-parse", "HEAD"], cwd=full_path)
            entry["commit_hash"] = log_result.stdout.strip()

            git_push_with_retry(["-u", "origin", target_branch], cwd=full_path)
            entry["action"] = "committed_and_pushed"
            committed_count += 1

        except subprocess.CalledProcessError as exc:
            entry["action"] = "error"
            entry["error"] = exc.stderr.strip() or exc.stdout.strip()

        results.append(entry)

    emit_json({
        "results": results,
        "committed_count": committed_count,
        "skipped_count": skipped_count,
    })
    return 0


# ---------------------------------------------------------------------------
# commit-superrepo (Phase 4 — super-repo)
# ---------------------------------------------------------------------------

def cmd_commit_superrepo(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key
    title = args.title
    suffix = args.suffix
    cwd = str(repo_root)

    commit_msg = f"{story_key}: {title} - {suffix}"

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
# transition-jira (Phase 5)
# ---------------------------------------------------------------------------

def cmd_transition_jira(args: argparse.Namespace) -> int:
    story_key = args.story_key
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
            "story_key": story_key,
        })
        return 0

    cmd = [
        sys.executable, str(jira_script),
        "transition-issue", story_key, target_status,
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
                "story_key": story_key,
            })
            return 0  # Non-fatal

        emit_json({
            "action": "transitioned",
            "story_key": story_key,
            "target_status": target_status,
        })

    except subprocess.TimeoutExpired:
        print("warning: Jira transition timed out", file=sys.stderr)
        emit_json({
            "action": "warning",
            "reason": "transition timed out",
            "story_key": story_key,
        })
    except Exception as exc:
        print(f"warning: Jira transition error: {exc}", file=sys.stderr)
        emit_json({
            "action": "warning",
            "reason": str(exc),
            "story_key": story_key,
        })

    return 0  # Always non-fatal


# ---------------------------------------------------------------------------
# status (Phase 6)
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    story_file_arg = getattr(args, "story_file", None)
    if story_file_arg:
        story_file = Path(story_file_arg)
    else:
        story_file = _resolve_story_file(args.story_key, Path(args.repo_root).resolve())
    qa_mode = args.qa_mode
    validation_only = bool(args.validation_only)

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    # If caller supplied test metrics from Phase 3 tracking, use them directly.
    if args.test_count is not None:
        test_count = args.test_count
        test_types: List[str] = json.loads(args.test_types) if args.test_types else []
        # ATDD success = at least one test generated (tests intentionally failing).
        # automation success = either:
        #   (a) at least one new test generated and no unchecked story tasks remain, or
        #   (b) validation-only rerun with no unchecked story tasks remaining.
        if qa_mode == "atdd":
            status = "0" if test_count > 0 else "1"
        else:
            content = story_file.read_text(encoding="utf-8")
            unchecked = len(UNCHECKED_RE.findall(content))
            status = "0" if unchecked == 0 and (test_count > 0 or validation_only) else "1"
    else:
        # Fallback heuristic when caller did not pass explicit counts.
        content = story_file.read_text(encoding="utf-8")
        content_lower = content.lower()
        test_types = []
        if "e2e" in content_lower or "playwright" in content_lower or "end-to-end" in content_lower:
            test_types.append("e2e")
        if "api test" in content_lower or "api-test" in content_lower:
            test_types.append("api")
        if "unit test" in content_lower or "xunit" in content_lower or "hardhat" in content_lower:
            test_types.append("unit")
        test_file_re = re.compile(r"\.(spec|test)\.(js|ts|mjs)|Test\.cs|\.test\.sol")
        test_count = len(test_file_re.findall(content))
        unchecked = len(UNCHECKED_RE.findall(content))
        if qa_mode == "atdd":
            status = "0" if test_count > 0 else "1"
        else:
            status = "0" if unchecked == 0 and (test_count > 0 or validation_only) else "1"

    result_payload = {
        "status": status,
        "qa_mode": qa_mode,
        "test_count": test_count,
        "test_types": test_types,
    }
    if qa_mode == "automation":
        result_payload["result_mode"] = "validation_only" if validation_only else "generated"

    result = json.dumps(result_payload)
    print(f"{SENTINEL}{result}{SENTINEL}")
    return 0


# ---------------------------------------------------------------------------
# main — argparse dispatcher
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic automation for zone-qa skill phases 0, 1, 2, 4, 5, 6."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # sync-superrepo
    p_sync = subparsers.add_parser("sync-superrepo", help="Phase 0: Pull latest super-repo branch")
    p_sync.add_argument("--repo-root", default=".", help="Repository root directory")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="Phase 1: Resolve story key to story")
    p_resolve.add_argument("--story-key", required=True, help="story key (e.g. BMAD-152)")
    p_resolve.add_argument(
        "--qa-mode",
        default=None,
        choices=["atdd", "automation"],
        help="Optional QA mode input; overrides story qa_mode when supplied",
    )
    p_resolve.add_argument("--repo-root", default=".", help="Repository root directory")

    # prepare-branches
    p_branches = subparsers.add_parser("prepare-branches", help="Phase 2: Prepare module branches")
    p_branches.add_argument("--story-file", required=True, help="Path to story markdown file")
    p_branches.add_argument(
        "--qa-mode",
        required=True,
        choices=["atdd", "automation"],
        help="QA mode",
    )
    p_branches.add_argument("--story-key", required=True, help="story key")
    p_branches.add_argument("--story-key", required=True, help="Story key identifier")
    p_branches.add_argument("--epic-branch", default=None, help="Epic integration branch name")
    p_branches.add_argument("--initiative-branch", default=None, help="Initiative integration branch name")
    p_branches.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-modules
    p_commit_sub = subparsers.add_parser("commit-modules", help="Phase 4: Commit and push per sub-repo")
    p_commit_sub.add_argument("--modules", required=True, help="JSON array of module paths")
    p_commit_sub.add_argument("--story-key", required=True, help="story key")
    p_commit_sub.add_argument("--title", required=True, help="BMAD story title for commit message")
    p_commit_sub.add_argument("--suffix", default="test generation complete", help="Commit message suffix")
    p_commit_sub.add_argument(
        "--qa-mode",
        required=True,
        choices=["atdd", "automation"],
        help="QA mode",
    )
    p_commit_sub.add_argument("--story-key", required=True, help="Story key identifier")
    p_commit_sub.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-superrepo
    p_commit_super = subparsers.add_parser("commit-superrepo", help="Phase 4: Commit and push super-repo")
    p_commit_super.add_argument("--story-key", required=True, help="story key")
    p_commit_super.add_argument("--title", required=True, help="BMAD story title for commit message")
    p_commit_super.add_argument("--suffix", default="test generation complete; module updates", help="Commit message suffix")
    p_commit_super.add_argument("--repo-root", default=".", help="Repository root directory")

    # transition-jira
    p_jira = subparsers.add_parser("transition-jira", help="Phase 5: Transition story (best-effort)")
    p_jira.add_argument("--story-key", required=True, help="story key")
    p_jira.add_argument("--target-status", required=True, help="Target Jira status (e.g. 'In QA')")
    group = p_jira.add_mutually_exclusive_group()
    group.add_argument("--comment", default=None, help="Optional transition comment")
    group.add_argument("--comment-file", default=None, help="Read transition comment from a file")
    group.add_argument("--comment-stdin", action="store_true", help="Read transition comment from stdin")
    p_jira.add_argument("--comment-format", default="plain", choices=["plain", "markdown"],
                        help="Format of the transition comment content")
    p_jira.add_argument("--repo-root", default=".", help="Repository root directory")

    # status
    p_status = subparsers.add_parser("status", help="Phase 6: Output status sentinel")
    p_status.add_argument("--story-file", default=None, help="Path to story markdown file")
    p_status.add_argument("--story-key", default=None, help="story key (fallback resolution when --story-file omitted)")
    p_status.add_argument(
        "--qa-mode",
        default="automation",
        choices=["atdd", "automation"],
        help="QA mode",
    )
    p_status.add_argument("--repo-root", default=".", help="Repository root directory")
    p_status.add_argument(
        "--test-count",
        type=int,
        default=None,
        help="Number of tests generated (tracked by agent during Phase 3)",
    )
    p_status.add_argument(
        "--test-types",
        default=None,
        help='JSON array of test type strings, e.g. \'["unit","e2e"]\' (tracked by agent during Phase 3)',
    )
    p_status.add_argument(
        "--validation-only",
        action="store_true",
        help="Automation-mode success path when no new tests were created and the run only validated existing coverage",
    )

    # prewarm
    p_prewarm = subparsers.add_parser("prewarm", help="Phases 0-2.5: Sync, resolve, prepare, load skills")
    p_prewarm.add_argument("--story-key", required=True, help="story key")
    p_prewarm.add_argument("--qa-mode", default=None, choices=["atdd", "automation"], help="QA mode")
    p_prewarm.add_argument("--repo-root", default=".", help="Repository root directory")

    parsed = parser.parse_args()

    dispatch = {
        "sync-superrepo": cmd_sync_superrepo,
        "resolve": cmd_resolve,
        "prepare-branches": cmd_prepare_branches,
        "prewarm": cmd_prewarm,
        "commit-modules": cmd_commit_modules,
        "commit-superrepo": cmd_commit_superrepo,
        "transition-jira": cmd_transition_jira,
        "status": cmd_status,
    }

    handler = dispatch.get(parsed.command)
    if handler is None:
        die(f"Unknown command: {parsed.command}")

    return handler(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
