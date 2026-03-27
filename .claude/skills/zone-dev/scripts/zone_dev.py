#!/usr/bin/env python3
"""Deterministic automation for zone-dev skill phases 1, 2, 4, 5, 6."""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

SENTINEL = "###ZONE-DEV-RESULT###"
MODULE_REF_RE = re.compile(r"modules/([\w.]+)")
UNCHECKED_RE = re.compile(r"- \[ \]")
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

    # Look up the parent epic
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

    result = {
        "bmad_id": bmad_id,
        "bmad_title": bmad_title,
        "story_key": story_key,
        "story_branch": story_branch,
        "story_file_path": str(story_file_path),
        "jira_key": jira_key,
    }
    if epic_branch:
        result["epic_key"] = epic_key
        result["epic_branch"] = epic_branch
        result["parent_jira_key"] = parent_jira_key

    # --- Initiative lookup ---
    initiative_branch = None
    sprint_status_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    if sprint_status_path.exists() and parent_jira_key:
        sprint_data = read_yaml(sprint_status_path)
        # Find the epic's bmad_id from the jira-key-map lookup we already did
        epic_bmad_id = None
        for item in items:
            if item.get("bmad_type") == "epic" and item.get("jira_key") == parent_jira_key:
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


def ensure_initiative_branch(
    initiative_branch: str, submodule_name: str, sub_dir: str, repo_root: Path,
) -> str:
    """Ensure the initiative branch exists in the submodule. Returns status string."""
    ls_result = git(["ls-remote", "--heads", "origin", initiative_branch], cwd=sub_dir)
    if bool(ls_result.stdout.strip()):
        git(["checkout", initiative_branch], cwd=sub_dir)
        git(["pull", "origin", initiative_branch], cwd=sub_dir)
        return "checked_out_remote"

    local_check = git(["rev-parse", "--verify", initiative_branch], cwd=sub_dir, check=False)
    if local_check.returncode == 0:
        git(["checkout", initiative_branch], cwd=sub_dir)
        return "checked_out_local"

    default_branch = get_default_branch(submodule_name, repo_root)
    git(["checkout", default_branch], cwd=sub_dir)
    git(["pull", "origin", default_branch], cwd=sub_dir)
    git(["checkout", "-b", initiative_branch], cwd=sub_dir)
    git(["push", "-u", "origin", initiative_branch], cwd=sub_dir)
    return "created"


def ensure_epic_branch(
    epic_branch: str, submodule_name: str, sub_dir: str, repo_root: Path,
    initiative_branch: Optional[str] = None,
) -> str:
    """Ensure the epic branch exists in the submodule. Returns status string."""
    # Check if epic branch exists on remote
    ls_result = git(["ls-remote", "--heads", "origin", epic_branch], cwd=sub_dir)
    remote_exists = bool(ls_result.stdout.strip())

    if remote_exists:
        git(["checkout", epic_branch], cwd=sub_dir)
        git(["pull", "origin", epic_branch], cwd=sub_dir)
        return "checked_out_remote"

    # Check if epic branch exists locally
    local_check = git(["rev-parse", "--verify", epic_branch], cwd=sub_dir, check=False)
    if local_check.returncode == 0:
        git(["checkout", epic_branch], cwd=sub_dir)
        return "checked_out_local"

    # Neither exists — create from base branch (initiative or default)
    if initiative_branch:
        base_branch = initiative_branch
    else:
        base_branch = get_default_branch(submodule_name, repo_root)
    git(["checkout", base_branch], cwd=sub_dir)
    git(["pull", "origin", base_branch], cwd=sub_dir)
    git(["checkout", "-b", epic_branch], cwd=sub_dir)
    git(["push", "-u", "origin", epic_branch], cwd=sub_dir)
    return "created"


PREWARM_MAX_WORKERS = int(os.environ.get("PREWARM_WORKERS", "4"))


def _prepare_one_submodule(
    name: str,
    repo_root: Path,
    story_branch: str,
    epic_branch: Optional[str],
    initiative_branch: Optional[str],
    target_branches: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Prepare a single submodule: init, fetch, checkout/create story branch.

    Args:
        target_branches: list of branch names to fetch instead of all refs.
            When None, falls back to full ``git fetch origin``.
    """
    sub_path = repo_root / "modules" / name
    entry: Dict[str, Any] = {"path": f"modules/{name}", "status": "ok", "created": False}

    try:
        git(["submodule", "update", "--init", "--depth", "1", f"modules/{name}"], cwd=str(repo_root))
    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"submodule init failed: {exc.stderr.strip()}"
        return entry

    sub_dir = str(sub_path)
    git(["config", "user.name", "Zone AI Agent"], cwd=sub_dir)
    git(["config", "user.email", "ai@zonenetwork.com"], cwd=sub_dir)

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
            ["ls-remote", "--heads", "origin", story_branch],
            cwd=sub_dir,
        )
        remote_exists = bool(ls_result.stdout.strip())

        if remote_exists:
            git(["checkout", story_branch], cwd=sub_dir)
            git(["pull", "origin", story_branch], cwd=sub_dir)
            entry["status"] = "checked_out_remote"
        else:
            local_check = git(
                ["rev-parse", "--verify", story_branch],
                cwd=sub_dir,
                check=False,
            )
            if local_check.returncode == 0:
                git(["checkout", story_branch], cwd=sub_dir)
                entry["status"] = "checked_out_local"
            else:
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
    epic_branch = getattr(args, "epic_branch", None)
    initiative_branch = getattr(args, "initiative_branch", None)
    story_file = Path(args.story_file)

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")

    matches = MODULE_REF_RE.findall(content)
    seen = set()
    submodule_names = []
    for m in matches:
        if m not in seen:
            seen.add(m)
            submodule_names.append(m)

    # Build targeted fetch list
    target_branches = [story_branch]
    if epic_branch:
        target_branches.append(epic_branch)
    if initiative_branch:
        target_branches.append(initiative_branch)

    # Filter to existing dirs
    valid_names = [n for n in submodule_names if (repo_root / "modules" / n).is_dir()]

    # Process submodules in parallel
    results: List[Dict[str, Any]] = []
    with ThreadPoolExecutor(max_workers=PREWARM_MAX_WORKERS) as pool:
        futures = {
            pool.submit(
                _prepare_one_submodule, name, repo_root,
                story_branch, epic_branch, initiative_branch, target_branches,
            ): name
            for name in valid_names
        }
        for future in as_completed(futures):
            results.append(future.result())

    # Resolve domain skills from successfully prepared submodules
    prepared_names = [
        Path(r["path"]).name for r in results if r["status"] != "error"
    ]
    domain_skills = resolve_domain_skills(prepared_names, repo_root)

    emit_json({
        "submodules": results,
        "count": len(results),
        "domain_skills": domain_skills,
    })
    return 0


# ---------------------------------------------------------------------------
# prewarm (Phases 0-2.5 combined)
# ---------------------------------------------------------------------------

def cmd_prewarm(args: argparse.Namespace) -> int:
    """Run Phases 0-2.5 deterministically and write context files for the agent."""
    repo_root = Path(args.repo_root).resolve()
    jira_key = args.jira_key
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
        (repo_root / ".zone-prewarm-context.json").write_text(
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
        ns = argparse.Namespace(jira_key=jira_key, repo_root=str(repo_root))
        # Reuse resolve logic inline to capture the dict instead of emitting
        map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "jira-key-map.yaml"
        data = read_yaml(map_path)
        active_project_key = data.get("active_project_key")
        if not active_project_key:
            return _write_and_exit("blocked", "KEY_NOT_FOUND: active_project_key not found in jira-key-map.yaml", 1)

        items = data.get("projects", {}).get(active_project_key, {}).get("items", [])
        bmad_id = bmad_title = None
        for item in items:
            if item.get("jira_key") == jira_key and item.get("bmad_type") == "story":
                bmad_id = str(item["bmad_id"])
                bmad_title = str(item["bmad_title"])
                break
        if bmad_id is None:
            return _write_and_exit("blocked", f"KEY_NOT_FOUND: Jira key '{jira_key}' not found in jira-key-map.yaml", 1)

        parent_jira_key = epic_key = epic_branch = None
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

        story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)
        story_branch = f"agent/story/{jira_key}-{story_key}"
        story_file_path = repo_root / "_bmad-output" / "implementation-artifacts" / "stories" / f"{story_key}.md"

        if not story_file_path.exists():
            return _write_and_exit("blocked", f"STORY_FILE_MISSING: {story_file_path}", 1)

        # Initiative lookup
        initiative_branch = None
        sprint_status_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
        if sprint_status_path.exists() and parent_jira_key:
            sprint_data = read_yaml(sprint_status_path)
            epic_bmad_id_raw = None
            for item in items:
                if item.get("bmad_type") == "epic" and item.get("jira_key") == parent_jira_key:
                    epic_bmad_id_raw = str(item["bmad_id"])
                    break
            if epic_bmad_id_raw:
                for init_info in sprint_data.get("initiatives", []):
                    epic_ids = [str(e["id"]) for e in init_info.get("epics", []) if isinstance(e, dict)]
                    if epic_bmad_id_raw in epic_ids:
                        initiative_branch = init_info.get("branch")
                        break

        resolve_data = {
            "bmad_id": bmad_id, "bmad_title": bmad_title, "story_key": story_key,
            "story_branch": story_branch, "story_file_path": str(story_file_path),
            "jira_key": jira_key,
        }
        if epic_branch:
            resolve_data["epic_key"] = epic_key
            resolve_data["epic_branch"] = epic_branch
            resolve_data["parent_jira_key"] = parent_jira_key
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
        submodule_names = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                submodule_names.append(m)

        target_fetch = [story_branch]
        if epic_branch:
            target_fetch.append(epic_branch)
        if initiative_branch:
            target_fetch.append(initiative_branch)

        valid_names = [n for n in submodule_names if (repo_root / "modules" / n).is_dir()]

        results: List[Dict[str, Any]] = []
        with ThreadPoolExecutor(max_workers=PREWARM_MAX_WORKERS) as pool:
            futures = {
                pool.submit(
                    _prepare_one_submodule, name, repo_root,
                    story_branch, epic_branch, initiative_branch, target_fetch,
                ): name
                for name in valid_names
            }
            for future in as_completed(futures):
                results.append(future.result())

        prepared_names = [Path(r["path"]).name for r in results if r["status"] != "error"]
        domain_skills = resolve_domain_skills(prepared_names, repo_root)

        has_errors = any(r["status"] == "error" for r in results)
        if not prepared_names:
            context["prepare_branches"] = {"submodules": results, "count": 0, "domain_skills": domain_skills}
            return _write_and_exit("blocked", "PREPARE_FAILED: no submodules prepared successfully", 1)

        context["prepare_branches"] = {
            "submodules": results,
            "count": len(prepared_names),
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
    (repo_root / ".zone-prewarm-context.json").write_text(
        json.dumps(context, indent=2), encoding="utf-8",
    )
    (repo_root / ".zone-prewarm-skills.md").write_text(
        "\n\n".join(skills_content_parts), encoding="utf-8",
    )

    emit_json(context)
    return 0 if context["prewarm_status"] == "success" else 2


# ---------------------------------------------------------------------------
# commit-submodules (Phase 4)
# ---------------------------------------------------------------------------

def cmd_commit_submodules(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    story_branch = args.story_branch
    jira_key = args.jira_key
    title = args.title

    try:
        submodules = json.loads(args.submodules)
    except json.JSONDecodeError as exc:
        die(f"Invalid --submodules JSON: {exc}")

    commit_msg = f"{jira_key}: {title} - dev story implementation"
    results = []
    committed_count = 0
    skipped_count = 0

    for sub_path in submodules:
        full_path = str(repo_root / sub_path)
        entry: Dict[str, Any] = {"path": sub_path}

        if not os.path.isdir(full_path):
            entry["action"] = "error"
            entry["error"] = f"directory not found: {full_path}"
            results.append(entry)
            continue

        # Check for changes
        status_result = git(["status", "--porcelain"], cwd=full_path, check=False)
        if not status_result.stdout.strip():
            entry["action"] = "skipped"
            entry["reason"] = "no changes"
            skipped_count += 1
            results.append(entry)
            continue

        try:
            git(["config", "user.name", "Zone AI Agent"], cwd=full_path)
            git(["config", "user.email", "ai@zonenetwork.com"], cwd=full_path)
            # Reset CI-regenerated lock files before staging (Run14-H1)
            for lockfile in ("package-lock.json", "yarn.lock"):
                subprocess.run(["git", "checkout", "HEAD", "--", lockfile], cwd=full_path, check=False)
            git(["add", "-A"], cwd=full_path)
            commit_result = git(["commit", "-m", commit_msg], cwd=full_path)

            # Extract commit hash
            log_result = git(["rev-parse", "HEAD"], cwd=full_path)
            entry["commit_hash"] = log_result.stdout.strip()

            git_push_with_retry(["-u", "origin", story_branch], cwd=full_path)
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
# commit-superrepo (Phase 5)
# ---------------------------------------------------------------------------

def cmd_commit_superrepo(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    jira_key = args.jira_key
    title = args.title
    cwd = str(repo_root)

    commit_msg = f"{jira_key}: {title} - dev story complete; submodule updates"

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
# commit-planning (interactive skills)
# ---------------------------------------------------------------------------

def cmd_commit_planning(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    commit_msg = args.message
    cwd = str(repo_root)

    git(["add", "_bmad-output/"], cwd=cwd, check=False)
    git(["reset", "HEAD", "modules/"], cwd=cwd, check=False)

    diff_result = git(["diff", "--cached", "--name-only"], cwd=cwd, check=False)
    staged = diff_result.stdout.strip()

    if not staged:
        emit_json({"action": "skipped", "reason": "no staged changes in _bmad-output/", "commit_hash": None, "branch": None, "pushed": False})
        return 0

    try:
        git(["commit", "-m", commit_msg], cwd=cwd)
        commit_hash = git(["rev-parse", "HEAD"], cwd=cwd).stdout.strip()
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).stdout.strip()
        git_push_with_retry(["origin", "HEAD"], cwd=cwd)
        emit_json({"action": "committed_and_pushed", "commit_hash": commit_hash, "branch": branch, "pushed": True})
    except subprocess.CalledProcessError as exc:
        emit_json({"action": "error", "error": exc.stderr.strip() or exc.stdout.strip(), "commit_hash": None, "branch": None, "pushed": False})
        return 1

    return 0


# ---------------------------------------------------------------------------
# status (Phase 6)
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    story_file_arg = getattr(args, "story_file", None)
    if story_file_arg:
        story_file = Path(story_file_arg)
    else:
        story_file = _resolve_story_file(args.jira_key, Path(args.repo_root).resolve())

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")
    unchecked = len(UNCHECKED_RE.findall(content))

    status = "0" if unchecked == 0 else "1"
    result = json.dumps({"status": status, "unchecked": unchecked})
    print(f"{SENTINEL}{result}{SENTINEL}")
    return 0


# ---------------------------------------------------------------------------
# main — argparse dispatcher
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic automation for zone-dev skill phases 1, 2, 4, 5, 6."
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
    p_branches = subparsers.add_parser("prepare-branches", help="Phase 2: Prepare submodule story branches")
    p_branches.add_argument("--story-file", required=True, help="Path to story markdown file")
    p_branches.add_argument("--story-branch", required=True, help="Branch name for the story")
    p_branches.add_argument("--epic-branch", default=None, help="Epic integration branch name")
    p_branches.add_argument("--initiative-branch", default=None, help="Initiative integration branch name")
    p_branches.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-submodules
    p_commit_sub = subparsers.add_parser("commit-submodules", help="Phase 4: Commit and push per sub-repo")
    p_commit_sub.add_argument("--submodules", required=True, help="JSON array of submodule paths")
    p_commit_sub.add_argument("--story-branch", required=True, help="Branch name for the story")
    p_commit_sub.add_argument("--jira-key", required=True, help="Jira issue key")
    p_commit_sub.add_argument("--title", required=True, help="BMAD story title for commit message")
    p_commit_sub.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-superrepo
    p_commit_super = subparsers.add_parser("commit-superrepo", help="Phase 5: Commit and push super-repo")
    p_commit_super.add_argument("--story-key", required=True, help="Story key identifier")
    p_commit_super.add_argument("--jira-key", required=True, help="Jira issue key")
    p_commit_super.add_argument("--title", required=True, help="BMAD story title for commit message")
    p_commit_super.add_argument("--repo-root", default=".", help="Repository root directory")

    # prewarm
    p_prewarm = subparsers.add_parser("prewarm", help="Phases 0-2.5: Sync, resolve, prepare, load skills")
    p_prewarm.add_argument("--jira-key", required=True, help="Jira issue key")
    p_prewarm.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-planning
    p_commit_plan = subparsers.add_parser("commit-planning", help="Commit and push _bmad-output/ planning artifacts")
    p_commit_plan.add_argument("--message", required=True, help="Commit message")
    p_commit_plan.add_argument("--repo-root", default=".", help="Repository root directory")

    # status
    p_status = subparsers.add_parser("status", help="Phase 6: Output status sentinel")
    p_status.add_argument("--story-file", default=None, help="Path to story markdown file")
    p_status.add_argument("--jira-key", default=None, help="Jira issue key (fallback resolution when --story-file omitted)")
    p_status.add_argument("--repo-root", default=".", help="Repository root directory")

    parsed = parser.parse_args()

    dispatch = {
        "sync-superrepo": cmd_sync_superrepo,
        "resolve": cmd_resolve,
        "prepare-branches": cmd_prepare_branches,
        "prewarm": cmd_prewarm,
        "commit-submodules": cmd_commit_submodules,
        "commit-superrepo": cmd_commit_superrepo,
        "commit-planning": cmd_commit_planning,
        "status": cmd_status,
    }

    handler = dispatch.get(parsed.command)
    if handler is None:
        die(f"Unknown command: {parsed.command}")

    return handler(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
