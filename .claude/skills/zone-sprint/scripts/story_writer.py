#!/usr/bin/env python3
"""Story Writer utility for Zone Agentic SDLC (Phase 4 story generation)."""

import argparse
import os
import re
import sys
import time
from pathlib import Path

import yaml

STORY_KEY_RE = re.compile(r"^(\d+)-(\d+)-")

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    HAS_FCNTL = False

def read_text(path: Path) -> str:
    if not path.exists():
        print(f"Error: File not found: {path}", file=sys.stderr)
        sys.exit(1)
    return path.read_text(encoding="utf-8")

def _acquire_status_lock(lock_path: Path) -> object:
    """Acquire exclusive lock on sprint-status for concurrent write safety. Returns lock file handle or None."""
    if not HAS_FCNTL:
        return None
    lock_file = open(lock_path, "w")
    for attempt in range(10):
        try:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            return lock_file
        except (BlockingIOError, OSError):
            if attempt == 9:
                lock_file.close()
                print("Error: Could not acquire lock on sprint-status.yaml after 10 attempts.", file=sys.stderr)
                sys.exit(1)
            time.sleep(0.5)
    return lock_file

def _release_status_lock(lock_file: object) -> None:
    """Release lock and close lock file."""
    if lock_file is None:
        return
    try:
        if HAS_FCNTL:
            fcntl.flock(lock_file.fileno(), fcntl.LOCK_UN)
    finally:
        lock_file.close()

def update_sprint_status(status_file: Path, story_key: str, epic_num: int):
    """Updates sprint-status.yaml preserving comments using ruamel.yaml if available, else fallback.
    Uses file locking for concurrent write safety when multiple subagents run in parallel."""
    if not status_file.exists():
        print(f"Error: sprint-status.yaml not found at {status_file}", file=sys.stderr)
        sys.exit(1)

    lock_path = status_file.parent / ".sprint-status.lock"
    lock_file = _acquire_status_lock(lock_path)
    try:
        _update_sprint_status_impl(status_file, story_key, epic_num)
    finally:
        _release_status_lock(lock_file)

def _update_sprint_status_impl(status_file: Path, story_key: str, epic_num: int):
    """Internal implementation of sprint-status update (caller holds lock)."""
    try:
        from ruamel.yaml import YAML
        yaml_handler = YAML()
        yaml_handler.preserve_quotes = True

        with status_file.open("r", encoding="utf-8") as f:
            data = yaml_handler.load(f)

        dev_status = data.get("development_status", {})

        # Mark epic in progress if it's currently backlog
        epic_key = f"epic-{epic_num}"
        if epic_key in dev_status and dev_status[epic_key] == "backlog":
            dev_status[epic_key] = "in-progress"

        # Mark story ready for dev
        if story_key in dev_status:
            dev_status[story_key] = "ready-for-dev"

        with status_file.open("w", encoding="utf-8") as f:
            yaml_handler.dump(data, f)

    except ImportError:
        # Fallback to crude string replacement if ruamel.yaml not installed
        lines = status_file.read_text(encoding="utf-8").splitlines()
        updated_lines = []
        for line in lines:
            if line.strip().startswith(f"epic-{epic_num}:") and "backlog" in line:
                updated_lines.append(line.replace("backlog", "in-progress"))
            elif line.strip().startswith(f"{story_key}:") and "backlog" in line:
                updated_lines.append(line.replace("backlog", "ready-for-dev"))
            else:
                updated_lines.append(line)
        status_file.write_text("\n".join(updated_lines) + "\n", encoding="utf-8")

def main():
    parser = argparse.ArgumentParser(description="Create a BMAD story from external inputs.")
    parser.add_argument("command", choices=["write"], help="Command to execute")
    parser.add_argument("story_key", help="The full key of the story (e.g. 1-2-user-auth)")
    parser.add_argument("--repo-root", required=True, help="Path to project repository")
    parser.add_argument("--title", required=True, help="Human readable story title")
    parser.add_argument("--statement-file", required=True, help="Path to file containing user story statement")
    parser.add_argument("--ac-file", required=True, help="Path to file containing acceptance criteria snippet")
    parser.add_argument("--tasks-file", required=True, help="Path to file containing tasks/subtasks snippet")
    parser.add_argument("--dev-notes-file", required=True, help="Path to file containing comprehensive dev notes section")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    
    match = STORY_KEY_RE.match(args.story_key)
    if not match:
        print(f"Error: Invalid story_key format. Expected 'epic_num-story_num-slug'", file=sys.stderr)
        sys.exit(1)
        
    epic_num = int(match.group(1))
    story_num = int(match.group(2))
    
    # Resolve paths
    template_path = repo_root / "_bmad/bmm/workflows/4-implementation/create-story/template.md"
    story_dir = repo_root / "_bmad-output/implementation-artifacts/stories"
    status_file = repo_root / "_bmad-output/implementation-artifacts/sprint-status.yaml"
    out_file = story_dir / f"{args.story_key}.md"
    
    story_dir.mkdir(parents=True, exist_ok=True)
    
    try:
        template = read_text(template_path)
        statement = read_text(Path(args.statement_file))
        ac_text = read_text(Path(args.ac_file))
        tasks_text = read_text(Path(args.tasks_file))
        dev_notes = read_text(Path(args.dev_notes_file))
        
        # Process template
        output = template.replace("{{epic_num}}", str(epic_num))
        output = output.replace("{{story_num}}", str(story_num))
        output = output.replace("{{story_title}}", args.title)
        output = output.replace("{{agent_model_name_version}}", "Claude/GPT (via zone-sprint)")
        
        # Inject sections
        # Replace the entire statement block
        statement_pattern = re.compile(r"As a \{\{role\}\},.*?so that \{\{benefit\}\}\.", re.DOTALL)
        output = statement_pattern.sub(statement, output)
        
        # Inject ACs
        output = output.replace("1. [Add acceptance criteria from epics/PRD]", ac_text.strip())
        
        # Inject Tasks
        tasks_start = output.find("## Tasks / Subtasks")
        if tasks_start != -1:
            next_heading = output.find("## Dev Notes", tasks_start)
            if next_heading != -1:
                output = output[:tasks_start + 19] + "\n\n" + tasks_text.strip() + "\n\n" + output[next_heading:]
        
        # Inject Dev Notes (Replacing everything from ## Dev Notes down to ## Dev Agent Record)
        dev_notes_start = output.find("## Dev Notes")
        if dev_notes_start != -1:
            dev_agent_record_start = output.find("## Dev Agent Record")
            if dev_agent_record_start != -1:
                # Replace the entire chunk including the hardcoded Project Structure/References
                output = output[:dev_notes_start] + "## Dev Notes\n\n" + dev_notes.strip() + "\n\n" + output[dev_agent_record_start:]
                
        out_file.write_text(output, encoding="utf-8")
        print(f"Created story {args.story_key} at {out_file}")
        
        update_sprint_status(status_file, args.story_key, epic_num)
        print(f"Updated sprint-status.yaml")
        
    except Exception as e:
        print(f"Fatal Error processing story: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
