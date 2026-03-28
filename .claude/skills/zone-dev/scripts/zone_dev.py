#!/usr/bin/env python3
"""Deterministic automation for zone-dev skill phases 1, 2, 4, 5, 6.

Adapted for GymOps monorepo (GitHub-based, no Jira/modules).
"""

from __future__ import annotations

import argparse
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

SENTINEL = "###ZONE-DEV-RESULT###"
SRC_REF_RE = re.compile(r"(?:src|prisma|tests)/[\w/.-]+")
UNCHECKED_RE = re.compile(r"- \[ \]")
SKILL_MAP_FILENAME = "module-skill-map.yaml"


def _resolve_story_file(story_key: str, repo_root: Path) -> Path:
    """Resolve a story key to its story file path."""
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
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, check=check)


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


# ---------------------------------------------------------------------------
# Domain skill resolution (monorepo: maps src paths to skills)
# ---------------------------------------------------------------------------

def resolve_domain_skills(src_paths: List[str], repo_root: Path) -> List[Dict[str, Any]]:
    """Map source paths to domain skills via module-skill-map.yaml.

    Returns a deduplicated list of dicts: {skill, path, exists}.
    """
    script_dir = Path(__file__).resolve().parent.parent
    map_path = script_dir / SKILL_MAP_FILENAME

    if not map_path.exists():
        print(f"warning: skill map not found: {map_path}", file=sys.stderr)
        return []

    with map_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh)

    modules = data.get("modules", {}) if isinstance(data, dict) else {}
    default_skill = data.get("default", {}).get("skill", "zone-frontend") if isinstance(data, dict) else "zone-frontend"

    seen: set[str] = set()
    result: List[Dict[str, Any]] = []
    skills_base = repo_root / ".claude" / "skills"

    for src_path in src_paths:
        matched = False
        for module_prefix, module_config in modules.items():
            if src_path.startswith(module_prefix):
                skill = module_config.get("skill", default_skill) if isinstance(module_config, dict) else default_skill
                if skill not in seen:
                    seen.add(skill)
                    skill_path = skills_base / skill / "SKILL.md"
                    result.append({"skill": skill, "path": str(skill_path), "exists": skill_path.exists()})
                matched = True
                break
        if not matched and default_skill not in seen:
            seen.add(default_skill)
            skill_path = skills_base / default_skill / "SKILL.md"
            result.append({"skill": default_skill, "path": str(skill_path), "exists": skill_path.exists()})

    return result


# ---------------------------------------------------------------------------
# sync-repo (Phase 0)
# ---------------------------------------------------------------------------

def cmd_sync_superrepo(args: argparse.Namespace) -> int:
    """Phase 0: Pull latest repo branch before starting work."""
    cwd = str(Path(args.repo_root).resolve())
    branch = _current_branch(cwd)

    git(["fetch", "origin"], cwd=cwd)
    result = git(["pull", "--rebase", "origin", branch], cwd=cwd, check=False)

    if result.returncode != 0:
        git(["rebase", "--abort"], cwd=cwd, check=False)
        result = git(["pull", "--no-rebase", "origin", branch], cwd=cwd, check=False)
        if result.returncode != 0:
            git(["merge", "--abort"], cwd=cwd, check=False)
            die(f"Failed to sync branch '{branch}': {result.stderr.strip()}")

    emit_json({"action": "synced", "branch": branch})
    return 0


# ---------------------------------------------------------------------------
# resolve (Phase 1) — resolves story key to file path
# ---------------------------------------------------------------------------

def cmd_resolve(args: argparse.Namespace) -> int:
    """Resolve a story key to its story file and metadata."""
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key

    story_file_path = repo_root / "_bmad-output" / "implementation-artifacts" / "stories" / f"{story_key}.md"

    if not story_file_path.exists():
        die(f"Story file not found: {story_file_path}")

    content = story_file_path.read_text(encoding="utf-8")

    # Extract epic reference from frontmatter
    epic_match = re.search(r"epic:\s*[\"']?([^\"'\n]+)", content)
    epic_key = epic_match.group(1).strip() if epic_match else None

    # Derive branch names
    story_branch = f"feat/{story_key}"
    epic_branch = f"epic/{epic_key}" if epic_key else None

    result = {
        "story_key": story_key,
        "story_branch": story_branch,
        "story_file_path": str(story_file_path),
    }
    if epic_key:
        result["epic_key"] = epic_key
        result["epic_branch"] = epic_branch

    emit_json(result)
    return 0


# ---------------------------------------------------------------------------
# prepare-branches (Phase 2) — monorepo: just create branch
# ---------------------------------------------------------------------------

def cmd_prepare_branches(args: argparse.Namespace) -> int:
    """Create feature branch and resolve domain skills."""
    repo_root = Path(args.repo_root).resolve()
    story_branch = args.story_branch
    story_file = Path(args.story_file)
    cwd = str(repo_root)

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")

    # Extract src paths from story file
    src_paths = list(set(SRC_REF_RE.findall(content)))

    # Configure git
    git(["config", "user.name", "GymOps AI Agent"], cwd=cwd)
    git(["config", "user.email", "ai@gymops.dev"], cwd=cwd)

    # Check if branch exists
    ls_result = git(["ls-remote", "--heads", "origin", story_branch], cwd=cwd, check=False)
    remote_exists = bool(ls_result.stdout.strip())

    branch_status = "ok"
    if remote_exists:
        git(["checkout", story_branch], cwd=cwd, check=False)
        git(["pull", "origin", story_branch], cwd=cwd, check=False)
        branch_status = "checked_out_remote"
    else:
        local_check = git(["rev-parse", "--verify", story_branch], cwd=cwd, check=False)
        if local_check.returncode == 0:
            git(["checkout", story_branch], cwd=cwd)
            branch_status = "checked_out_local"
        else:
            git(["checkout", "-b", story_branch], cwd=cwd)
            branch_status = "created"

    domain_skills = resolve_domain_skills(src_paths, repo_root)

    emit_json({
        "branch": story_branch,
        "branch_status": branch_status,
        "src_paths": src_paths,
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

    # Phase 0: sync repo
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

    # Phase 1: resolve story
    try:
        story_file_path = repo_root / "_bmad-output" / "implementation-artifacts" / "stories" / f"{story_key}.md"
        if not story_file_path.exists():
            return _write_and_exit("blocked", f"STORY_FILE_MISSING: {story_file_path}", 1)

        content = story_file_path.read_text(encoding="utf-8")
        epic_match = re.search(r"epic:\s*[\"']?([^\"'\n]+)", content)
        epic_key = epic_match.group(1).strip() if epic_match else None

        story_branch = f"feat/{story_key}"
        resolve_data = {
            "story_key": story_key,
            "story_branch": story_branch,
            "story_file_path": str(story_file_path),
        }
        if epic_key:
            resolve_data["epic_key"] = epic_key
            resolve_data["epic_branch"] = f"epic/{epic_key}"

        context["resolve"] = resolve_data

    except Exception as exc:
        return _write_and_exit("blocked", f"RESOLVE_FAILED: {exc}", 1)

    # Phase 2: prepare branch
    try:
        src_paths = list(set(SRC_REF_RE.findall(content)))

        git(["config", "user.name", "GymOps AI Agent"], cwd=cwd)
        git(["config", "user.email", "ai@gymops.dev"], cwd=cwd)

        ls_result = git(["ls-remote", "--heads", "origin", story_branch], cwd=cwd, check=False)
        remote_exists = bool(ls_result.stdout.strip())

        if remote_exists:
            git(["checkout", story_branch], cwd=cwd, check=False)
            git(["pull", "origin", story_branch], cwd=cwd, check=False)
        else:
            local_check = git(["rev-parse", "--verify", story_branch], cwd=cwd, check=False)
            if local_check.returncode == 0:
                git(["checkout", story_branch], cwd=cwd)
            else:
                git(["checkout", "-b", story_branch], cwd=cwd)

        domain_skills = resolve_domain_skills(src_paths, repo_root)
        context["prepare_branches"] = {
            "branch": story_branch,
            "src_paths": src_paths,
            "domain_skills": domain_skills,
        }

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
# commit (Phase 4) — monorepo: commit and push all changes
# ---------------------------------------------------------------------------

def cmd_commit_modules(args: argparse.Namespace) -> int:
    """Phase 4: Commit and push code changes in monorepo."""
    repo_root = Path(args.repo_root).resolve()
    story_branch = args.story_branch
    story_key = args.story_key
    title = args.title
    cwd = str(repo_root)

    commit_msg = f"feat({story_key}): {title}\n\nCo-Authored-By: GymOps AI Agent <ai@gymops.dev>"

    status_result = git(["status", "--porcelain"], cwd=cwd, check=False)
    if not status_result.stdout.strip():
        emit_json({"results": [], "committed_count": 0, "skipped_count": 1})
        return 0

    try:
        git(["config", "user.name", "GymOps AI Agent"], cwd=cwd)
        git(["config", "user.email", "ai@gymops.dev"], cwd=cwd)
        git(["add", "-A"], cwd=cwd)
        git(["commit", "-m", commit_msg], cwd=cwd)
        commit_hash = git(["rev-parse", "HEAD"], cwd=cwd).stdout.strip()
        git_push_with_retry(["-u", "origin", story_branch], cwd=cwd)

        emit_json({
            "results": [{"path": ".", "action": "committed_and_pushed", "commit_hash": commit_hash}],
            "committed_count": 1,
            "skipped_count": 0,
        })
    except subprocess.CalledProcessError as exc:
        emit_json({
            "results": [{"path": ".", "action": "error", "error": exc.stderr.strip()}],
            "committed_count": 0,
            "skipped_count": 0,
        })
        return 1

    return 0


# ---------------------------------------------------------------------------
# commit-superrepo (Phase 5) — commit BMAD artifacts
# ---------------------------------------------------------------------------

def cmd_commit_superrepo(args: argparse.Namespace) -> int:
    """Phase 5: Commit and push _bmad-output/ artifacts."""
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key
    title = args.title
    cwd = str(repo_root)

    commit_msg = f"docs({story_key}): {title} - update story artifacts"

    git(["add", "_bmad-output/"], cwd=cwd, check=False)

    diff_result = git(["diff", "--cached", "--name-only"], cwd=cwd, check=False)
    staged = diff_result.stdout.strip()

    if not staged:
        emit_json({"action": "skipped", "reason": "no staged changes", "commit_hash": None, "branch": None, "pushed": False})
        return 0

    try:
        git(["commit", "-m", commit_msg], cwd=cwd)
        commit_hash = git(["rev-parse", "HEAD"], cwd=cwd).stdout.strip()
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).stdout.strip()
        git_push_with_retry(["origin", "HEAD"], cwd=cwd)
        emit_json({"action": "committed_and_pushed", "commit_hash": commit_hash, "branch": branch, "pushed": True})
    except subprocess.CalledProcessError as exc:
        emit_json({"action": "error", "error": exc.stderr.strip(), "commit_hash": None, "branch": None, "pushed": False})
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

    diff_result = git(["diff", "--cached", "--name-only"], cwd=cwd, check=False)
    staged = diff_result.stdout.strip()

    if not staged:
        emit_json({"action": "skipped", "reason": "no staged changes", "commit_hash": None, "branch": None, "pushed": False})
        return 0

    try:
        git(["commit", "-m", commit_msg], cwd=cwd)
        commit_hash = git(["rev-parse", "HEAD"], cwd=cwd).stdout.strip()
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).stdout.strip()
        git_push_with_retry(["origin", "HEAD"], cwd=cwd)
        emit_json({"action": "committed_and_pushed", "commit_hash": commit_hash, "branch": branch, "pushed": True})
    except subprocess.CalledProcessError as exc:
        emit_json({"action": "error", "error": exc.stderr.strip(), "commit_hash": None, "branch": None, "pushed": False})
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
        story_file = _resolve_story_file(args.story_key, Path(args.repo_root).resolve())

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
        description="Deterministic automation for zone-dev skill (GymOps monorepo)."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # sync-superrepo
    p_sync = subparsers.add_parser("sync-superrepo", help="Phase 0: Pull latest branch")
    p_sync.add_argument("--repo-root", default=".", help="Repository root directory")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="Phase 1: Resolve story key to file")
    p_resolve.add_argument("--story-key", required=True, help="Story key (e.g. 1-1-user-auth)")
    p_resolve.add_argument("--repo-root", default=".", help="Repository root directory")

    # prepare-branches
    p_branches = subparsers.add_parser("prepare-branches", help="Phase 2: Create feature branch")
    p_branches.add_argument("--story-file", required=True, help="Path to story markdown file")
    p_branches.add_argument("--story-branch", required=True, help="Branch name for the story")
    p_branches.add_argument("--epic-branch", default=None, help="Epic branch name")
    p_branches.add_argument("--initiative-branch", default=None, help="Initiative branch name")
    p_branches.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-modules (kept for compatibility, works as monorepo commit)
    p_commit_sub = subparsers.add_parser("commit-modules", help="Phase 4: Commit and push code")
    p_commit_sub.add_argument("--modules", default="[]", help="Ignored in monorepo mode")
    p_commit_sub.add_argument("--story-branch", required=True, help="Branch name")
    p_commit_sub.add_argument("--story-key", required=True, help="Story key")
    p_commit_sub.add_argument("--title", required=True, help="Story title for commit message")
    p_commit_sub.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-superrepo
    p_commit_super = subparsers.add_parser("commit-superrepo", help="Phase 5: Commit artifacts")
    p_commit_super.add_argument("--story-key", required=True, help="Story key")
    p_commit_super.add_argument("--title", required=True, help="Story title for commit message")
    p_commit_super.add_argument("--repo-root", default=".", help="Repository root directory")

    # prewarm
    p_prewarm = subparsers.add_parser("prewarm", help="Phases 0-2.5: Sync, resolve, prepare, load skills")
    p_prewarm.add_argument("--story-key", required=True, help="Story key")
    p_prewarm.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-planning
    p_commit_plan = subparsers.add_parser("commit-planning", help="Commit planning artifacts")
    p_commit_plan.add_argument("--message", required=True, help="Commit message")
    p_commit_plan.add_argument("--repo-root", default=".", help="Repository root directory")

    # status
    p_status = subparsers.add_parser("status", help="Phase 6: Output status sentinel")
    p_status.add_argument("--story-file", default=None, help="Path to story markdown file")
    p_status.add_argument("--story-key", default=None, help="Story key (fallback when --story-file omitted)")
    p_status.add_argument("--repo-root", default=".", help="Repository root directory")

    parsed = parser.parse_args()

    dispatch = {
        "sync-superrepo": cmd_sync_superrepo,
        "resolve": cmd_resolve,
        "prepare-branches": cmd_prepare_branches,
        "prewarm": cmd_prewarm,
        "commit-modules": cmd_commit_modules,
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
