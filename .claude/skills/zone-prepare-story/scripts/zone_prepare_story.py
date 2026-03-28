#!/usr/bin/env python3
"""Deterministic automation for zone-prepare-story skill phases 1, 2, 2.7, 2.8, 4, 5, 5.5, 6."""

from __future__ import annotations

import argparse
import json
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

SENTINEL = "###ZONE-PREPARE-STORY-RESULT###"
SRC_REF_RE = re.compile(r"(?:src|prisma|tests)/[\w/.-]+")
SKILL_MAP_FILENAME = "module-skill-map.yaml"
READY_FOR_DEV_RE = re.compile(r"Status:\s*ready-for-dev", re.IGNORECASE)


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


# ---------------------------------------------------------------------------
# Domain skill resolution
# ---------------------------------------------------------------------------

def resolve_domain_skills(module_names: List[str], repo_root: Path) -> List[Dict[str, Any]]:
    """Map module names to domain skills via module-skill-map.yaml.

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

    map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "story-key-map.yaml"
    data = read_yaml(map_path)

    active_project_key = data.get("active_project_key")
    if not active_project_key:
        die("active_project_key not found in story-key-map.yaml")

    projects = data.get("projects", {})
    project = projects.get(active_project_key, {})
    items = project.get("items", [])

    bmad_id = None
    bmad_title = None
    parent_story_key = None
    for item in items:
        if item.get("story_key") == story_key and item.get("bmad_type") == "story":
            bmad_id = str(item["bmad_id"])
            bmad_title = str(item["bmad_title"])
            parent_story_key = item.get("parent_story_key")
            break

    if bmad_id is None:
        die(f"story key '{story_key}' not found in story-key-map.yaml (project={active_project_key})")

    # Derive story_key: dots->dashes in bmad_id + '-' + slugify(title)
    story_key = bmad_id.replace(".", "-") + "-" + slugify(bmad_title)

    story_file_path = (
        repo_root
        / "_bmad-output"
        / "implementation-artifacts"
        / "stories"
        / f"{story_key}.md"
    )

    # Load sprint-status.yaml once for both status validation and initiative lookup
    sprint_status_path = repo_root / "_bmad-output" / "implementation-artifacts" / "sprint-status.yaml"
    sprint_data = None
    if sprint_status_path.exists():
        sprint_data = read_yaml(sprint_status_path)
        dev_status = sprint_data.get("development_status", {})
        current_status = dev_status.get(story_key)
        if current_status and current_status != "backlog":
            die(
                f"Story '{story_key}' is in '{current_status}' status, expected 'backlog'. "
                f"Only backlog stories can be prepared."
            )
    else:
        print("warning: sprint-status.yaml not found, skipping status validation", file=sys.stderr)

    # --- Initiative lookup ---
    initiative_branch = None
    if sprint_data and parent_story_key:
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

    # NOTE: story file does NOT need to exist — create-story workflow produces it

    result: Dict[str, Any] = {
        "bmad_id": bmad_id,
        "bmad_title": bmad_title,
        "story_key": story_key,
        "story_file_path": str(story_file_path),
        "story_key": story_key,
    }
    if parent_story_key:
        result["parent_story_key"] = parent_story_key
    if initiative_branch:
        result["initiative_branch"] = initiative_branch

    # --- Epic branch computation ---
    epic_branch = None
    if parent_story_key:
        for item in items:
            if item.get("bmad_type") == "epic" and item.get("story_key") == parent_story_key:
                epic_bmad_id = str(item["bmad_id"]).replace(".", "-")
                epic_key = epic_bmad_id + "-" + slugify(str(item["bmad_title"]))
                epic_branch = f"agent/epic/{parent_story_key}-{epic_key}"
                break

    if epic_branch:
        result["epic_branch"] = epic_branch

    emit_json(result)
    return 0


# ---------------------------------------------------------------------------
# resolve-domain-skills (Phase 2)
# ---------------------------------------------------------------------------

def cmd_resolve_domain_skills(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    bmad_id = args.bmad_id

    epics_path = repo_root / "_bmad-output" / "planning-artifacts" / "epics.md"

    if not epics_path.exists():
        print("warning: epics.md not found, proceeding without domain skills", file=sys.stderr)
        emit_json({"domain_skills": [], "modules": []})
        return 0

    content = epics_path.read_text(encoding="utf-8")

    # Parse bmad_id into epic_num.story_num (e.g., "2.1")
    # Build pattern to find "### Story 2.1:" header
    story_header_pattern = re.compile(
        rf"### Story {re.escape(bmad_id)}:\s*.*",
        re.IGNORECASE,
    )

    # Find the story section
    match = story_header_pattern.search(content)
    if not match:
        print(f"warning: story section for '{bmad_id}' not found in epics.md", file=sys.stderr)
        emit_json({"domain_skills": [], "modules": []})
        return 0

    # Extract section from match to next story/epic header or end of file
    start = match.start()
    # Find next ### or ## header after this one
    next_header = re.search(r"\n##[#]?\s", content[match.end():])
    if next_header:
        end = match.end() + next_header.start()
    else:
        end = len(content)

    section = content[start:end]

    # Extract **Repo:** modules/{name} references
    repo_matches = SRC_REF_RE.findall(section)

    # Deduplicate while preserving order
    seen: set[str] = set()
    module_names: List[str] = []
    for name in repo_matches:
        if name not in seen:
            seen.add(name)
            module_names.append(name)

    if not module_names:
        print(f"warning: no module references found in story {bmad_id} section", file=sys.stderr)
        emit_json({"domain_skills": [], "modules": []})
        return 0

    domain_skills = resolve_domain_skills(module_names, repo_root)

    emit_json({
        "domain_skills": domain_skills,
        "modules": module_names,
    })
    return 0


# ---------------------------------------------------------------------------
# checkout-modules (Phase 2.7)
# ---------------------------------------------------------------------------

def cmd_checkout_modules(args: argparse.Namespace) -> int:
    """Checkout the best research branch in each module (read-only, no create/push)."""
    repo_root = Path(args.repo_root).resolve()
    epic_branch = getattr(args, "epic_branch", None)
    initiative_branch = getattr(args, "initiative_branch", None)

    try:
        modules = json.loads(args.modules)
    except json.JSONDecodeError as exc:
        die(f"Invalid --modules JSON: {exc}")

    results = []
    for name in modules:
        sub_path = repo_root / "modules" / name
        entry: Dict[str, Any] = {"module": name, "status": "ok"}

        if not sub_path.is_dir():
            entry["status"] = "skipped"
            entry["reason"] = "directory not found"
            results.append(entry)
            continue

        sub_dir = str(sub_path)

        try:
            # Initialize module if needed
            git(["module", "update", "--init", f"modules/{name}"], cwd=str(repo_root))
        except subprocess.CalledProcessError as exc:
            entry["status"] = "error"
            entry["error"] = f"module init failed: {exc.stderr.strip()}"
            results.append(entry)
            continue

        git(["config", "user.name", "GymOps AI Agent"], cwd=sub_dir)
        git(["config", "user.email", "ai@gymops.dev"], cwd=sub_dir)

        try:
            git(["fetch", "origin"], cwd=sub_dir)
        except subprocess.CalledProcessError as exc:
            entry["status"] = "error"
            entry["error"] = f"fetch failed: {exc.stderr.strip()}"
            results.append(entry)
            continue

        # Priority: epic branch → initiative branch → default branch
        checked_out = None

        if epic_branch:
            ls_result = git(["ls-remote", "--heads", "origin", epic_branch], cwd=sub_dir)
            if ls_result.stdout.strip():
                git(["checkout", epic_branch], cwd=sub_dir, check=False)
                git(["pull", "origin", epic_branch], cwd=sub_dir, check=False)
                checked_out = epic_branch
                entry["branch"] = epic_branch
                entry["source"] = "epic"

        if not checked_out and initiative_branch:
            ls_result = git(["ls-remote", "--heads", "origin", initiative_branch], cwd=sub_dir)
            if ls_result.stdout.strip():
                git(["checkout", initiative_branch], cwd=sub_dir, check=False)
                git(["pull", "origin", initiative_branch], cwd=sub_dir, check=False)
                checked_out = initiative_branch
                entry["branch"] = initiative_branch
                entry["source"] = "initiative"

        if not checked_out:
            default_branch = get_default_branch(name, repo_root)
            git(["checkout", default_branch], cwd=sub_dir, check=False)
            git(["pull", "origin", default_branch], cwd=sub_dir, check=False)
            checked_out = default_branch
            entry["branch"] = default_branch
            entry["source"] = "default"

        results.append(entry)

    emit_json({"modules": results, "count": len(results)})
    return 0


# ---------------------------------------------------------------------------
# resolve-nuget-deps (Phase 2.8)
# ---------------------------------------------------------------------------

def cmd_resolve_nuget_deps(args: argparse.Namespace) -> int:
    """Phase 2.8: Resolve cross-repo NuGet dependencies using build tags."""
    repo_root = Path(args.repo_root).resolve()
    branch = args.branch or ""
    initiative_branch = getattr(args, "initiative_branch", "") or ""

    try:
        modules = json.loads(args.modules)
    except json.JSONDecodeError as exc:
        die(f"Invalid --modules JSON: {exc}")

    # Load nuget-resolver config
    config_path = repo_root / ".claude" / "skills" / "nuget-resolver" / "config.yaml"
    if not config_path.exists():
        emit_json({"has_nuget_deps": False, "dependencies": [], "reason": "nuget-resolver config not found"})
        return 0

    config = read_yaml(config_path)
    cross_repo_deps = config.get("cross_repo_deps", {})
    package_mappings = config.get("package_mappings", {})
    version_rules = config.get("version_rules", {})
    stable_branches = [b.lower() for b in version_rules.get("stable_branches", ["master", "main"])]
    dev_suffix = version_rules.get("dev_suffix", "-dev")

    # Strip "modules/" prefix for matching
    sub_names = [s.replace("modules/", "") if s.startswith("modules/") else s for s in modules]

    dependencies = []
    for downstream in sub_names:
        upstream_repos = cross_repo_deps.get(downstream, [])
        if not upstream_repos:
            continue

        for upstream in upstream_repos:
            upstream_path = repo_root / "modules" / upstream
            dep_entry: Dict[str, Any] = {
                "downstream_repo": downstream,
                "upstream_repo": upstream,
                "packages": package_mappings.get(upstream, []),
            }

            # Init upstream module (may not be initialized in CI)
            git(["module", "update", "--init", f"modules/{upstream}"], cwd=str(repo_root), check=False)

            if not upstream_path.is_dir():
                dep_entry["build_tag"] = None
                dep_entry["resolved_version"] = None
                dep_entry["warning"] = f"upstream module modules/{upstream} not found"
                dependencies.append(dep_entry)
                continue

            # Fetch to get latest branches and tags
            git(["fetch", "origin"], cwd=str(upstream_path), check=False)

            # Checkout best available branch: epic -> initiative -> default
            checked_out = None
            for candidate in [branch, initiative_branch]:
                if not candidate:
                    continue
                ls_result = git(["ls-remote", "--heads", "origin", candidate],
                                cwd=str(upstream_path), check=False)
                if ls_result.returncode == 0 and ls_result.stdout.strip():
                    git(["checkout", candidate], cwd=str(upstream_path), check=False)
                    git(["pull", "origin", candidate], cwd=str(upstream_path), check=False)
                    checked_out = candidate
                    break
            if not checked_out:
                default_br = get_default_branch(upstream, repo_root)
                git(["checkout", default_br], cwd=str(upstream_path), check=False)
                git(["pull", "origin", default_br], cwd=str(upstream_path), check=False)
                checked_out = default_br

            # Get HEAD commit of upstream module
            head_result = git(["rev-parse", "HEAD"], cwd=str(upstream_path), check=False)
            if head_result.returncode != 0:
                dep_entry["build_tag"] = None
                dep_entry["resolved_version"] = None
                dep_entry["warning"] = "could not read HEAD commit"
                dependencies.append(dep_entry)
                continue

            head_commit = head_result.stdout.strip()

            # Find build tag via ls-remote
            tag_result = git(["ls-remote", "--tags", "origin"], cwd=str(upstream_path), check=False)
            build_tag = None
            if tag_result.returncode == 0:
                for line in tag_result.stdout.strip().split("\n"):
                    if not line.strip():
                        continue
                    parts = line.split()
                    if len(parts) < 2:
                        continue
                    tag_commit = parts[0]
                    ref = parts[1]
                    if "refs/tags/build-" not in ref:
                        continue
                    tag_name = ref.replace("refs/tags/", "").rstrip("^{}")
                    is_deref = ref.endswith("^{}")
                    # For annotated tags, prefer dereferenced commit
                    if tag_commit == head_commit or (not is_deref and tag_commit.startswith(head_commit[:7])):
                        build_tag = tag_name
                    elif is_deref and tag_commit == head_commit:
                        build_tag = tag_name

            if build_tag:
                base_version = build_tag.replace("build-", "")
                needs_dev = branch.lower() not in stable_branches
                resolved_version = f"{base_version}{dev_suffix}" if needs_dev else base_version
                dep_entry["build_tag"] = build_tag
                dep_entry["resolved_version"] = resolved_version
            else:
                dep_entry["build_tag"] = None
                dep_entry["resolved_version"] = None
                dep_entry["warning"] = f"no build tag found for commit {head_commit[:8]}; version TBD at implementation time"
                print(f"warning: no build tag found for {upstream} at {head_commit[:8]}", file=sys.stderr)

            dependencies.append(dep_entry)

    # Write NuGet context file for Phase 3 injection
    if dependencies:
        nuget_ctx_path = repo_root / ".claude" / "tmp" / "nuget-deps-context.md"
        nuget_ctx_path.parent.mkdir(parents=True, exist_ok=True)
        lines = ["### NuGet Package Dependencies\n"]
        for dep in dependencies:
            tag = dep.get("build_tag") or "N/A"
            ver = dep.get("resolved_version") or "TBD — resolve at implementation time via `nuget-resolver` skill"
            lines.append(f"**Source:** {dep['upstream_repo']} ({tag})")
            lines.append(f"**Resolved Version:** {ver}")
            lines.append(f"**Branch:** {branch}\n")
            lines.append("Update the following PackageReference versions in .csproj or Directory.Packages.props:")
            for pkg in dep.get("packages", []):
                lines.append(f"- {pkg} → {ver}")
            lines.append("")
        lines.append("If build fails due to missing package, wait 2 minutes and retry (CI may still be publishing).\n")
        nuget_ctx_path.write_text("\n".join(lines))

    emit_json({
        "has_nuget_deps": len(dependencies) > 0,
        "dependencies": dependencies,
    })
    return 0


# ---------------------------------------------------------------------------
# commit-superrepo (Phase 4)
# ---------------------------------------------------------------------------

def cmd_commit_superrepo(args: argparse.Namespace) -> int:
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key
    title = args.title
    cwd = str(repo_root)

    commit_msg = f"{story_key}: {title} - story preparation complete"

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

    # Resolve target status from config if --skill/--outcome provided
    if not target_status and args.skill and args.outcome:
        config_path = Path(__file__).parent.parent.parent / "_common" / "workflow-transitions.yaml"
        if config_path.exists():
            with config_path.open("r", encoding="utf-8") as fh:
                config = yaml.safe_load(fh) or {}
            skill_map = config.get("transitions", {}).get(args.skill, {})
            target_status = skill_map.get(args.outcome)
        if not target_status:
            print(f"error: no transition for skill={args.skill} outcome={args.outcome}", file=sys.stderr)
            emit_json({"action": "error", "reason": f"unknown transition: {args.skill}/{args.outcome}"})
            return 0  # Non-fatal
    elif not target_status:
        print("error: either --target-status or --skill/--outcome required", file=sys.stderr)
        emit_json({"action": "error", "reason": "missing target-status or skill/outcome"})
        return 0  # Non-fatal

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
# attach-story (Phase 5.5)
# ---------------------------------------------------------------------------

def cmd_attach_story(args: argparse.Namespace) -> int:
    """Phase 5.5: Attach story file to story (best-effort)."""
    story_key = args.story_key
    story_file = Path(args.story_file)
    repo_root = Path(args.repo_root).resolve()

    if not story_file.exists():
        print(f"warning: story file not found at {story_file}, skipping attachment", file=sys.stderr)
        emit_json({
            "action": "skipped",
            "reason": "story file not found",
            "story_key": story_key,
        })
        return 0

    jira_script = repo_root / ".claude" / "skills" / "jira-agile" / "scripts" / "jira_agile.py"

    if not jira_script.exists():
        print(f"warning: jira_agile.py not found at {jira_script}, skipping attachment", file=sys.stderr)
        emit_json({
            "action": "skipped",
            "reason": "jira_agile.py not found",
            "story_key": story_key,
        })
        return 0

    cmd = [
        sys.executable, str(jira_script),
        "attach-file", story_key, str(story_file),
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
                "story_key": story_key,
            })
            return 0  # Non-fatal

        emit_json({
            "action": "attached",
            "story_key": story_key,
            "file": str(story_file),
        })

    except subprocess.TimeoutExpired:
        print("warning: Jira attachment timed out", file=sys.stderr)
        emit_json({
            "action": "warning",
            "reason": "attachment timed out",
            "story_key": story_key,
        })
    except Exception as exc:
        print(f"warning: Jira attachment error: {exc}", file=sys.stderr)
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
    story_key = args.story_key
    story_file = Path(args.story_file)

    if not story_file.exists():
        result = json.dumps({"status": "1", "story_key": story_key})
        print(f"{SENTINEL}{result}{SENTINEL}")
        return 0

    content = story_file.read_text(encoding="utf-8")
    has_ready_status = bool(READY_FOR_DEV_RE.search(content))

    status = "0" if has_ready_status else "1"
    result = json.dumps({"status": status, "story_key": story_key})
    print(f"{SENTINEL}{result}{SENTINEL}")
    return 0


# ---------------------------------------------------------------------------
# main — argparse dispatcher
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic automation for zone-prepare-story skill phases 1, 2, 2.7, 4, 5, 5.5, 6."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # sync-superrepo
    p_sync = subparsers.add_parser("sync-superrepo", help="Phase 0: Pull latest super-repo branch")
    p_sync.add_argument("--repo-root", default=".", help="Repository root directory")

    # resolve
    p_resolve = subparsers.add_parser("resolve", help="Phase 1: Resolve story key to story metadata")
    p_resolve.add_argument("--story-key", required=True, help="story key (e.g. CLSDLC-25)")
    p_resolve.add_argument("--repo-root", default=".", help="Repository root directory")

    # resolve-domain-skills
    p_domain = subparsers.add_parser("resolve-domain-skills", help="Phase 2: Resolve domain skills from epics")
    p_domain.add_argument("--bmad-id", required=True, help="BMAD story ID (e.g. 2.1)")
    p_domain.add_argument("--repo-root", default=".", help="Repository root directory")

    # checkout-modules
    p_checkout = subparsers.add_parser("checkout-modules", help="Phase 2.7: Checkout research branches in modules")
    p_checkout.add_argument("--modules", required=True, help="JSON array of module names")
    p_checkout.add_argument("--epic-branch", default=None, help="Epic branch to prefer over initiative")
    p_checkout.add_argument("--initiative-branch", default=None, help="Initiative branch to prefer")
    p_checkout.add_argument("--repo-root", default=".", help="Repository root directory")

    # resolve-nuget-deps
    p_nuget = subparsers.add_parser("resolve-nuget-deps", help="Phase 2.8: Resolve cross-repo NuGet dependencies")
    p_nuget.add_argument("--modules", required=True, help="JSON array of module paths (e.g. modules/zone.zonepay)")
    p_nuget.add_argument("--branch", default="", help="Current epic/feature branch name")
    p_nuget.add_argument("--initiative-branch", default="", help="Initiative/parent branch name (fallback)")
    p_nuget.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-superrepo
    p_commit = subparsers.add_parser("commit-superrepo", help="Phase 4: Commit and push super-repo")
    p_commit.add_argument("--story-key", required=True, help="Story key identifier")
    p_commit.add_argument("--story-key", required=True, help="story key")
    p_commit.add_argument("--title", required=True, help="BMAD story title for commit message")
    p_commit.add_argument("--repo-root", default=".", help="Repository root directory")

    # transition-jira
    p_jira = subparsers.add_parser("transition-jira", help="Phase 5: Transition story (best-effort)")
    p_jira.add_argument("--story-key", required=True, help="story key")
    p_jira.add_argument("--target-status", default=None, help="Target Jira status (direct override)")
    p_jira.add_argument("--skill", default=None, help="Skill name for config lookup (e.g. 'zone-dev')")
    p_jira.add_argument("--outcome", default=None, help="Outcome name for config lookup (e.g. 'success')")
    group = p_jira.add_mutually_exclusive_group()
    group.add_argument("--comment", default=None, help="Optional transition comment")
    group.add_argument("--comment-file", default=None, help="Read transition comment from a file")
    group.add_argument("--comment-stdin", action="store_true", help="Read transition comment from stdin")
    p_jira.add_argument("--comment-format", default="plain", choices=["plain", "markdown"],
                        help="Format of the transition comment content")
    p_jira.add_argument("--repo-root", default=".", help="Repository root directory")

    # attach-story
    p_attach = subparsers.add_parser("attach-story", help="Phase 5.5: Attach story file to story")
    p_attach.add_argument("--story-key", required=True, help="story key")
    p_attach.add_argument("--story-file", required=True, help="Path to story markdown file")
    p_attach.add_argument("--repo-root", default=".", help="Repository root directory")

    # status
    p_status = subparsers.add_parser("status", help="Phase 6: Output status sentinel")
    p_status.add_argument("--story-key", required=True, help="Story key identifier")
    p_status.add_argument("--story-file", required=True, help="Path to story markdown file")
    p_status.add_argument("--repo-root", default=".", help="Repository root directory")

    parsed = parser.parse_args()

    dispatch = {
        "sync-superrepo": cmd_sync_superrepo,
        "resolve": cmd_resolve,
        "resolve-domain-skills": cmd_resolve_domain_skills,
        "checkout-modules": cmd_checkout_modules,
        "resolve-nuget-deps": cmd_resolve_nuget_deps,
        "commit-superrepo": cmd_commit_superrepo,
        "transition-jira": cmd_transition_jira,
        "attach-story": cmd_attach_story,
        "status": cmd_status,
    }

    handler = dispatch.get(parsed.command)
    if handler is None:
        die(f"Unknown command: {parsed.command}")

    return handler(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
