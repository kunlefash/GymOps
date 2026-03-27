---
name: zone-test-review
description: Headless CI skill that resolves a Jira key to a BMAD story, executes the TEA test-review workflow in YOLO mode, commits/pushes the test quality report, and creates PRs on PASS.
version: 1.0.0
triggers:
  keywords:
    - zone-test-review
    - test-review-ci
    - headless-test-review
  intents:
    - execute_test_review_headless
    - ci_test_review
---

# Zone Test Review — Headless CI Test-Review Skill

Autonomous, CI-friendly skill that takes a Jira key, resolves it to a BMAD story, runs the full TEA `testarch-test-review` workflow without user interaction, and commits results to the appropriate branch of the super repo.

**Input**: `%jira_key%` (e.g. `BMAD-152`)
**Output**: `###ZONE-TEST-REVIEW-RESULT###{"status":"0","score":N,"grade":"X","recommendation":"..."}###ZONE-TEST-REVIEW-RESULT###` on PASS (recommendation = Approve or Approve with Comments), `###ZONE-TEST-REVIEW-RESULT###{"status":"1",...}###ZONE-TEST-REVIEW-RESULT###` on FAIL.

**NOTE**: When working with submodules, you should spawn subagents per submodule/repo to perform tasks. This will greatly improve speed.

---

## Pre-Warm Mode

If this prompt contains `PHASES 0-2 PRE-RESOLVED`, the pipeline has already
executed Phases 0-2.5. In this case:

1. **Skip Phases 0, 1, 2, 2.5** — do NOT run sync-superrepo, resolve,
   prepare-branches, or read domain skill files.
2. **Extract session variables** from the JSON in `PHASES 0-2 PRE-RESOLVED`:
   - `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_branch}`,
     `{story_file_path}`, `{jira_key}`, `{epic_branch}`, `{epic_key}`, `{parent_jira_key}`, etc.
3. **Internalize domain skills** from the `DOMAIN SKILLS` section.
4. If `prewarm_status` is `"partial"`, review `prepare_branches` output for
   errors and work with successfully prepared submodules only.
5. **Begin at Phase 3** (the test review phase).

If no `PHASES 0-2 PRE-RESOLVED` marker exists, execute all phases from Phase 0.

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py sync-superrepo --repo-root .
```

Pulls the latest super-repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**HALT protocol (Phase 0 failure):** If exit code is non-zero, set `{blocker_summary}` to `"SYNC_FAILED: super-repo sync failed — branch may be behind or have conflicts"`, then run Phase 4.7 (unconditional Jira comment) and Phase 4.8 (Jira transition to Blocked) using `%jira_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.


---

## Phase 0.5: Pre-Execution Workspace Check

Before any submodule operations, verify the workspace is clean:
```
git status --porcelain
```

Evaluate the output **only** for pre-existing dirty state that this skill did not cause:
- If `modules/*` entries appear as modified **AND** Phase 2 `prepare-branches` has NOT yet run in this session → genuine blocker.
- If `.log` files appear at repo root → genuine blocker (stale CI artefacts from a previous run).

**If a genuine pre-existing blocker is found**: set `{blocker_summary}` = `"WORKSPACE_DIRTY: unexpected pre-existing dirty state before Phase 2 — <list of dirty paths>"`, then run Phase 4.7 (unconditional Jira comment) and Phase 4.8 (Jira transition to Blocked) using `%jira_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.

**YOLO mode**: Never ask the user about dirty state — classify automatically and either continue or halt per the rules above.

---

## Phase 1: Resolve Jira Key to Story

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py resolve \
  --jira-key %jira_key% --repo-root .
```

Capture JSON output as session variables: `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_branch}`, `{story_file_path}`, `{jira_key}`.
If the output includes `epic_branch`, also capture `{epic_branch}`, `{epic_key}`, `{parent_jira_key}` — these are used in Phase 4.5 for PR creation.
**HALT protocol (Phase 1 failure):** If exit code is non-zero, classify the blocker from the script's error output:
- `KEY_NOT_FOUND` — Jira key not present in `jira-key-map.yaml`
- `STORY_FILE_MISSING` — story file not found (story not yet prepared by zone-prepare-story)
- `INVALID_STATUS` — story is not in a reviewable status
- `SPRINT_STATUS_MISSING` — `sprint-status.yaml` absent or malformed

Set `{blocker_summary}` to `"<BLOCKER_TYPE>: <error message from script>"`, then run Phase 4.7 (unconditional Jira comment) and Phase 4.8 (Jira transition to Blocked) using `%jira_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 2.


---

## Phase 2: Checkout Submodule Story Branches

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py prepare-branches \
  --story-file {story_file_path} --story-branch {story_branch} --checkout-only --repo-root .
```

Capture JSON output. Also capture `{domain_skills}` — the list of domain skill objects resolved from the checked-out submodules. Capture `{submodules_json}` as the `submodules` field (JSON array). Initialize `{blocker_summary}` as empty string.

Verify at least one submodule has `status` in `checked_out_remote` or `checked_out_local`. If **all** submodules are `skipped` or `error` (no tests to review):
- **Tier 3 ESCALATE-JIRA**: classify blocker as `BRANCH_NOT_FOUND`, list the missing branches per submodule.
- Append to `{blocker_summary}`: e.g., `BRANCH_NOT_FOUND: story branch '{story_branch}' not found in any submodule (checked: <list>)`.
- Skip Phases 2.5, 3, 4 — proceed directly to Phase 4.7 with `status: "1"`.

**Checkout only**: Branches are never created; only existing branches (remote or local) are checked out. Submodules where the story branch does not exist are skipped with `status: "skipped"`. If at least one submodule was checked out, proceed to Phase 2.5.

**E2E/API test repo**: `zoneqa_automation` is automatically included in the checkout list by `zone_review.py` when any story-referenced module is a testable source module. This ensures E2E and API tests written by `zone-qa` into `tests/cardless/pwa/` and `tests/cardless/api/` are checked out and available for review. Its entry will have `"role": "e2e_test_repo"` in the Phase 2 output.

**Expected dirty state**: After `prepare-branches` runs, `git status` on the super-repo will show checked-out submodule directories as modified (e.g., `M modules/zone.framework`). This is expected. Do NOT treat this as a blocker. Phase 4's `commit-superrepo` script handles cleanup via `git reset HEAD modules/`.

---

## Phase 2.5: Load Domain Skills

For each entry in `{domain_skills}` where `exists` is `true`:
1. Read the SKILL.md file at the entry's `path`.
2. Internalize the coding standards, architectural patterns, and conventions described.
3. **Context budget rule**: Only load each skill's main `SKILL.md` — do NOT pre-load referenced sub-documents. Load those on-demand during Phase 3 if a specific review task needs them.

If `{domain_skills}` is empty (no mappings found or map file missing), proceed to Phase 3 without loading any domain skills.

---

## Phase 3: Execute TEA Test Review Workflow (YOLO Mode)

Invoke the **bmad-tea-testarch-test-review** workflow. The test-review workflow validates test quality against best practices and produces a findings report.

1. **Load config** — read `_bmad/tea/config.yaml`; capture `{user_name}`, `{communication_language}`, `{output_folder}`, `{test_artifacts}` as session variables.
2. **Load the BMAD workflow engine**: `_bmad/core/tasks/workflow.xml` — read its entire contents.
3. **Pass workflow config**: `_bmad/tea/workflows/testarch/test-review/workflow.yaml` as `workflow-config`.
4. **Set context**:
   - `story_path` = `{story_file_path}`
   - `review_scope = "directory"` (review all test files changed in story branch per submodule)
   - `test_stack_type = "auto"`
5. **E2E/API test review context**: When the TEA workflow reviews test files in `zoneqa_automation` (identified by `"role": "e2e_test_repo"` in the Phase 2 output), apply `zone-qa-automation` conventions (loaded in Phase 2.5) as the quality baseline. Specifically validate:
   - Page objects extend `BasePage` from `pageObjectClass/basePage.js`
   - API tests use `getHeadersForBank(request, institution)` — never inline token fetch
   - Tests use multi-institution loops (`BANKA`/`BANKB`/`OFI`) for cross-tenant coverage
   - File naming follows `camelCase.spec.js`
   - Locators use `.first()` on ambiguous queries
   - `this.waitAndClick()` / `this.waitAndFill()` used — no bare `.click()`
   - E2E tests live in `tests/cardless/pwa/`; API tests in `tests/cardless/api/`

   Violations of these conventions should be reported as MEDIUM or HIGH findings.
6. **Execute** all workflow steps without pausing (YOLO mode).
7. **After workflow**, read the generated report at `{test_artifacts}/test-review.md`. Parse:
   - `**Recommendation**:` → `{recommendation}` (Approve | Approve with Comments | Request Changes | Block)
   - `**Quality Score**:` → `{score}/100`, `{grade}`
   - Violation counts from `**Total Violations**:` line → `{critical_count}`, `{high_count}`, `{medium_count}`, `{low_count}`
8. **Append** to story file at `{story_file_path}` under `### Test Quality Review (AI)`:
   ```
   **Test Review Recommendation:** {recommendation}
   **Quality Score:** {score}/100 (Grade: {grade})
   **Violations:** Critical={critical_count}, High={high_count}, Medium={medium_count}, Low={low_count}
   ```
   Then add action items for CRITICAL and HIGH violations as `- [ ] [AI-Test-Review][Severity] Description [file:line]` under Tasks/Subtasks.

**YOLO mode — report and track** (these override ALL workflow prompts and interactive steps):
- Skip ALL user confirmations — auto-approve every gate.
- **No fixes**: NEVER fix issues in the tests. Only report findings and create action items for tracking.
- Never pause for user input. Drive all choices toward completion.
- If a submodule was skipped in Phase 2 (branch not found), review the submodules that were checked out; do not HALT.

**HALT protocol**:

| Tier | Condition | Action |
|------|-----------|--------|
| **Tier 1** — Submodule-level failures | Individual submodule test discovery fails | Retry once; if still failing, skip that submodule with log; continue reviewing remaining submodules |
| **Tier 3** — Fundamental blockers | Story file unreadable or all submodules skipped | ESCALATE-JIRA immediately — classify blocker (`STORY_FILE_MISSING \| BRANCH_NOT_FOUND`), append to `{blocker_summary}`, skip to Phase 4.7 with `status: "1"` |

---

## Phase 4: Commit and Push Super-Repo

Run:
```
python3 .claude/skills/zone-test-review/scripts/zone_test_review.py commit-superrepo \
  --story-key {story_key} --jira-key {jira_key} \
  --title "{bmad_title}" --repo-root .
```

Capture JSON output. If `action` is `"skipped"`, no `_bmad-output/` changes were staged — this is not an error.

---

## Phase 4.5: Create Pull Requests (Conditional — PASS only)

PASS = `{recommendation}` is "Approve" or "Approve with Comments". If the recommendation is anything else, skip to Phase 4.6.

If `{epic_branch}` was not resolved in Phase 1 (e.g., bug fix stories with no parent epic), pass `--epic-branch ""` — the script resolves the target branch per-submodule from `.gitmodules` (default: `development`).

If the review PASSES, run:
```
python3 .claude/skills/zone-test-review/scripts/zone_test_review.py create-pullrequests \
  --story-branch {story_branch} --epic-branch "{epic_branch}" \
  --jira-key {jira_key} --title "{bmad_title}" \
  --submodules '{submodules_json}' --story-file {story_file_path} --repo-root .
```

Where `{submodules_json}` is the JSON array from Phase 2 output (`submodules` field). Escape it as a single-quoted JSON string.

Capture JSON output. Log the `created_count`, `error_count`, and `skipped_count`. Capture `{pr_url}` from the first `pr_url` in `results` where `status` is `"created"` or `"already_exists"`. PR creation errors are non-fatal — always proceed to Phase 4.6.

**PR description**: The full content of `{story_file_path}`, read raw, truncated to 64 KB for Bitbucket API limits. This differs from zone-code-review's extracted-sections approach.

---

## Phase 4.6: Attach Files to Jira

### Phase 4.6a — Attach Story File (Conditional — PASS only)

**Skip this sub-step** if review did not PASS (recommendation is not Approve or Approve with Comments).

Run (best-effort, non-fatal):
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py attach-story \
  --jira-key {jira_key} --story-file {story_file_path} --repo-root .
```

### Phase 4.6b — Attach Test-Review Report (Unconditional)

**Always runs** — regardless of PASS/FAIL. Best-effort, non-fatal.

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py attach-story \
  --jira-key {jira_key} --story-file {test_artifacts}/test-review.md --repo-root .
```

Set `{test_review_attachment_name}` = `test-review.md` on success, empty string on failure or skip.

---

## Phase 4.7: Post Jira Review Result Comment (Unconditional)

**Always runs** — regardless of PASS/FAIL, skipped phases, or Tier 3 blockers. Best-effort, non-fatal.

Determine `{status_emoji}` and `{status_word}`:
- PASS (recommendation = Approve or Approve with Comments, no Tier 3 blockers): `{status_emoji}` = ✅, `{status_word}` = "passed"
- FAIL or blocked: `{status_emoji}` = ⚠️, `{status_word}` = "failed"

**Extract `{test_review_executive_summary}`**: Read `{test_artifacts}/test-review.md` and extract the content of the `## Executive Summary` section — everything under that heading up to (but not including) the next `##` heading. Truncate to 32 KB if longer. If the file is unreadable or the section is absent, set to empty string.

Run:
```
python3 .claude/skills/jira-agile/scripts/jira_agile.py add-comment {jira_key} \
  --format markdown --body-stdin <<'EOF'
### {status_emoji} AI Test Review {status_word}

- Story: `{story_key}`
- Score: {score}/100 (Grade: {grade})
- Recommendation: {recommendation}
- Test review report: `{test_review_attachment_name}`
{story_report_line}
{pr_url_line}

{test_review_executive_summary}

{blocker_lines}
EOF
```

Where:
- `{story_report_line}` = `- Final story report: \`story_report_{story_stem}.md\`` if review PASSED; omit otherwise. `{story_stem}` is the story file name without extension (derived from `{story_file_path}`).
- `{pr_url_line}` = `- PR: [Open pull request]({pr_url})` if review PASSED and PRs were created; omit otherwise.
- `{test_review_attachment_name}` = `test-review.md` (or empty string if Phase 4.6b was skipped/failed).
- `{blocker_lines}` = empty string if `{blocker_summary}` is empty, else:
  `## Blockers` followed by `{blocker_summary}` as markdown bullet lines.
- Score/grade/recommendation are parsed from the story file's `### Test Quality Review (AI)` section (or defaults of `0`/`-`/`unknown` if review was skipped/blocked).

**Best-effort**: log warning if comment fails, do NOT fail the skill.

---

## Phase 4.8: Jira Transition (Unconditional)

**Always runs**. Determine `{outcome}`: `blocked` if `{blocker_summary}` is non-empty; `pass` if recommendation is "Approve" or "Approve with Comments"; `fail` otherwise. Run (best-effort, non-fatal):
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py transition-jira \
  --jira-key {jira_key} --skill zone-test-review --outcome {outcome} --repo-root .
```

---

## Phase 5: Output Status

Run:
```
python3 .claude/skills/zone-test-review/scripts/zone_test_review.py status \
  --story-file {story_file_path}
```

The script emits the sentinel line directly:
```
###ZONE-TEST-REVIEW-RESULT###{"status":"<0|1>","score":<N>,"grade":"<X>","recommendation":"<...>"}###ZONE-TEST-REVIEW-RESULT###
```

**Status criteria**: `"0"` (PASS) = recommendation is "Approve" or "Approve with Comments"; `"1"` (FAIL) = otherwise or section missing.

---

## Critical Guardrails

| Rule | Detail |
|------|--------|
| YOLO mode | All workflow confirmations auto-approved; all choices drive toward completion |
| No test fixes | NEVER fix issues in tests; report findings AND create action items for CRITICAL/HIGH violations |
| Checkout only | NEVER create submodule branches; only checkout existing branches (remote or local) |
| Submodule checkout first | Checkout story branches in referenced submodules BEFORE the test-review workflow runs |
| Submodule init | Only initialize submodules that the story file references in Tasks/Subtasks |
| Super-repo branch | NEVER create a new branch or checkout another branch — stay on current branch |
| Super-repo staging | NEVER `git add` any `modules/*` paths — only `_bmad-output/` artifacts |
| Headless/CI | Zero user interaction — all decisions automated — JSON-only final output |
| Commit message | Always use the format: `{jira_key}: {bmad_title} - test review report` |
| Git PUSH | Ensure all local commits are pushed automatically. No further instructions required |
| CI output | Result emitted as `###ZONE-TEST-REVIEW-RESULT###...###ZONE-TEST-REVIEW-RESULT###` sentinel in stdout — TeamCity greps for it |
| Status criteria | Status `"0"` = PASS (recommendation = Approve or Approve with Comments); `"1"` = FAIL |
| review_scope | Always `"directory"` — review all test files in story branch per submodule |
| Test report path | `{test_artifacts}/test-review.md` per TEA workflow config |
| PR creation | Only create PRs when recommendation = Approve/Approve with Comments; targets epic_branch if available, otherwise submodule default branch |
| PR description | Full story file content (raw), truncated to 64 KB |
| PR auth | Prefers `BB_EMAIL` + `BB_API_TOKEN` (API token auth); falls back to legacy `BB_USERNAME` + `BB_APP_PASSWORD`; skips gracefully if neither is configured |
| Jira transition | Outcome resolved via workflow-transitions.yaml; best-effort, non-fatal |
| Jira attachment | Attach story file AND test-review.md; both best-effort (non-fatal) |
| Phase 4.7 | **Always runs** — unconditional Jira comment with ✅/⚠️ review result; runs before Phase 4.8 transition; never skipped |
| Blocker summary | `{blocker_summary}` initialized in Phase 2; appended by Tier 3 ESCALATE-JIRA events; posted to Jira in Phase 4.7 |
| Expected dirty submodule state | After Phase 2, `git status` will show `M modules/<name>` — this is intentional. Never treat this as a blocker or ask the user; continue to Phase 2.5 |

---

## Key Files Referenced

| Purpose | Path |
|---------|------|
| Test review script | `.claude/skills/zone-test-review/scripts/zone_test_review.py` |
| Shared review script | `.claude/skills/zone-code-review/scripts/zone_review.py` |
| Jira key map | `_bmad-output/implementation-artifacts/jira-key-map.yaml` |
| Story files | `_bmad-output/implementation-artifacts/stories/{story_key}.md` |
| Sprint status | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| TEA config | `_bmad/tea/config.yaml` |
| Workflow engine | `_bmad/core/tasks/workflow.xml` |
| Test-review workflow | `_bmad/tea/workflows/testarch/test-review/workflow.yaml` |
| Test review report | `{test_artifacts}/test-review.md` |
| Submodule→skill map | `.claude/skills/zone-test-review/submodule-skill-map.yaml` |
| Domain skills | `.claude/skills/{skill-name}/SKILL.md` (loaded dynamically in Phase 2.5) |
