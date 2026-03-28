#!/usr/bin/env python3
"""GitHub integration client for GymOps BMAD pipeline.

Replaces Jira/Confluence integration with GitHub Issues and PR management.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def gh_cli(args: List[str], check: bool = True) -> subprocess.CompletedProcess:
    """Run a GitHub CLI command."""
    cmd = ["gh"] + args
    return subprocess.run(cmd, capture_output=True, text=True, check=check)


def create_pr(
    title: str,
    body: str,
    branch: str,
    base: str = "main",
    labels: Optional[List[str]] = None,
    reviewers: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a pull request via GitHub CLI."""
    args = ["pr", "create", "--title", title, "--body", body, "--base", base, "--head", branch]
    if labels:
        args.extend(["--label", ",".join(labels)])
    if reviewers:
        args.extend(["--reviewer", ",".join(reviewers)])

    result = gh_cli(args, check=False)
    if result.returncode == 0:
        pr_url = result.stdout.strip()
        return {"status": "created", "url": pr_url}
    else:
        return {"status": "error", "error": result.stderr.strip()}


def add_pr_comment(pr_number: int, body: str) -> Dict[str, Any]:
    """Add a comment to a pull request."""
    result = gh_cli(["pr", "comment", str(pr_number), "--body", body], check=False)
    if result.returncode == 0:
        return {"status": "commented"}
    return {"status": "error", "error": result.stderr.strip()}


def add_pr_label(pr_number: int, labels: List[str]) -> Dict[str, Any]:
    """Add labels to a pull request."""
    result = gh_cli(["pr", "edit", str(pr_number), "--add-label", ",".join(labels)], check=False)
    if result.returncode == 0:
        return {"status": "labeled"}
    return {"status": "error", "error": result.stderr.strip()}


def get_pr_diff(pr_number: int) -> str:
    """Get the diff for a pull request."""
    result = gh_cli(["pr", "diff", str(pr_number)], check=False)
    return result.stdout if result.returncode == 0 else ""


def get_pr_files(pr_number: int) -> List[str]:
    """Get the list of changed files in a PR."""
    result = gh_cli(["pr", "diff", str(pr_number), "--name-only"], check=False)
    if result.returncode == 0:
        return [f for f in result.stdout.strip().split("\n") if f]
    return []


def create_issue(
    title: str,
    body: str,
    labels: Optional[List[str]] = None,
) -> Dict[str, Any]:
    """Create a GitHub issue."""
    args = ["issue", "create", "--title", title, "--body", body]
    if labels:
        args.extend(["--label", ",".join(labels)])

    result = gh_cli(args, check=False)
    if result.returncode == 0:
        return {"status": "created", "url": result.stdout.strip()}
    return {"status": "error", "error": result.stderr.strip()}


if __name__ == "__main__":
    # Quick test
    print("GitHub client loaded successfully")
