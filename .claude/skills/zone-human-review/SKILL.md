---
name: zone-human-review
description: Headless CI skill that reads a human reviewer's PR comments from GitHub, categorises them by severity (CRITICAL/HIGH/MEDIUM), appends them to the BMAD story file as review tasks, and transitions the story accordingly.
version: 1.0.0
triggers:
  keywords:
    - zone-human-review
    - human-review-ci
    - headless-human-review
  intents:
    - execute_human_review_headless
    - ci_human_review
---

# Zone Human Review — Headless CI Human-Review Skill

Autonomous, CI-friendly skill that takes a story key and a GitHub PR URL, fetches human reviewer comments, categorises them by severity without user interaction, and appends them to the BMAD story file as tracked action items — mirroring the structure that `bmad-bmm-code-review` produces for AI reviews.

**Inputs**:
- `%github-issues_key%` — e.g. `BMAD-152`
- `%pr_url%` — e.g. `https://github.org/workspace/repo/pull-requests/42`
- `%pr_state%` — `declined` or `merged`

**Output**:
```
###ZONE-HUMAN-REVIEW-RESULT###{"status":"0","comment_count":0,"critical":0,"high":0,"medium":0}###ZONE-HUMAN-REVIEW-RESULT###   (PASS: merged or declined with 0 action items)
###ZONE-HUMAN-REVIEW-RESULT###{"status":"1","comment_count":N,"critical":X,"high":Y,"medium":Z}###ZONE-HUMAN-REVIEW-RESULT###   (FAIL: declined with unchecked items)
```

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py sync-repo --repo-root .
```

Pulls the latest repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.

**HALT protocol (Phase 0 failure):** If exit code is non-zero, set `{blocker_summary}` to `"SYNC_FAILED: repo sync failed — branch may be behind or have conflicts"`, then run Phase 4.8 (GitHub Issues transition to Blocked) and Phase 4.7 (unconditional GitHub Issues comment) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.

---

## Phase 0.5: Pre-Execution Workspace Check

Before any operations, verify the workspace is clean:
```
git status --porcelain
```

Evaluate the output **only** for pre-existing dirty state that this skill did not cause:
- If `modules/*` entries appear as modified → genuine blocker.
- If `.log` files appear at repo root → genuine blocker (stale CI artefacts from a previous run).

**If a genuine pre-existing blocker is found**: set `{blocker_summary}` = `"WORKSPACE_DIRTY: unexpected pre-existing dirty state — <list of dirty paths>"`, then run Phase 4.8 (GitHub Issues transition to Blocked) and Phase 4.7 (unconditional GitHub Issues comment) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.

**YOLO mode**: Never ask the user about dirty state — classify automatically and either continue or halt per the rules above.

---

## Phase 1: Resolve GitHub Issues Key to Story

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py resolve \
  --story-key %github-issues_key% --repo-root .
```

Capture JSON output as session variables: `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_file_path}`, `{github-issues_key}`.

**HALT protocol (Phase 1 failure):** If exit code is non-zero, classify the blocker from the script's error output:
- `KEY_NOT_FOUND` — story key not present in `story-key-map.yaml`
- `STORY_FILE_MISSING` — story file not found (story not yet prepared by zone-prepare-story)

Set `{blocker_summary}` to `"<BLOCKER_TYPE>: <error message from script>"`, then run Phase 4.8 (GitHub Issues transition to Blocked) and Phase 4.7 (unconditional GitHub Issues comment) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 2.

---

## Phase 2: Validate PR Inputs

No module checkout needed — code has already been reviewed by a human.

1. Validate `%pr_state%` is `declined` or `merged`; if neither → set `{blocker_summary}` = `"INVALID_PR_STATE: pr_state must be 'declined' or 'merged', got '%pr_state%'"` → Tier 3 blocker, skip to Phase 4.7/4.8 with `status: "1"`.
2. Parse `%pr_url%` to extract `{workspace}`, `{repo_slug}`, `{pr_id}`:
   - Expected pattern: `https://github.org/{workspace}/{repo_slug}/pull-requests/{pr_id}`
   - If parsing fails → set `{blocker_summary}` = `"INVALID_PR_URL: cannot parse workspace/repo_slug/pr_id from '%pr_url%'"` → Tier 3 blocker.
3. Initialize `{blocker_summary}` = `""`, `{critical_count}` = 0, `{high_count}` = 0, `{medium_count}` = 0, `{comment_count}` = 0.
4. If `%pr_state%` == `"merged"`: set `{review_outcome}` = `"pass"`, `{comment_count}` = 0 — skip Phase 3, proceed to Phase 4.
5. If `%pr_state%` == `"declined"`: proceed to Phase 3.

---

## Phase 3: Fetch & Analyze Human Review Comments (YOLO Mode)

**Only runs when `%pr_state%` == `"declined"`.**

### Step 3.1 — Fetch Comments

Run:
```
python3 .claude/skills/zone-human-review/scripts/zone_human_review.py fetch-pr-comments \
  --pr-url %pr_url% --repo-root .
```

Capture JSON output:
- `{comments}` — array of objects with: `id`, `author`, `content`, `inline.path`, `inline.line`, `created_on`
- `{comment_count}` — total comments fetched

If script exits non-zero → set `{blocker_summary}` = `"PR_COMMENTS_FETCH_FAILED: <error from script>"` → Tier 3 blocker, skip to Phase 4.7/4.8 with `status: "1"`.

### Step 3.2 — Categorise Comments (YOLO Mode — no user input)

For each comment in `{comments}`, read `content` and assign a severity using these rules:

| Severity | Criteria |
|----------|----------|
| **CRITICAL** | Security vulnerabilities, authentication bypass, data loss/corruption risk, breaking API contract, hardcoded secrets, SQL injection / XSS / injection risks |
| **HIGH** | Incorrect business logic, missing validation at system boundaries, unhandled error paths that cause silent failures, significant performance issues (N+1, unbounded queries), missing required audit trail |
| **MEDIUM** | Code quality issues, naming convention violations, minor logic issues, missing unit tests for a changed path, refactoring suggestions, style deviations from domain skill standards |
| **Skip** | Purely conversational comments or comments marked as resolved (contain "✓", "fixed", "resolved", "done", "LGTM" with no follow-up concern, or are clearly acknowledging a response) |

Auto-assign; never pause for user input.

### Step 3.3 — Append to Story File

Append to `{story_file_path}` under `### Human Code Review` section (after the last existing `###` review section, or at end of file):

```markdown
### Human Code Review

**Reviewer Comments:** {comment_count} total ({critical_count} CRITICAL, {high_count} HIGH, {medium_count} MEDIUM, {skipped_count} informational/resolved)
**PR:** {pr_url}
**State:** declined

#### Findings

**[{SEVERITY}]** {author}: {content_truncated_200_chars} [{file_path}:{line_or_blank}]
... (one line per categorised comment)
```

Then, under the `Tasks/Subtasks` section of the story file, append action items for CRITICAL, HIGH, and MEDIUM findings:
```markdown
- [ ] [Human-Review][CRITICAL] {short_description} [{file_path}:{line}]
- [ ] [Human-Review][HIGH] {short_description} [{file_path}:{line}]
- [ ] [Human-Review][MEDIUM] {short_description} [{file_path}:{line}]
```

Set `{review_outcome}` = `"fail"` if (critical_count + high_count + medium_count) > 0, else `"pass"`.

Capture final counts: `{critical_count}`, `{high_count}`, `{medium_count}`, `{skipped_count}`.

---

## Phase 4: Commit and Push Super-Repo

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py commit-repo \
  --story-key {story_key} --story-key {github-issues_key} \
  --title "{bmad_title}" --repo-root .
```

Note: The `commit-repo` command uses the commit message `{github-issues_key}: {bmad_title} - code review report`. This skill overrides that to use `human review report` — pass `--title "{bmad_title} - human review"` so the resulting commit message is `{github-issues_key}: {bmad_title} - human review - code review report`. Alternatively, accept the standard suffix from `commit-repo` — the important distinction is captured in the story file content.

Capture JSON output. If `action` is `"skipped"`, no `_bmad-output/` changes were staged — this is not an error.

---

## Phase 4.6: Attach Story File to GitHub Issues (Conditional — PASS only)

**Skip this phase** if `{review_outcome}` != `"pass"`.

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py attach-story \
  --story-key {github-issues_key} --story-file {story_file_path} --repo-root .
```

Best-effort — non-fatal on failure.

---

## Phase 4.7: Post GitHub Issues Comment (Unconditional)

**Always runs.** Best-effort — non-fatal on failure.

**If PASS** (`{review_outcome}` == `"pass"`):

Run:
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ✅ Human Code Review passed

- Story: `{story_key}`
- PR state: {pr_state}
- Comments: CRITICAL={critical_count}, HIGH={high_count}, MEDIUM={medium_count}
- PR: [{pr_url}]({pr_url})
EOF
```

**If FAIL or blocked**:

Run:
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ⚠️ Human Code Review failed

- Story: `{story_key}`
- PR state: declined
- Comments: CRITICAL={critical_count}, HIGH={high_count}, MEDIUM={medium_count}
- PR: [{pr_url}]({pr_url})

{blocker_lines}
EOF
```

Where:
- `{blocker_lines}` = empty string if `{blocker_summary}` is empty, else `## Blockers` followed by `{blocker_summary}` as markdown bullet lines.

---

## Phase 4.8: GitHub Issues Transition (Unconditional)

**Always runs.** Determine `{outcome}`: `blocked` if `{blocker_summary}` is non-empty; `pass` if (critical_count + high_count + medium_count) == 0; `fail` otherwise. Run (best-effort, non-fatal):

```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py transition-github-issues \
  --story-key {github-issues_key} --skill zone-human-review --outcome {outcome} --repo-root .
```

Outcomes (from `workflow-transitions.yaml`):
- `pass` → `"Done"`
- `fail` → `"In Progress"`
- `blocked` → `"Blocked"`

Always proceed to Phase 5.

---

## Phase 5: Output Status

Run:
```
python3 .claude/skills/zone-human-review/scripts/zone_human_review.py status \
  --story-file {story_file_path}
```

The script emits the sentinel line directly:
```
###ZONE-HUMAN-REVIEW-RESULT###{"status":"<0|1>","comment_count":N,"critical":X,"high":Y,"medium":Z}###ZONE-HUMAN-REVIEW-RESULT###
```

---

## Critical Guardrails

| Rule | Detail |
|------|--------|
| YOLO mode | All categorisation decisions auto-made; no user interaction |
| No code fixes | Never modify code; only create action items in the story file |
| No branch checkout | No module operations — story file is the only artifact written |
| Super-repo staging | Never `git add modules/*` — only `_bmad-output/` |
| Commit message | `{github-issues_key}: {bmad_title} - human review report` |
| Severity assignment | AI-assigned based on comment content; CRITICAL/HIGH/MEDIUM only (no LOW) |
| Skip resolved comments | Ignore purely conversational or self-resolved comments |
| CI output | Sentinel `###ZONE-HUMAN-REVIEW-RESULT###...###ZONE-HUMAN-REVIEW-RESULT###` to stdout |
| Merged state | pr_state=merged always PASS; skip Phase 3; no comment fetching |
| GitHub Issues transition | Outcome resolved via workflow-transitions.yaml; best-effort, non-fatal |
| GitHub Issues attachment | Attach story file on PASS only; best-effort, non-fatal |
| Phase 4.7 | **Always runs** — unconditional GitHub Issues comment with ✅/⚠️ result; never skipped |

---

## Key Files Referenced

| Purpose | Path |
|---------|------|
| Human review script | `.claude/skills/zone-human-review/scripts/zone_human_review.py` |
| Shared review script | `.claude/skills/zone-code-review/scripts/zone_review.py` |
| GitHub Issues agile script | `.claude/skills/github-issues-agile/scripts/github-issues_agile.py` |
| Prepare-story script | `.claude/skills/zone-prepare-story/scripts/zone_prepare_story.py` |
| Workflow transitions | `.claude/skills/_common/workflow-transitions.yaml` |
| story key map | `_bmad-output/implementation-artifacts/story-key-map.yaml` |
| Story files | `_bmad-output/implementation-artifacts/stories/{story_key}.md` |
