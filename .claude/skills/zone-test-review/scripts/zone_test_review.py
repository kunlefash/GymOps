#!/usr/bin/env python3
"""Deterministic automation for zone-test-review skill phases 4, 4.5, and 5."""

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
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any, Dict, List, Optional

import yaml

# ---------------------------------------------------------------------------
# Utilities
# ---------------------------------------------------------------------------

SENTINEL = "###ZONE-TEST-REVIEW-RESULT###"
PREWARM_MAX_WORKERS = int(os.environ.get("PREWARM_WORKERS", "4"))
SKILL_MAP_FILENAME = "module-skill-map.yaml"

# Matches "**Recommendation**: Approve" etc. in TEA test-review report
RECOMMENDATION_RE = re.compile(
    r"\*\*Recommendation\*\*\s*:\s*(.+)",
    re.IGNORECASE,
)

# Matches "**Quality Score**: 85/100 (Grade: B)" or similar
QUALITY_SCORE_RE = re.compile(
    r"\*\*Quality Score\*\*\s*:\s*(\d+)\s*/\s*100(?:\s*\(Grade:\s*([A-F][+-]?)\))?",
    re.IGNORECASE,
)

# Matches "**Test Review Recommendation:** Approve" in story file section
STORY_RECOMMENDATION_RE = re.compile(
    r"\*\*Test Review Recommendation:\*\*\s*(.+)",
    re.IGNORECASE,
)

# Matches "**Quality Score:** 85/100 (Grade: B)" in story file section
STORY_QUALITY_SCORE_RE = re.compile(
    r"\*\*Quality Score:\*\*\s*(\d+)\s*/\s*100\s*\(Grade:\s*([A-F][+-]?)\)",
    re.IGNORECASE,
)

PASS_RECOMMENDATIONS = {"approve", "approve with comments"}

REMOTE_URL_RE = re.compile(r"git@github\.org:([^/]+)/(.+?)(?:\.git)?$")


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
    """Print error to stderr and exit."""
    print(f"error: {message}", file=sys.stderr)
    sys.exit(code)


def git(args: List[str], cwd: Optional[str] = None, check: bool = True) -> subprocess.CompletedProcess:
    """Run a git command, capturing output."""
    return subprocess.run(
        ["git"] + args,
        cwd=cwd,
        capture_output=True,
        text=True,
        check=check,
    )


def _current_branch(cwd: str) -> str:
    return git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).stdout.strip()


def git_push_with_retry(push_args: List[str], cwd: str, max_retries: int = 5) -> subprocess.CompletedProcess:
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


# ---------------------------------------------------------------------------
# resolve_domain_skills
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
            result.append({"skill": skill, "path": str(skill_path), "exists": skill_path.exists()})
    return result


# ---------------------------------------------------------------------------
# prewarm (Phases 0-2.5)
# ---------------------------------------------------------------------------

MODULE_REF_RE = re.compile(r"modules/([\w.]+)")


def _prepare_one_module(name, repo_root, story_branch, target_branches=None):
    """Prepare a single module for test review (checkout-only, with deep fetch for diff context)."""
    sub_path = repo_root / "modules" / name
    entry = {"path": f"modules/{name}", "status": "ok", "created": False}
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
        # Deepen for diff context (test review needs history)
        git(["fetch", "origin", "--deepen", "50"], cwd=sub_dir, check=False)
    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"fetch failed: {exc.stderr.strip()}"
        return entry
    try:
        ls_result = git(["ls-remote", "--heads", "origin", story_branch], cwd=sub_dir)
        remote_exists = bool(ls_result.stdout.strip())
        if remote_exists:
            git(["checkout", story_branch], cwd=sub_dir)
            git(["pull", "origin", story_branch], cwd=sub_dir)
            entry["status"] = "checked_out_remote"
        else:
            local_check = git(["rev-parse", "--verify", story_branch], cwd=sub_dir, check=False)
            if local_check.returncode == 0:
                git(["checkout", story_branch], cwd=sub_dir)
                entry["status"] = "checked_out_local"
            else:
                entry["status"] = "skipped"
                entry["reason"] = "branch not found (checkout-only)"
    except subprocess.CalledProcessError as exc:
        entry["status"] = "error"
        entry["error"] = f"branch checkout failed: {exc.stderr.strip()}"
    return entry


def cmd_prewarm(args):
    """Run Phases 0-2.5 deterministically for test-review and write context files."""
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key
    cwd = str(repo_root)

    context = {
        "prewarm_version": "1.0",
        "prewarm_status": "success",
        "blocker_summary": "",
        "resolve": {},
        "prepare_branches": {},
        "domain_skills_loaded": [],
    }

    def _write_and_exit(status, blocker, code):
        context["prewarm_status"] = status
        context["blocker_summary"] = blocker
        (repo_root / ".gymops-prewarm-context.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
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

    # Phase 1: resolve (same as zone_review.py resolve logic)
    try:
        map_path = repo_root / "_bmad-output" / "implementation-artifacts" / "story-key-map.yaml"
        data = read_yaml(map_path)
        active_project_key = data.get("active_project_key")
        if not active_project_key:
            return _write_and_exit("blocked", "KEY_NOT_FOUND: active_project_key not found", 1)
        items = data.get("projects", {}).get(active_project_key, {}).get("items", [])
        bmad_id = bmad_title = None
        for item in items:
            if item.get("story_key") == story_key and item.get("bmad_type") == "story":
                bmad_id = str(item["bmad_id"])
                bmad_title = str(item["bmad_title"])
                break
        if bmad_id is None:
            return _write_and_exit("blocked", f"KEY_NOT_FOUND: '{story_key}' not found", 1)

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
        story_branch = f"agent/story/{story_key}-{story_key}"
        story_file_path = repo_root / "_bmad-output" / "implementation-artifacts" / "stories" / f"{story_key}.md"

        if not story_file_path.exists():
            return _write_and_exit("blocked", f"STORY_FILE_MISSING: {story_file_path}", 1)

        resolve_data = {
            "bmad_id": bmad_id, "bmad_title": bmad_title, "story_key": story_key,
            "story_branch": story_branch, "story_file_path": str(story_file_path),
            "story_key": story_key,
        }
        if epic_branch:
            resolve_data["epic_key"] = epic_key
            resolve_data["epic_branch"] = epic_branch
            resolve_data["parent_story_key"] = parent_story_key
        context["resolve"] = resolve_data
    except SystemExit:
        return _write_and_exit("blocked", "RESOLVE_FAILED: SystemExit", 1)
    except Exception as exc:
        return _write_and_exit("blocked", f"RESOLVE_FAILED: {exc}", 1)

    # Phase 2: prepare-branches (checkout-only with deep fetch)
    try:
        content = story_file_path.read_text(encoding="utf-8")
        matches = MODULE_REF_RE.findall(content)
        seen = set()
        module_names = []
        for m in matches:
            if m not in seen:
                seen.add(m)
                module_names.append(m)

        valid_names = [n for n in module_names if (repo_root / "modules" / n).is_dir()]
        results = []
        with ThreadPoolExecutor(max_workers=PREWARM_MAX_WORKERS) as pool:
            futures = {
                pool.submit(_prepare_one_module, name, repo_root, story_branch, [story_branch]): name
                for name in valid_names
            }
            for future in as_completed(futures):
                results.append(future.result())

        prepared_names = [Path(r["path"]).name for r in results if r["status"] not in ("error", "skipped")]
        domain_skills = resolve_domain_skills(prepared_names, repo_root)
        has_errors = any(r["status"] == "error" for r in results)

        if not prepared_names:
            context["prepare_branches"] = {"modules": results, "count": 0, "domain_skills": domain_skills}
            return _write_and_exit("blocked", "PREPARE_FAILED: no modules prepared", 1)

        context["prepare_branches"] = {
            "modules": results, "count": len(prepared_names), "domain_skills": domain_skills,
        }
        if has_errors:
            context["prewarm_status"] = "partial"
    except Exception as exc:
        return _write_and_exit("blocked", f"PREPARE_FAILED: {exc}", 1)

    # Phase 2.5: read domain skill files
    skills_parts = []
    loaded_skills = []
    for ds in domain_skills:
        if ds.get("exists"):
            try:
                skill_text = Path(ds["path"]).read_text(encoding="utf-8")
                skills_parts.append(f"--- SKILL: {ds['skill']} ---\n{skill_text}\n--- END SKILL: {ds['skill']} ---")
                loaded_skills.append(ds["skill"])
            except Exception:
                pass
    context["domain_skills_loaded"] = loaded_skills

    (repo_root / ".gymops-prewarm-context.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
    (repo_root / ".gymops-prewarm-skills.md").write_text("\n\n".join(skills_parts), encoding="utf-8")

    emit_json(context)
    return 0 if context["prewarm_status"] == "success" else 2


# ---------------------------------------------------------------------------
# commit-superrepo (Phase 4)
# ---------------------------------------------------------------------------

def cmd_commit_superrepo(args: argparse.Namespace) -> int:
    """Phase 4: Commit and push super-repo with test review report commit message."""
    repo_root = Path(args.repo_root).resolve()
    story_key = args.story_key
    title = args.title
    cwd = str(repo_root)

    commit_msg = f"{story_key}: {title} - test review report"

    git(["add", "_bmad-output/"], cwd=cwd, check=False)
    git(["reset", "HEAD", "modules/"], cwd=cwd, check=False)

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
        commit_hash = git(["rev-parse", "HEAD"], cwd=cwd).stdout.strip()
        branch = git(["rev-parse", "--abbrev-ref", "HEAD"], cwd=cwd).stdout.strip()

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

def _parse_bb_remote(sub_dir: str) -> Optional[tuple]:
    """Extract (workspace, repo_slug) from the module's origin remote URL."""
    result = git(["remote", "get-url", "origin"], cwd=sub_dir, check=False)
    if result.returncode != 0:
        return None
    m = REMOTE_URL_RE.match(result.stdout.strip())
    if not m:
        return None
    return m.group(1), m.group(2)


def _resolve_bb_auth() -> Optional[str]:
    """Resolve GitHub auth header. Prefers API token; falls back to app password."""
    bb_email = os.environ.get("BB_EMAIL", "")
    bb_token = os.environ.get("BB_API_TOKEN", "")
    if bb_email and bb_token:
        return "Basic " + b64encode(f"{bb_email}:{bb_token}".encode()).decode()

    bb_user = os.environ.get("BB_USERNAME", "")
    bb_pass = os.environ.get("BB_APP_PASSWORD", "")
    if bb_user and bb_pass:
        print("warning: using legacy BB_USERNAME/BB_APP_PASSWORD; migrate to BB_EMAIL/BB_API_TOKEN before June 2026", file=sys.stderr)
        return "Basic " + b64encode(f"{bb_user}:{bb_pass}".encode()).decode()

    return None


def _build_pr_description(
    story_file: Optional[str],
    story_key: str,
    story_branch: str,
    epic_branch: str,
) -> str:
    """Build PR description from the full story file content (truncated to 64 KB).

    Unlike zone-code-review, the entire story file is used as the PR body
    rather than extracting specific sections.
    """
    BB_DESC_LIMIT = 64 * 1024  # 64 KB
    fallback = f"{story_key}: `{story_branch}` → `{epic_branch}`"

    if not story_file:
        return fallback

    story_path = Path(story_file)
    if not story_path.exists():
        return fallback

    try:
        content = story_path.read_text(encoding="utf-8")
    except Exception:
        return fallback

    if not content.strip():
        return fallback

    if len(content.encode("utf-8")) > BB_DESC_LIMIT:
        while len(content.encode("utf-8")) > BB_DESC_LIMIT - 20:
            content = content[: len(content) - 200]
        content = content.rstrip() + "\n\n…*(truncated)*"

    return content


def _bb_create_pr(
    workspace: str,
    repo_slug: str,
    title: str,
    source_branch: str,
    dest_branch: str,
    auth_header: str,
    description: str = "",
) -> Dict[str, Any]:
    """Create a GitHub PR via REST API. Returns dict with status info."""
    url = f"https://api.github.org/2.0/repositories/{workspace}/{repo_slug}/pullrequests"
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
    """Phase 4.5: Create GitHub PRs from story_branch → epic_branch.

    PR description = full story file content (not extracted sections).
    When epic_branch is empty (bug fixes with no parent epic), the target
    branch is resolved per-module from .gitmodules (default: 'development').
    """
    repo_root = Path(args.repo_root).resolve()
    story_branch = args.story_branch
    epic_branch = args.epic_branch
    story_key = args.story_key
    title = args.title
    use_default = not epic_branch

    auth_header = _resolve_bb_auth()

    if auth_header is None:
        print("warning: GitHub credentials not configured (set BB_EMAIL + BB_API_TOKEN, or legacy BB_USERNAME + BB_APP_PASSWORD); skipping PR creation", file=sys.stderr)
        try:
            modules = json.loads(args.modules)
        except (json.JSONDecodeError, TypeError):
            modules = []
        results = [
            {"module": s.get("path", "unknown"), "status": "skipped", "reason": "missing BB credentials"}
            for s in modules
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

    pr_title = f"{story_key}: {title}"
    story_file = getattr(args, "story_file", None)

    try:
        modules = json.loads(args.modules)
    except (json.JSONDecodeError, TypeError):
        die("--modules must be a valid JSON array")

    qualifying = [
        s for s in modules
        if s.get("status") in ("checked_out_remote", "checked_out_local")
    ]

    # Build PR description once; use first module's resolved target for fallback text
    if use_default and qualifying:
        first_sub_name = qualifying[0].get("path", "").split("/")[-1] if "/" in qualifying[0].get("path", "") else qualifying[0].get("path", "")
        desc_target = get_default_branch(first_sub_name, repo_root)
    else:
        desc_target = epic_branch
    pr_description = _build_pr_description(story_file, story_key, story_branch, desc_target)

    results = []
    created = 0
    errors = 0
    skipped = 0

    for sub in qualifying:
        sub_path = sub.get("path", "")
        sub_dir = str(repo_root / sub_path)
        entry: Dict[str, Any] = {"module": sub_path}

        # Resolve target branch per-module when no epic branch
        if use_default:
            sub_name = sub_path.split("/")[-1] if "/" in sub_path else sub_path
            target_branch = get_default_branch(sub_name, repo_root)
        else:
            target_branch = epic_branch

        remote_info = _parse_bb_remote(sub_dir)
        if not remote_info:
            entry["status"] = "skipped"
            entry["reason"] = "could not parse GitHub remote URL"
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
            created += 1
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
# status (Phase 5)
# ---------------------------------------------------------------------------

def cmd_status(args: argparse.Namespace) -> int:
    """Phase 5: Output status sentinel.

    Reads story file, finds ### Test Quality Review (AI) section,
    parses **Test Review Recommendation:** and **Quality Score:**,
    emits sentinel JSON.

    status="0" (PASS) = recommendation is Approve or Approve with Comments;
    status="1" (FAIL) = otherwise or section missing.
    """
    story_file_arg = getattr(args, "story_file", None)
    if story_file_arg:
        story_file = Path(story_file_arg)
    else:
        story_file = _resolve_story_file(args.story_key, Path(args.repo_root).resolve())

    if not story_file.exists():
        die(f"Story file not found: {story_file}")

    content = story_file.read_text(encoding="utf-8")

    # Find the ### Test Quality Review (AI) section
    section_match = re.search(
        r"^###\s+Test Quality Review \(AI\)\s*$",
        content,
        re.MULTILINE | re.IGNORECASE,
    )

    recommendation = "unknown"
    score = 0
    grade = "-"

    if section_match:
        section_start = section_match.end()
        # Find the end of this section (next ### heading or EOF)
        next_section = re.search(r"^###\s+", content[section_start:], re.MULTILINE)
        section_text = content[section_start: section_start + next_section.start()] if next_section else content[section_start:]

        rec_match = STORY_RECOMMENDATION_RE.search(section_text)
        if rec_match:
            recommendation = rec_match.group(1).strip()

        score_match = STORY_QUALITY_SCORE_RE.search(section_text)
        if score_match:
            score = int(score_match.group(1))
            grade = score_match.group(2) or "-"

    is_pass = recommendation.lower() in PASS_RECOMMENDATIONS
    status = "0" if is_pass else "1"

    result = json.dumps({
        "status": status,
        "score": score,
        "grade": grade,
        "recommendation": recommendation,
    })
    print(f"{SENTINEL}{result}{SENTINEL}")
    return 0


# ---------------------------------------------------------------------------
# main — argparse dispatcher
# ---------------------------------------------------------------------------

def main() -> int:
    parser = argparse.ArgumentParser(
        description="Deterministic automation for zone-test-review skill phases 4, 4.5, 5."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # prewarm
    p_prewarm = subparsers.add_parser("prewarm", help="Phases 0-2.5: Sync, resolve, prepare, load skills")
    p_prewarm.add_argument("--story-key", required=True, help="story key")
    p_prewarm.add_argument("--repo-root", default=".", help="Repository root directory")

    # commit-superrepo
    p_commit = subparsers.add_parser("commit-superrepo", help="Phase 4: Commit and push super-repo")
    p_commit.add_argument("--story-key", required=True, help="Story key identifier")
    p_commit.add_argument("--story-key", required=True, help="story key")
    p_commit.add_argument("--title", required=True, help="BMAD story title for commit message")
    p_commit.add_argument("--repo-root", default=".", help="Repository root directory")

    # create-pullrequests
    p_pr = subparsers.add_parser("create-pullrequests", help="Phase 4.5: Create GitHub PRs")
    p_pr.add_argument("--story-branch", required=True, help="Source branch for PRs")
    p_pr.add_argument("--epic-branch", default="", help="Destination branch for PRs (empty = module default)")
    p_pr.add_argument("--story-key", required=True, help="story key for PR title")
    p_pr.add_argument("--title", required=True, help="BMAD title for PR title")
    p_pr.add_argument("--modules", required=True, help="JSON string of module result objects")
    p_pr.add_argument("--story-file", default=None, help="Path to story markdown file (used as PR description)")
    p_pr.add_argument("--repo-root", default=".", help="Repository root directory")

    # status
    p_status = subparsers.add_parser("status", help="Phase 5: Output status sentinel")
    p_status.add_argument("--story-file", default=None, help="Path to story markdown file")
    p_status.add_argument("--story-key", default=None, help="story key (fallback resolution when --story-file omitted)")
    p_status.add_argument("--repo-root", default=".", help="Repository root directory")

    parsed = parser.parse_args()

    dispatch = {
        "prewarm": cmd_prewarm,
        "commit-superrepo": cmd_commit_superrepo,
        "create-pullrequests": cmd_create_pullrequests,
        "status": cmd_status,
    }

    handler = dispatch.get(parsed.command)
    if handler is None:
        die(f"Unknown command: {parsed.command}")

    return handler(parsed)


if __name__ == "__main__":
    raise SystemExit(main())
