#!/usr/bin/env python3
"""Deterministic sprint planner for Zone Agentic SDLC (plan-only)."""

from __future__ import annotations

import argparse
import datetime as dt
import importlib.util
import json
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml

STORY_KEY_RE = re.compile(r"^(\d+)-(\d+)-")
EPIC_HEADING_RE = re.compile(r"^##\s+Epic\s+(\d+):\s*(.+?)\s*$")
STORY_HEADING_RE = re.compile(r"^###\s+Story\s+(\d+)\.(\d+):\s*(.+?)\s*$")

COMPLEXITY_KEYWORDS = {
    "blockchain",
    "besu",
    "settlement",
    "nibss",
    "webhook",
    "kafka",
    "rabbitmq",
    "integration",
    "async",
    "security",
    "rbac",
    "audit",
    "compliance",
}

UNCERTAINTY_KEYWORDS = {
    "where applicable",
    "as specified",
    "optional",
    "policy",
    "configured",
    "periodic",
    "retry",
    "fallback",
    "support",
}

RISK_KEYWORDS = {
    "payment",
    "settlement",
    "refund",
    "dispute",
    "blockchain",
    "nibss",
    "security",
    "compliance",
    "audit",
}

JIRA_REQUIRED_CREDENTIALS = ("ATLASSIAN_EMAIL", "ATLASSIAN_API_TOKEN", "ATLASSIAN_CLOUD_ID")


class SprintPlanningError(RuntimeError):
    """Raised when planning cannot continue."""


@dataclass
class StoryEntry:
    epic_num: int
    story_num: int
    bmad_id: str
    story_key: str
    title: str
    status: str
    body: str
    dependencies: List[str] = field(default_factory=list)
    blocked_by: List[str] = field(default_factory=list)
    points: Optional[int] = None
    estimate_rationale: List[str] = field(default_factory=list)
    selectable: bool = False
    jira_key: Optional[str] = None

    @property
    def sort_key(self) -> Tuple[int, int]:
        return (self.epic_num, self.story_num)


@dataclass
class EpicOption:
    k: int
    points: int
    completed_epic: int
    stories: List[str]


def resolve_path(template: str, repo_root: Path) -> Path:
    return Path(template.replace("{project-root}", str(repo_root))).resolve()


def read_yaml(path: Path) -> Dict[str, Any]:
    if not path.exists():
        return {}
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_precomputed_estimates(path: Path) -> Optional[Dict[str, Dict[str, Any]]]:
    """Load story estimates from YAML/JSON file produced by estimation subagent."""
    if not path.exists():
        return None
    if path.suffix in (".yaml", ".yml"):
        raw = read_yaml(path)
    else:
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return None
    if not isinstance(raw, dict):
        return None
    return {str(k): v if isinstance(v, dict) else {} for k, v in raw.items()}


def read_text(path: Path) -> str:
    if not path.exists():
        raise SprintPlanningError(f"Required file not found: {path}")
    return path.read_text(encoding="utf-8")


def latest_file(pattern: str, base: Path) -> Optional[Path]:
    matches = sorted(base.glob(pattern), key=lambda p: p.stat().st_mtime, reverse=True)
    return matches[0] if matches else None


def load_skill_config(repo_root: Path) -> Dict[str, Any]:
    config_path = repo_root / ".claude/skills/zone-sprint/config.yaml"
    config = read_yaml(config_path)
    if not config:
        raise SprintPlanningError(f"Skill config missing or empty: {config_path}")
    return config


def load_phase4_config(config: Dict[str, Any], repo_root: Path) -> Dict[str, str]:
    execution = dict(config.get("execution", {}))
    phase4_mode = str(execution.get("phase4_mode", "markdown-workflow")).strip() or "markdown-workflow"
    workflow_template = str(
        execution.get(
            "story_creator_workflow",
            "{project-root}/.claude/skills/zone-sprint/references/story-creator.md",
        )
    )
    workflow_path = resolve_path(workflow_template, repo_root)
    return {
        "phase4_mode": phase4_mode,
        "story_creator_workflow": str(workflow_path),
    }


def load_bmad_paths(repo_root: Path) -> Dict[str, Path]:
    bmad_config_path = repo_root / "_bmad/bmm/config.yaml"
    bmad_config = read_yaml(bmad_config_path)
    planning = bmad_config.get("planning_artifacts", "{project-root}/_bmad-output/planning-artifacts")
    implementation = bmad_config.get(
        "implementation_artifacts", "{project-root}/_bmad-output/implementation-artifacts"
    )
    return {
        "planning_artifacts": resolve_path(planning, repo_root),
        "implementation_artifacts": resolve_path(implementation, repo_root),
    }


def parse_epics_markdown(epics_content: str) -> Tuple[Dict[str, Dict[str, Any]], Dict[int, str]]:
    stories: Dict[str, Dict[str, Any]] = {}
    epic_titles: Dict[int, str] = {}

    current_epic_num: Optional[int] = None
    current_story: Optional[Dict[str, Any]] = None
    body_lines: List[str] = []

    def flush_story() -> None:
        nonlocal current_story, body_lines
        if not current_story:
            return
        current_story["body"] = "\n".join(body_lines).strip()
        stories[current_story["bmad_id"]] = current_story
        current_story = None
        body_lines = []

    for raw_line in epics_content.splitlines():
        epic_match = EPIC_HEADING_RE.match(raw_line.strip())
        if epic_match:
            flush_story()
            current_epic_num = int(epic_match.group(1))
            epic_titles[current_epic_num] = epic_match.group(2).strip()
            continue

        story_match = STORY_HEADING_RE.match(raw_line.strip())
        if story_match:
            flush_story()
            epic_num = int(story_match.group(1))
            story_num = int(story_match.group(2))
            if current_epic_num is None:
                current_epic_num = epic_num
            bmad_id = f"{epic_num}.{story_num}"
            current_story = {
                "bmad_id": bmad_id,
                "epic_num": epic_num,
                "story_num": story_num,
                "title": story_match.group(3).strip(),
                "body": "",
            }
            continue

        if current_story is not None:
            body_lines.append(raw_line)

    flush_story()
    return stories, epic_titles


def slug_to_title(story_key: str) -> str:
    parts = story_key.split("-")[2:]
    if not parts:
        return story_key
    return " ".join(word.capitalize() for word in parts)


def build_story_entries(
    development_status: Dict[str, str],
    stories_meta: Dict[str, Dict[str, Any]],
) -> List[StoryEntry]:
    entries: List[StoryEntry] = []
    for key, status in development_status.items():
        match = STORY_KEY_RE.match(str(key))
        if not match:
            continue
        epic_num = int(match.group(1))
        story_num = int(match.group(2))
        bmad_id = f"{epic_num}.{story_num}"
        meta = stories_meta.get(bmad_id, {})
        entries.append(
            StoryEntry(
                epic_num=epic_num,
                story_num=story_num,
                bmad_id=bmad_id,
                story_key=str(key),
                title=str(meta.get("title") or slug_to_title(str(key))),
                status=str(status),
                body=str(meta.get("body") or ""),
            )
        )
    entries.sort(key=lambda item: item.sort_key)
    return entries


def attach_dependencies(entries: List[StoryEntry]) -> None:
    by_epic_story = {(item.epic_num, item.story_num): item for item in entries}
    for item in entries:
        if item.story_num <= 1:
            continue
        previous = by_epic_story.get((item.epic_num, item.story_num - 1))
        if previous:
            item.dependencies = [previous.bmad_id]


def effort_to_story_points(
    effort_score: int,
    estimated_person_days: Optional[float] = None,
    minimum: int = 1,
    maximum: int = 13,
) -> int:
    """Map zone-estimator output to Fibonacci story points (1, 2, 3, 5, 8, 13)."""
    EFFORT_TO_DAYS = {
        1: 0.1,
        2: 0.5,
        3: 1,
        4: 2.5,
        5: 4.5,
        6: 10,
        7: 17,
        8: 24,
        9: 45,
        10: 60,
    }
    days = (
        estimated_person_days
        if estimated_person_days is not None
        else EFFORT_TO_DAYS.get(effort_score, 1)
    )
    if days <= 0.25:
        points = 1
    elif days <= 1:
        points = 2
    elif days <= 2:
        points = 3
    elif days <= 4:
        points = 5
    elif days <= 7:
        points = 8
    else:
        points = 13
    return max(minimum, min(maximum, points))


def estimate_points(body: str, title: str, minimum: int, maximum: int) -> Tuple[int, List[str]]:
    score = 1
    rationale: List[str] = ["base=1"]

    ac_count = body.count("**Given**")
    if ac_count >= 2:
        score += 1
        rationale.append("acceptance_criteria>=2:+1")

    word_count = len(body.split())
    if word_count >= 120:
        score += 1
        rationale.append("body_words>=120:+1")

    lowered = f"{title}\n{body}".lower()
    hits = sum(1 for keyword in COMPLEXITY_KEYWORDS if keyword in lowered)
    if hits >= 2:
        score += 2
        rationale.append("complexity_keywords>=2:+2")
    elif hits == 1:
        score += 1
        rationale.append("complexity_keywords=1:+1")

    uncertainty_hits = sum(1 for keyword in UNCERTAINTY_KEYWORDS if keyword in lowered)
    if uncertainty_hits >= 2:
        score += 1
        rationale.append("uncertainty_keywords>=2:+1")

    risk_hits = sum(1 for keyword in RISK_KEYWORDS if keyword in lowered)
    if risk_hits >= 2:
        score += 1
        rationale.append("risk_keywords>=2:+1")

    if score <= 1:
        points = 1
        effort_band = "trivial"
    elif score == 2:
        points = 2
        effort_band = "small"
    elif score == 3:
        points = 3
        effort_band = "medium"
    elif score <= 5:
        points = 5
        effort_band = "large"
    elif score <= 7:
        points = 8
        effort_band = "very-large"
    else:
        points = 13
        effort_band = "epic-sized"

    clamped = max(minimum, min(maximum, points))
    if clamped != points:
        rationale.append(f"clamped:{points}->{clamped}")
    if clamped >= 8:
        rationale.append("split_recommended=true")

    rationale.append(f"effort_band={effort_band}")
    rationale.append(f"final={clamped}")
    return clamped, rationale


def attach_blockers_and_estimates(
    entries: List[StoryEntry],
    minimum: int,
    maximum: int,
    precomputed_estimates: Optional[Dict[str, Dict[str, Any]]] = None,
) -> None:
    by_bmad = {item.bmad_id: item for item in entries}
    for item in entries:
        if item.dependencies:
            dependency = by_bmad.get(item.dependencies[0])
            if dependency and dependency.status != "done":
                item.blocked_by = [dependency.bmad_id]
        if item.status == "backlog":
            if precomputed_estimates and item.story_key in precomputed_estimates:
                est = precomputed_estimates[item.story_key]
                if est.get("status") == "UNESTIMABLE":
                    item.points = max(minimum, min(maximum, 5))
                    item.estimate_rationale = ["zone-estimator=UNESTIMABLE", f"default=5", f"final={item.points}"]
                else:
                    effort_score = int(est.get("effort_score", 3))
                    est_days = est.get("estimated_person_days")
                    if est_days is not None:
                        try:
                            est_days = float(est_days)
                        except (TypeError, ValueError):
                            est_days = None
                    item.points = effort_to_story_points(effort_score, est_days, minimum, maximum)
                    item.estimate_rationale = [
                        f"zone-estimator:effort_score={effort_score}",
                        f"estimated_person_days={est_days}",
                        f"final={item.points}",
                    ]
                    if item.points >= 8:
                        item.estimate_rationale.append("split_recommended=true")
            else:
                item.points, item.estimate_rationale = estimate_points(
                    item.body, item.title, minimum, maximum
                )


def mark_selectable(entries: List[StoryEntry]) -> None:
    entries_by_epic: Dict[int, List[StoryEntry]] = {}
    by_bmad = {item.bmad_id: item for item in entries}

    for item in entries:
        entries_by_epic.setdefault(item.epic_num, []).append(item)

    for epic_entries in entries_by_epic.values():
        epic_entries.sort(key=lambda story: story.story_num)
        selected_prefix: set[str] = set()
        blocked_by_external = False

        for item in epic_entries:
            if item.status == "done":
                continue

            if item.status != "backlog":
                blocked_by_external = True
                continue

            if blocked_by_external:
                item.selectable = False
                continue

            dep_ok = True
            for dependency_id in item.dependencies:
                dependency = by_bmad.get(dependency_id)
                if dependency is None:
                    continue
                if dependency.status == "done" or dependency.bmad_id in selected_prefix:
                    continue
                dep_ok = False

            item.selectable = dep_ok
            if item.selectable:
                selected_prefix.add(item.bmad_id)
            elif item.dependencies:
                dependency = by_bmad.get(item.dependencies[0])
                if dependency and dependency.status != "backlog":
                    blocked_by_external = True


def build_epic_options(entries: List[StoryEntry]) -> Dict[int, List[EpicOption]]:
    by_epic_backlog: Dict[int, List[StoryEntry]] = {}
    by_epic_selectable: Dict[int, List[StoryEntry]] = {}

    for item in entries:
        if item.status != "backlog":
            continue
        by_epic_backlog.setdefault(item.epic_num, []).append(item)
        if item.selectable:
            by_epic_selectable.setdefault(item.epic_num, []).append(item)

    options: Dict[int, List[EpicOption]] = {}
    for epic_num, backlog_items in by_epic_backlog.items():
        backlog_items.sort(key=lambda story: story.story_num)
        selectable_items = sorted(by_epic_selectable.get(epic_num, []), key=lambda story: story.story_num)

        total_backlog = len(backlog_items)
        completable = len(selectable_items) == total_backlog

        epic_options: List[EpicOption] = [EpicOption(k=0, points=0, completed_epic=0, stories=[])]
        running_points = 0
        running_stories: List[str] = []

        for idx, story in enumerate(selectable_items, start=1):
            running_points += int(story.points or 0)
            running_stories.append(story.bmad_id)
            is_complete = 1 if completable and idx == total_backlog and total_backlog > 0 else 0
            epic_options.append(
                EpicOption(
                    k=idx,
                    points=running_points,
                    completed_epic=is_complete,
                    stories=list(running_stories),
                )
            )

        options[epic_num] = epic_options

    return options


def choose_prioritized_epic_option(
    options: Dict[int, List[EpicOption]],
    epic_num: int,
    budget: int,
) -> Tuple[List[str], int, int]:
    """Select the maximum option for a single epic that fits within budget."""
    epic_opts = options.get(epic_num, [])
    best_option: Optional[EpicOption] = None
    for opt in epic_opts:
        if opt.points <= budget and (best_option is None or opt.points > best_option.points):
            best_option = opt
    if best_option is None:
        return [], 0, 0
    return list(best_option.stories), best_option.points, best_option.completed_epic


def choose_story_set(
    options: Dict[int, List[EpicOption]],
    target_points: int,
    allow_overflow: bool,
    exclude_epics: Optional[set[int]] = None,
) -> Tuple[List[str], int, int]:
    if not options:
        return [], 0, 0

    epics = sorted(k for k in options.keys() if not (exclude_epics and k in exclude_epics))
    state: Dict[int, Dict[str, Any]] = {0: {"completed": 0, "stories": 0, "choice": {}}}

    def score(completed: int, points: int, stories: int) -> Tuple[int, int, int]:
        if allow_overflow:
            utilization = -abs(points - target_points)
        else:
            utilization = points
        return (completed, utilization, stories)

    for epic in epics:
        next_state: Dict[int, Dict[str, Any]] = {}
        for used_points, payload in state.items():
            for option in options[epic]:
                new_points = used_points + option.points
                if not allow_overflow and new_points > target_points:
                    continue

                new_payload = {
                    "completed": payload["completed"] + option.completed_epic,
                    "stories": payload["stories"] + option.k,
                    "choice": dict(payload["choice"]),
                }
                new_payload["choice"][epic] = option

                current = next_state.get(new_points)
                if current is None:
                    next_state[new_points] = new_payload
                    continue

                current_score = score(current["completed"], new_points, current["stories"])
                candidate_score = score(new_payload["completed"], new_points, new_payload["stories"])
                if candidate_score > current_score:
                    next_state[new_points] = new_payload

        state = next_state

    if not state:
        return [], 0, 0

    best_points: Optional[int] = None
    best_payload: Optional[Dict[str, Any]] = None
    best_score: Optional[Tuple[int, int, int]] = None

    for points, payload in state.items():
        candidate_score = score(payload["completed"], points, payload["stories"])
        if best_score is None or candidate_score > best_score:
            best_points = points
            best_payload = payload
            best_score = candidate_score

    selected: List[str] = []
    if best_payload is None or best_points is None:
        return [], 0, 0

    for epic in epics:
        option = best_payload["choice"].get(epic)
        if option:
            selected.extend(option.stories)

    return selected, best_points, int(best_payload["completed"])


def assign_waves(selected_entries: List[StoryEntry], done_ids: set[str]) -> Dict[str, int]:
    remaining = sorted(selected_entries, key=lambda story: story.sort_key)
    completed = set(done_ids)
    wave_index = 1
    waves: Dict[str, int] = {}

    while remaining:
        wave = [story for story in remaining if all(dep in completed for dep in story.dependencies)]
        if not wave:
            break

        for story in wave:
            waves[story.bmad_id] = wave_index
            completed.add(story.bmad_id)

        remaining = [story for story in remaining if story.bmad_id not in waves]
        wave_index += 1

    return waves


def _parse_env_file(path: Path) -> Dict[str, str]:
    env_vars: Dict[str, str] = {}
    if not path.exists():
        return env_vars

    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip()
        if (value.startswith('"') and value.endswith('"')) or (
            value.startswith("'") and value.endswith("'")
        ):
            value = value[1:-1]
        env_vars[key] = value
    return env_vars


def _search_paths(repo_root: Path, filename: str, absolute_fallback: str) -> List[Path]:
    return [
        repo_root / filename,
        repo_root.parent / filename,
        repo_root.parent.parent / filename,
        repo_root.parent.parent.parent / filename,
        Path(absolute_fallback),
    ]


def _has_all_credentials(data: Dict[str, Any]) -> bool:
    return all(bool(str(data.get(key, "")).strip()) for key in JIRA_REQUIRED_CREDENTIALS)


def _detect_jira_auth_source(repo_root: Path) -> str:
    for env_path in _search_paths(repo_root, ".env.local", "/apps/zone.cardless/.env.local"):
        if _has_all_credentials(_parse_env_file(env_path)):
            return "env.local"

    if _has_all_credentials({key: os.getenv(key, "") for key in JIRA_REQUIRED_CREDENTIALS}):
        return "environment"

    for mcp_path in _search_paths(repo_root, ".mcp.json", "/apps/zone.cardless/.mcp.json"):
        if not mcp_path.exists():
            continue
        try:
            config = json.loads(mcp_path.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            continue
        env = config.get("mcpServers", {}).get("jira-agile", {}).get("env", {})
        if isinstance(env, dict) and _has_all_credentials(env):
            return "mcp.json"

    return "none"


def _load_jira_auth_loader(repo_root: Path):
    jira_client_path = repo_root / ".claude/skills/_common/jira_client.py"
    if not jira_client_path.exists():
        raise SprintPlanningError(f"jira_client module not found: {jira_client_path}")

    spec = importlib.util.spec_from_file_location("zone_sprint_jira_client", jira_client_path)
    if spec is None or spec.loader is None:
        raise SprintPlanningError(f"Unable to load jira_client module spec: {jira_client_path}")

    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    get_jira_auth = getattr(module, "get_jira_auth", None)
    if not callable(get_jira_auth):
        raise SprintPlanningError(f"get_jira_auth not found in: {jira_client_path}")
    return get_jira_auth


def check_preflight(repo_root: Path, phase4_config: Dict[str, str]) -> Dict[str, Any]:
    jira_agile_script = repo_root / ".claude/skills/jira-agile/scripts/jira_agile.py"
    workflow_path = Path(phase4_config["story_creator_workflow"])

    jira_cli_ready = False
    jira_cli_error = ""

    if jira_agile_script.exists():
        command = ["python3", str(jira_agile_script), "--help"]
        completed = subprocess.run(command, capture_output=True, text=True)
        jira_cli_ready = completed.returncode == 0
        if not jira_cli_ready:
            jira_cli_error = (completed.stderr or completed.stdout).strip().splitlines()[0]
    else:
        jira_cli_error = f"Missing script: {jira_agile_script}"

    jira_env_ready = False
    jira_auth_error = ""
    jira_auth_source = "none"
    missing_credentials = list(JIRA_REQUIRED_CREDENTIALS)

    try:
        get_jira_auth = _load_jira_auth_loader(repo_root)
        previous_cwd = Path.cwd()
        try:
            os.chdir(repo_root)
            get_jira_auth()
        finally:
            os.chdir(previous_cwd)
        jira_env_ready = True
        missing_credentials = []
    except Exception as exc:  # pragma: no cover - env dependent
        jira_auth_error = str(exc)

    detected_source = _detect_jira_auth_source(repo_root)
    jira_auth_source = detected_source if jira_env_ready else ("none" if detected_source == "none" else detected_source)

    return {
        "phase4_mode": phase4_config["phase4_mode"],
        "story_creator_workflow": str(workflow_path),
        "story_creator_workflow_exists": workflow_path.exists(),
        "jira_agile_script": str(jira_agile_script),
        "jira_agile_cli_ready": jira_cli_ready,
        "jira_agile_cli_error": jira_cli_error,
        "jira_env_ready": jira_env_ready,
        "jira_missing_env": missing_credentials,
        "jira_auth_source": jira_auth_source,
        "jira_auth_error": jira_auth_error,
        "jira_missing_credentials": missing_credentials,
    }


def build_plan(
    repo_root: Path,
    target_points_override: Optional[int],
    project_key_override: Optional[str],
    estimates_file: Optional[Path] = None,
    prioritize_epic: Optional[int] = None,
) -> Dict[str, Any]:
    config = load_skill_config(repo_root)
    phase4_config = load_phase4_config(config, repo_root)
    bmad_paths = load_bmad_paths(repo_root)

    planning_artifacts = bmad_paths["planning_artifacts"]
    implementation_artifacts = bmad_paths["implementation_artifacts"]

    sprint_status_path = implementation_artifacts / "sprint-status.yaml"
    epics_path = planning_artifacts / "epics.md"
    readiness_path = latest_file("implementation-readiness-report-*.md", planning_artifacts)

    jira_config = config.get("jira", {})
    mapping_template = str(
        jira_config.get(
            "mapping_file",
            "{project-root}/_bmad-output/implementation-artifacts/jira-key-map.yaml",
        )
    )
    mapping_path = resolve_path(mapping_template, repo_root)

    sprint_status = read_yaml(sprint_status_path)
    development_status = sprint_status.get("development_status")
    if not isinstance(development_status, dict) or not development_status:
        raise SprintPlanningError(f"No development_status entries found in {sprint_status_path}")

    epics_content = read_text(epics_path)
    stories_meta, epic_titles = parse_epics_markdown(epics_content)

    entries = build_story_entries(development_status, stories_meta)
    attach_dependencies(entries)

    planning_config = config.get("planning", {})
    minimum = int(planning_config.get("min_point_per_story", 1))
    maximum = int(planning_config.get("max_point_per_story", 13))

    precomputed = None
    if estimates_file is not None:
        precomputed = load_precomputed_estimates(estimates_file)
    elif planning_config.get("estimates_file"):
        est_path = resolve_path(str(planning_config["estimates_file"]), repo_root)
        precomputed = load_precomputed_estimates(est_path)

    attach_blockers_and_estimates(entries, minimum, maximum, precomputed)
    mark_selectable(entries)

    options = build_epic_options(entries)

    sprint_config = config.get("sprint", {})
    configured_target = sprint_config.get("target_story_points")
    target_points = target_points_override if target_points_override is not None else configured_target
    if target_points in (None, ""):
        raise SprintPlanningError(
            "target_story_points is missing. Set .claude/skills/zone-sprint/config.yaml or pass --target-points."
        )
    target_points = int(target_points)

    allow_overflow = bool(planning_config.get("allow_overflow", False))

    if prioritize_epic is not None:
        phase1_ids, phase1_points, phase1_completed = choose_prioritized_epic_option(
            options, prioritize_epic, target_points
        )
        remaining_budget = target_points - phase1_points
        phase2_ids, phase2_points, phase2_completed = choose_story_set(
            options, remaining_budget, allow_overflow, exclude_epics={prioritize_epic}
        )
        selected_ids = phase1_ids + phase2_ids
        selected_points = phase1_points + phase2_points
        completed_epics = phase1_completed + phase2_completed
    else:
        selected_ids, selected_points, completed_epics = choose_story_set(
            options, target_points, allow_overflow
        )
    selected_set = set(selected_ids)

    mapping_data = read_yaml(mapping_path)
    project_key = str(
        project_key_override
        or jira_config.get("project_key")
        or mapping_data.get("active_project_key")
        or "BMAD"
    )

    project_mapping = mapping_data.get("projects", {}).get(project_key, {})
    mapping_items = project_mapping.get("items", []) if isinstance(project_mapping, dict) else []
    jira_by_bmad: Dict[str, str] = {}
    for item in mapping_items:
        if item.get("bmad_type") == "story" and item.get("jira_key"):
            jira_by_bmad[str(item.get("bmad_id"))] = str(item.get("jira_key"))

    done_ids = {item.bmad_id for item in entries if item.status == "done"}
    selected_entries = [item for item in entries if item.bmad_id in selected_set]
    selected_entries.sort(key=lambda story: story.sort_key)

    for item in selected_entries:
        item.jira_key = jira_by_bmad.get(item.bmad_id)

    waves = assign_waves(selected_entries, done_ids)

    duration_days = int(sprint_config.get("duration_days", 14))
    today = dt.date.today()
    end_date = today + dt.timedelta(days=max(duration_days - 1, 0))

    project_history = (
        project_mapping.get("sprint_planning_history", []) if isinstance(project_mapping, dict) else []
    )
    sprint_index = len(project_history) + 1
    sprint_name_template = str(sprint_config.get("name_template", "Sprint {index} ({start_date} - {end_date})"))
    sprint_name = sprint_name_template.format(
        index=sprint_index,
        start_date=today.isoformat(),
        end_date=end_date.isoformat(),
    )
    sprint_goal = str(
        sprint_config.get(
            "goal_template",
            "Deliver highest-value unblocked stories while maximizing epic completion.",
        )
    )

    selected_payload = []
    for item in selected_entries:
        selected_payload.append(
            {
                "bmad_id": item.bmad_id,
                "epic": item.epic_num,
                "story": item.story_num,
                "story_key": item.story_key,
                "title": item.title,
                "status": item.status,
                "story_points": item.points,
                "dependencies": item.dependencies,
                "wave": waves.get(item.bmad_id),
                "jira_key": item.jira_key,
                "estimate_rationale": item.estimate_rationale,
                "body": item.body,
            }
        )

    backlog_entries = [item for item in entries if item.status == "backlog"]
    backlog_entries.sort(key=lambda story: story.sort_key)

    dependency_matrix: Dict[str, Dict[str, Any]] = {}
    blocked_ids: List[str] = []
    unblocked_ids: List[str] = []

    for item in backlog_entries:
        blocked = len(item.blocked_by) > 0
        if blocked:
            blocked_ids.append(item.bmad_id)
        else:
            unblocked_ids.append(item.bmad_id)

        dependency_matrix[item.bmad_id] = {
            "story_key": item.story_key,
            "title": item.title,
            "dependencies": list(item.dependencies),
            "blocked_by": list(item.blocked_by),
            "unblocked_at_plan_time": not blocked,
            "selectable": item.selectable,
            "story_points": item.points,
        }

    epic_summary: List[Dict[str, Any]] = []
    by_epic_backlog: Dict[int, List[StoryEntry]] = {}
    by_epic_selected: Dict[int, List[StoryEntry]] = {}
    for item in backlog_entries:
        by_epic_backlog.setdefault(item.epic_num, []).append(item)
    for item in selected_entries:
        by_epic_selected.setdefault(item.epic_num, []).append(item)

    for epic_num in sorted(by_epic_backlog.keys()):
        backlog_count = len(by_epic_backlog[epic_num])
        selected_count = len(by_epic_selected.get(epic_num, []))
        epic_summary.append(
            {
                "epic": epic_num,
                "epic_title": epic_titles.get(epic_num, f"Epic {epic_num}"),
                "backlog_story_count": backlog_count,
                "selected_story_count": selected_count,
                "completed_by_selection": backlog_count > 0 and selected_count == backlog_count,
            }
        )

    preflight = check_preflight(repo_root, phase4_config)
    jira_requirements_met = preflight["jira_agile_cli_ready"] and preflight["jira_env_ready"]

    wave_1_story_keys = [
        item["story_key"] for item in selected_payload if item.get("wave") == 1
    ]
    workflow_instructions = [
        (
            f"Execute markdown-native workflow {phase4_config['story_creator_workflow']} "
            f"for story key {story_key}"
        )
        for story_key in wave_1_story_keys
    ]

    commands = {
        "phase4_mode": phase4_config["phase4_mode"],
        "phase4_story_creator_workflow": phase4_config["story_creator_workflow"],
        "phase4_wave1_story_keys": wave_1_story_keys,
        "phase4_execute_wave1": workflow_instructions,
        "jira_discover_board": (
            "python3 .claude/skills/jira-agile/scripts/jira_agile.py list-boards "
            f"--project {project_key} --type scrum --max-results 50"
        ),
        "jira_estimation": [
            f"python3 .claude/skills/jira-agile/scripts/jira_agile.py set-estimation <board_id> {item['jira_key']} {item['story_points']}"
            for item in selected_payload
            if item.get("jira_key")
        ],
        "jira_create_sprint": (
            "python3 .claude/skills/jira-agile/scripts/jira_agile.py create-sprint <board_id> "
            f"\"{sprint_name}\" --goal \"{sprint_goal}\" "
            f"--start-date \"{today.isoformat()}T00:00:00.000Z\" "
            f"--end-date \"{end_date.isoformat()}T00:00:00.000Z\""
        ),
    }

    return {
        "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
        "paths": {
            "repo_root": str(repo_root),
            "sprint_status": str(sprint_status_path),
            "epics": str(epics_path),
            "readiness_report": str(readiness_path) if readiness_path else "",
            "jira_mapping": str(mapping_path),
        },
        "project_key": project_key,
        "sprint": {
            "name": sprint_name,
            "goal": sprint_goal,
            "start_date": today.isoformat(),
            "end_date": end_date.isoformat(),
            "duration_days": duration_days,
            "target_story_points": target_points,
            "selected_story_points": selected_points,
            "completed_epics_by_selection": completed_epics,
            "prioritize_epic": prioritize_epic,
        },
        "summary": {
            "total_backlog_stories": len(backlog_entries),
            "selected_story_count": len(selected_payload),
            "selected_wave_1_story_count": len(
                [item for item in selected_payload if item.get("wave") == 1]
            ),
            "unblocked_at_plan_time": len(unblocked_ids),
            "blocked_at_plan_time": len(blocked_ids),
        },
        "selected_stories": selected_payload,
        "epic_summary": epic_summary,
        "dependency_matrix": dependency_matrix,
        "blocked_story_ids": blocked_ids,
        "unblocked_story_ids": unblocked_ids,
        "preflight": {
            **preflight,
            "jira_requirements_met": jira_requirements_met,
            "jira_require_tools": bool(jira_config.get("require_tools", True)),
        },
        "commands": commands,
        "execution": {
            "phase4_mode": phase4_config["phase4_mode"],
            "story_creator_workflow": phase4_config["story_creator_workflow"],
        },
    }


def emit(payload: Dict[str, Any], output_format: str) -> str:
    if output_format == "yaml":
        return yaml.safe_dump(payload, sort_keys=False)
    return json.dumps(payload, indent=2)


def main() -> int:
    parser = argparse.ArgumentParser(description="zone-sprint deterministic planner (plan-only)")
    parser.add_argument(
        "command",
        nargs="?",
        choices=["plan"],
        default="plan",
        help="Only 'plan' is supported.",
    )
    parser.add_argument("--repo-root", default=".", help="Repository root")
    parser.add_argument("--target-points", type=int, help="Override target story points")
    parser.add_argument(
        "--prioritize-epic",
        type=int,
        metavar="N",
        help="Prioritize Epic N: fill budget with Epic N stories first, then fill remainder with other epics",
    )
    parser.add_argument("--project-key", help="Override Jira project key")
    parser.add_argument(
        "--estimates-file",
        help="Path to precomputed story estimates (YAML/JSON from zone-estimator subagent)",
    )
    parser.add_argument("--format", choices=["json", "yaml"], default="json")
    parser.add_argument("--output", help="Write plan output to file")

    args = parser.parse_args()

    try:
        repo_root = Path(args.repo_root).resolve()
        estimates_path = None
        if args.estimates_file:
            p = Path(args.estimates_file)
            estimates_path = (repo_root / p) if not p.is_absolute() else p.resolve()
        plan = build_plan(
            repo_root,
            args.target_points,
            args.project_key,
            estimates_file=estimates_path,
            prioritize_epic=args.prioritize_epic,
        )
        rendered = emit(plan, args.format)
        if args.output:
            Path(args.output).write_text(rendered + "\n", encoding="utf-8")
        print(rendered)
        return 0
    except SprintPlanningError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
