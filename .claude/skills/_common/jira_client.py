#!/usr/bin/env python3
"""
Shared Jira HTTP Client for BMAD Skills

Provides unified access to both Jira Agile API and Core API.
Zero external dependencies beyond Python stdlib (urllib).

Used by:
- jira-sync: Bidirectional YAML-Jira synchronization
- jira-agile: Sprint/board/epic management CLI

Authentication via environment variables or .mcp.json.
"""

import json
import os
import uuid
from base64 import b64encode
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.error import HTTPError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from jira_adf import render_adf


class JiraClient:
    """Unified Jira REST API client (Agile + Core APIs)."""

    def __init__(self, cloud_id: str, email: str, api_token: str):
        """Initialize with Basic auth credentials."""
        self.cloud_id = cloud_id
        self.agile_base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/agile/1.0"
        self.api_base_url = f"https://api.atlassian.com/ex/jira/{cloud_id}/rest/api/3"  # API v3 (v2 deprecated)

        credentials = b64encode(f"{email}:{api_token}".encode()).decode()
        self.headers = {
            "Authorization": f"Basic {credentials}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }

    def _request(
        self,
        method: str,
        path: str,
        base_url: str = None,
        data: Optional[Dict] = None,
        params: Optional[Dict] = None
    ) -> Dict:
        """Make HTTP request to Jira API."""
        if base_url is None:
            base_url = self.api_base_url

        url = f"{base_url}{path}"
        if params:
            # Remove None values
            params = {k: v for k, v in params.items() if v is not None}
            if params:
                url = f"{url}?{urlencode(params)}"

        body = json.dumps(data).encode() if data else None
        req = Request(url, data=body, headers=self.headers, method=method)

        try:
            with urlopen(req) as response:
                if response.status == 204:
                    return {"success": True}
                return json.loads(response.read().decode())
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            raise Exception(f"HTTP {e.code}: {error_body}")

    # ===== AGILE API: Board Operations =====

    def list_boards(
        self,
        project_key: Optional[str] = None,
        board_type: Optional[str] = None,
        name: Optional[str] = None,
        start_at: int = 0,
        max_results: int = 50
    ) -> Dict:
        """List available boards."""
        return self._request(
            "GET",
            "/board",
            base_url=self.agile_base_url,
            params={
                "projectKeyOrId": project_key,
                "type": board_type,
                "name": name,
                "startAt": start_at,
                "maxResults": max_results
            }
        )

    def get_board(self, board_id: int) -> Dict:
        """Get board details."""
        return self._request("GET", f"/board/{board_id}", base_url=self.agile_base_url)

    # ===== AGILE API: Sprint Operations =====

    def list_sprints(
        self,
        board_id: int,
        state: Optional[str] = None,
        start_at: int = 0,
        max_results: int = 50
    ) -> Dict:
        """List sprints for a board."""
        return self._request(
            "GET",
            f"/board/{board_id}/sprint",
            base_url=self.agile_base_url,
            params={"state": state, "startAt": start_at, "maxResults": max_results}
        )

    def get_sprint(self, sprint_id: int) -> Dict:
        """Get sprint details."""
        return self._request("GET", f"/sprint/{sprint_id}", base_url=self.agile_base_url)

    def create_sprint(
        self,
        board_id: int,
        name: str,
        goal: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Create a new sprint."""
        data = {"originBoardId": board_id, "name": name}
        if goal:
            data["goal"] = goal
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date
        return self._request("POST", "/sprint", base_url=self.agile_base_url, data=data)

    def update_sprint(
        self,
        sprint_id: int,
        name: Optional[str] = None,
        state: Optional[str] = None,
        goal: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict:
        """Update sprint properties or state."""
        data = {}
        if name:
            data["name"] = name
        if state:
            data["state"] = state
        if goal:
            data["goal"] = goal
        if start_date:
            data["startDate"] = start_date
        if end_date:
            data["endDate"] = end_date
        return self._request(
            "POST", f"/sprint/{sprint_id}", base_url=self.agile_base_url, data=data
        )

    # ===== AGILE API: Sprint-Issue Operations =====

    def get_sprint_issues(
        self,
        sprint_id: int,
        jql: Optional[str] = None,
        fields: Optional[List[str]] = None,
        start_at: int = 0,
        max_results: int = 50
    ) -> Dict:
        """Get issues in a sprint."""
        params = {"startAt": start_at, "maxResults": max_results}
        if jql:
            params["jql"] = jql
        if fields:
            params["fields"] = ",".join(fields)
        return self._request(
            "GET", f"/sprint/{sprint_id}/issue", base_url=self.agile_base_url, params=params
        )

    def add_to_sprint(self, sprint_id: int, issue_keys: List[str]) -> Dict:
        """Add issues to a sprint."""
        return self._request(
            "POST",
            f"/sprint/{sprint_id}/issue",
            base_url=self.agile_base_url,
            data={"issues": issue_keys}
        )

    def move_to_backlog(self, issue_keys: List[str]) -> Dict:
        """Move issues to backlog (remove from sprint)."""
        return self._request(
            "POST", "/backlog/issue", base_url=self.agile_base_url, data={"issues": issue_keys}
        )

    # ===== AGILE API: Backlog Operations =====

    def get_backlog(
        self,
        board_id: int,
        jql: Optional[str] = None,
        fields: Optional[List[str]] = None,
        start_at: int = 0,
        max_results: int = 50
    ) -> Dict:
        """Get backlog issues for a board."""
        params = {"startAt": start_at, "maxResults": max_results}
        if jql:
            params["jql"] = jql
        if fields:
            params["fields"] = ",".join(fields)
        return self._request(
            "GET", f"/board/{board_id}/backlog", base_url=self.agile_base_url, params=params
        )

    def get_estimation(self, board_id: int, issue_key: str) -> Dict:
        """Get story points for an issue."""
        return self._request(
            "GET",
            f"/issue/{issue_key}/estimation",
            base_url=self.agile_base_url,
            params={"boardId": board_id}
        )

    def set_estimation(self, board_id: int, issue_key: str, value: float) -> Dict:
        """Set story points for an issue."""
        return self._request(
            "PUT",
            f"/issue/{issue_key}/estimation",
            base_url=self.agile_base_url,
            params={"boardId": board_id},
            data={"value": str(value)}
        )

    # ===== AGILE API: Epic Operations =====

    def list_epics(
        self,
        board_id: int,
        done: Optional[bool] = None,
        start_at: int = 0,
        max_results: int = 50
    ) -> Dict:
        """List epics on a board."""
        params = {"startAt": start_at, "maxResults": max_results}
        if done is not None:
            params["done"] = str(done).lower()
        return self._request(
            "GET", f"/board/{board_id}/epic", base_url=self.agile_base_url, params=params
        )

    def get_epic_issues(
        self,
        epic_key: str,
        jql: Optional[str] = None,
        fields: Optional[List[str]] = None,
        start_at: int = 0,
        max_results: int = 50
    ) -> Dict:
        """Get issues in an epic."""
        params = {"startAt": start_at, "maxResults": max_results}
        if jql:
            params["jql"] = jql
        if fields:
            params["fields"] = ",".join(fields)
        return self._request(
            "GET", f"/epic/{epic_key}/issue", base_url=self.agile_base_url, params=params
        )

    def move_to_epic(self, epic_key: str, issue_keys: List[str]) -> Dict:
        """Move issues to an epic."""
        return self._request(
            "POST",
            f"/epic/{epic_key}/issue",
            base_url=self.agile_base_url,
            data={"issues": issue_keys}
        )

    # ===== CORE API: Issue Operations =====

    def get_issue(self, issue_key: str, fields: Optional[List[str]] = None) -> Dict:
        """Fetch single issue with field selection."""
        params = {}
        if fields:
            params["fields"] = ",".join(fields)
        return self._request("GET", f"/issue/{issue_key}", params=params)

    def create_issue(self, issue_data: Dict[str, Any]) -> Dict:
        """
        Create a new issue (Story, Epic, Task, Bug, etc.).
        
        Args:
            issue_data: Dict with 'fields' key containing issue fields.
                        Required fields: project, summary, issuetype
                        Optional: description, parent (for subtasks/stories under epics)
        
        Example:
            jira.create_issue({
                "fields": {
                    "project": {"key": "BMAD"},
                    "summary": "My new story",
                    "issuetype": {"name": "Story"},
                    "description": {"type": "doc", "version": 1, "content": [...]},
                    "parent": {"key": "BMAD-123"}  # Optional: link to epic
                }
            })
        
        Returns: Dict with 'id', 'key', 'self' fields
        """
        return self._request("POST", "/issue", data=issue_data)

    def search_jql(
        self,
        jql: str,
        fields: Optional[List[str]] = None,
        max_results: int = 100,
        start_at: int = 0
    ) -> Dict:
        """Search issues with JQL query."""
        params = {"jql": jql, "maxResults": max_results, "startAt": start_at}
        if fields:
            params["fields"] = ",".join(fields)
        return self._request("GET", "/search/jql", params=params)  # API v3 uses /search/jql

    def batch_get_issues(
        self, issue_keys: List[str], fields: Optional[List[str]] = None
    ) -> Dict[str, Dict]:
        """
        Batch fetch issues using JQL 'key IN (...)' query.

        More efficient than individual get_issue() calls.

        Returns: Dict keyed by issue_key for easy lookup
        """
        if not issue_keys:
            return {}

        jql = f"key IN ({','.join(issue_keys)})"
        results = self.search_jql(jql, fields, max_results=len(issue_keys))
        return {issue["key"]: issue for issue in results.get("issues", [])}

    def get_transitions(self, issue_key: str) -> List[Dict]:
        """Get available status transitions for issue."""
        result = self._request("GET", f"/issue/{issue_key}/transitions")
        return result.get("transitions", [])

    def find_transition_id(self, issue_key: str, target_status: str) -> str:
        """
        Find transition ID for target status name.

        Raises: ValueError if no transition to target status exists
        """
        transitions = self.get_transitions(issue_key)
        target_lower = target_status.lower()

        for transition in transitions:
            if transition.get("to", {}).get("name", "").lower() == target_lower:
                return transition["id"]

        raise ValueError(f"No transition to '{target_status}' for {issue_key}")

    def transition_issue(
        self,
        issue_key: str,
        transition_id: str,
        comment: Optional[str] = None,
        comment_format: str = "plain",
    ) -> Dict:
        """
        Change issue status.

        Args:
            issue_key: Issue key (e.g., "BMAD-5")
            transition_id: Transition ID from get_transitions()
            comment: Optional comment to add with transition
        """
        data: Dict[str, Any] = {"transition": {"id": transition_id}}

        if comment:
            data["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": render_adf(comment, comment_format)
                        }
                    }
                ]
            }

        return self._request("POST", f"/issue/{issue_key}/transitions", data=data)

    def update_issue(
        self,
        issue_key: str,
        fields: Dict[str, Any],
        comment: Optional[str] = None,
        comment_format: str = "plain",
    ) -> Dict:
        """
        Update issue fields (assignee, labels, etc.).

        Args:
            issue_key: Issue key
            fields: Dict of field updates (e.g., {"assignee": {"accountId": "..."}})
            comment: Optional comment to add
        """
        data: Dict[str, Any] = {"fields": fields}

        if comment:
            data["update"] = {
                "comment": [
                    {
                        "add": {
                            "body": render_adf(comment, comment_format)
                        }
                    }
                ]
            }

        return self._request("PUT", f"/issue/{issue_key}", data=data)

    def add_comment(self, issue_key: str, body: str, body_format: str = "plain") -> Dict:
        """Add comment to issue (API v3 uses ADF format)."""
        adf_body = render_adf(body, body_format)
        return self._request("POST", f"/issue/{issue_key}/comment", data={"body": adf_body})

    def attach_file(
        self, issue_key: str, file_path: str, filename: Optional[str] = None
    ) -> Dict:
        """
        Attach a file to a story.

        Uses multipart/form-data upload via the Jira attachment REST API.
        Requires X-Atlassian-Token: no-check header.

        Args:
            issue_key: Issue key (e.g., "CLSDLC-25")
            file_path: Local path to the file to attach
            filename: Override filename (defaults to basename of file_path)
        """
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        if filename is None:
            filename = path.name

        file_content = path.read_bytes()
        boundary = uuid.uuid4().hex

        # Build multipart/form-data body
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="{filename}"\r\n'
            f"Content-Type: application/octet-stream\r\n"
            f"\r\n"
        ).encode() + file_content + f"\r\n--{boundary}--\r\n".encode()

        url = f"{self.api_base_url}/issue/{issue_key}/attachments"
        headers = {
            "Authorization": self.headers["Authorization"],
            "Accept": "application/json",
            "X-Atlassian-Token": "no-check",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
        }

        req = Request(url, data=body, headers=headers, method="POST")

        try:
            with urlopen(req) as response:
                if response.status == 204:
                    return {"success": True}
                return json.loads(response.read().decode())
        except HTTPError as e:
            error_body = e.read().decode() if e.fp else str(e)
            raise Exception(f"HTTP {e.code}: {error_body}")


# ===== Authentication Helper =====

def _parse_env_file(path: Path) -> Dict[str, str]:
    """
    Parse a .env file and return key-value pairs.

    Handles:
    - Quoted values (single and double quotes)
    - Comments (lines starting with #)
    - Empty lines
    """
    env_vars = {}
    if not path.exists():
        return env_vars

    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()

        # Remove surrounding quotes
        if (value.startswith('"') and value.endswith('"')) or \
           (value.startswith("'") and value.endswith("'")):
            value = value[1:-1]

        env_vars[key] = value

    return env_vars


def get_jira_auth() -> tuple[str, str, str]:
    """
    Get Jira credentials from .env.local, environment, or .mcp.json.

    Returns: (cloud_id, email, api_token)

    Priority:
    1. .env.local file in project root (primary)
    2. Environment variables: ATLASSIAN_CLOUD_ID, ATLASSIAN_EMAIL, ATLASSIAN_API_TOKEN
    3. .mcp.json: jira-agile server config (fallback)

    Raises: ValueError if credentials not found
    """
    # Search paths for .env.local
    env_search_paths = [
        Path.cwd() / ".env.local",
        Path.cwd().parent / ".env.local",
        Path.cwd().parent.parent / ".env.local",
        Path.cwd().parent.parent.parent / ".env.local",
        Path("/apps/zone.cardless/.env.local"),  # Absolute fallback
    ]

    # Priority 1: Check .env.local file first (if exists)
    env_file_vars = {}
    for env_path in env_search_paths:
        if env_path.exists():
            env_file_vars = _parse_env_file(env_path)
            break  # Use the first .env.local found

    # Priority 2: Merge with environment variables
    # .env.local values take precedence, env vars fill gaps
    cloud_id = env_file_vars.get("ATLASSIAN_CLOUD_ID") or os.getenv("ATLASSIAN_CLOUD_ID")
    email = env_file_vars.get("ATLASSIAN_EMAIL") or os.getenv("ATLASSIAN_EMAIL")
    token = env_file_vars.get("ATLASSIAN_API_TOKEN") or os.getenv("ATLASSIAN_API_TOKEN")

    if all([cloud_id, email, token]):
        return cloud_id, email, token

    # Priority 3: Fallback to .mcp.json
    mcp_search_paths = [
        Path.cwd() / ".mcp.json",
        Path.cwd().parent / ".mcp.json",
        Path.cwd().parent.parent / ".mcp.json",
        Path.cwd().parent.parent.parent / ".mcp.json",
        Path("/apps/zone.cardless/.mcp.json"),  # Absolute fallback
    ]

    for mcp_path in mcp_search_paths:
        if mcp_path.exists():
            break
    else:
        mcp_path = None

    if mcp_path and mcp_path.exists():
        config = json.loads(mcp_path.read_text())
        env = config.get("mcpServers", {}).get("jira-agile", {}).get("env", {})
        cloud_id = env.get("ATLASSIAN_CLOUD_ID")
        email = env.get("ATLASSIAN_EMAIL")
        token = env.get("ATLASSIAN_API_TOKEN")

        if all([cloud_id, email, token]):
            return cloud_id, email, token

    raise ValueError(
        "Jira credentials not found. Configure .env.local (preferred), " +
        "set ATLASSIAN_* env vars, or configure .mcp.json"
    )
