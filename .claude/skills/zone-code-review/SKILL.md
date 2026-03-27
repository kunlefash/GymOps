---
name: zone-code-review
description: Headless CI skill that resolves a Jira key to a BMAD story, executes the code-review workflow in YOLO mode, and commits/pushes the report to super-repo without fixing them.
version: 2.0.0
triggers:
  keywords:
    - zone-code-review
    - code-review-ci
    - headless-code-review
  intents:
    - execute_code_review_headless
    - ci_code_review
---

# Zone Code Review — Headless CI Code-Review Skill

Autonomous, CI-friendly skill that takes a Jira key, resolves it to a BMAD story, runs the full code-review workflow without user interaction, and commits results to the appropriate branch of the super repo.

**Input**: `%jira_key%` (e.g. `BMAD-152`)
**Output**: `###ZONE-REVIEW-RESULT###{"status":"0","unchecked":0}###ZONE-REVIEW-RESULT###` on PASS (no CRITICAL/HIGH/MEDIUM issues), `###ZONE-REVIEW-RESULT###{"status":"1","unchecked":N}###ZONE-REVIEW-RESULT###` on FAIL (unchecked issues or review incomplete).

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
5. **Begin at Phase 3** (the review phase).

If no `PHASES 0-2 PRE-RESOLVED` marker exists, execute all phases from Phase 0.

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py sync-superrepo --repo-root .
```

Pulls the latest super-repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**HALT protocol (Phase 0 failure):** If exit code is non-zero, set `{blocker_summary}` to `"SYNC_FAILED: super-repo sync failed — branch may be behind or have conflicts"`, then run Phase 4.8 (Jira transition to Blocked) and Phase 4.9 (unconditional Jira comment) using `%jira_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.


---

## Phase 0.5: Pre-Execution Workspace Check

Before any submodule operations, verify the workspace is clean:
```
git status --porcelain
```

Evaluate the output **only** for pre-existing dirty state that this skill did not cause:
- If `modules/*` entries appear as modified **AND** Phase 2 `prepare-branches` has NOT yet run in this session → genuine blocker.
- If `.log` files appear at repo root → genuine blocker (stale CI artefacts from a previous run).

**If a genuine pre-existing blocker is found**: set `{blocker_summary}` = `"WORKSPACE_DIRTY: unexpected pre-existing dirty state before Phase 2 — <list of dirty paths>"`, then run Phase 4.8 (Jira transition to Blocked) and Phase 4.9 (unconditional Jira comment) using `%jira_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.

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

Set `{blocker_summary}` to `"<BLOCKER_TYPE>: <error message from script>"`, then run Phase 4.8 (Jira transition to Blocked) and Phase 4.9 (unconditional Jira comment) using `%jira_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 2.


---

## Phase 2: Checkout Submodule Story Branches

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py prepare-branches \
  --story-file {story_file_path} --story-branch {story_branch} --checkout-only --repo-root .
```

Capture JSON output. Also capture `{domain_skills}` — the list of domain skill objects resolved from the checked-out submodules. Initialize `{blocker_summary}` as empty string.

Verify at least one submodule has `status` in `checked_out_remote` or `checked_out_local`. If **all** submodules are `skipped` or `error` (no code to review):
- **Tier 3 ESCALATE-JIRA**: classify blocker as `BRANCH_NOT_FOUND`, list the missing branches per submodule.
- Append to `{blocker_summary}`: e.g., `BRANCH_NOT_FOUND: story branch '{story_branch}' not found in any submodule (checked: <list>)`.
- Skip Phases 2.5, 3, 3.5, 4 — proceed directly to Phase 4.9 with `status: "1"`.

**Checkout only**: Branches are never created; only existing branches (remote or local) are checked out. Submodules where the story branch does not exist are skipped with `status: "skipped"`. If at least one submodule was checked out, proceed to Phase 2.5.

**Expected dirty state**: After `prepare-branches` runs, `git status` on the super-repo will show checked-out submodule directories as modified (e.g., `M modules/zone.framework`). This is expected — the submodule pointer has moved from the recorded super-repo commit to the story branch HEAD. Do NOT treat this as a blocker or pause for user input. Phase 4's `commit-superrepo` script handles cleanup via `git reset HEAD modules/`.

---

## Phase 2.5: Load Domain Skills

For each entry in `{domain_skills}` where `exists` is `true`:
1. Read the SKILL.md file at the entry's `path`.
2. Internalize the coding standards, architectural patterns, and conventions described.
3. **Context budget rule**: Only load each skill's main `SKILL.md` — do NOT pre-load referenced sub-documents or supplementary files. Load those on-demand during Phase 3 when a specific review task needs them.

If `{domain_skills}` is empty (no mappings found or map file missing), proceed to Phase 3 without loading any domain skills.

---

## Phase 2.7: Auto-Fix Story File List Discrepancies

Before the code-review workflow runs, pre-reconcile the story's `### File List` with actual git changes so that bookkeeping gaps never reach the adversarial reviewer:

1. For each submodule checked out in Phase 2, collect changed file paths:
   ```
   git diff --name-only {epic_branch}...{story_branch} -- .
   ```
   (Run inside each submodule directory. If `{epic_branch}` is not available, use the submodule's default branch.)

2. Read the story file at `{story_file_path}` and parse the `### File List` section.

3. For each file in the git diff that is NOT already in the File List:
   - Normalize the path (strip leading `./`, redundant separators)
   - Deduplicate against existing entries by normalized path
   - Append `- {path}` as a new bullet under `### File List`

4. Track all auto-added files in `{auto_fixed_files}` (list of paths).

5. If any files were auto-added, append a `### Auto-Resolved Reporting Discrepancies` section to the story file (after `### File List`, before any review sections):
   ```
   ### Auto-Resolved Reporting Discrepancies
   The following files were present in git diff but missing from the Dev Agent Record File List.
   They were auto-added before code review and are excluded from issue counts:
   - path/to/file1
   - path/to/file2
   ```

6. Do NOT auto-fix the reverse case: if the File List claims a file but git has no evidence, leave it — the workflow will correctly flag it as HIGH (false claim).

7. Save the story file. Proceed to Phase 3.

---

## Phase 3: Execute Code-Review Workflow (YOLO Mode)

Invoke the **bmad-bmm-code-review** command flow. The code-review workflow validates story claims against implementation and produces a findings report — **report only, no fixes**.

1. **Load config** — read `_bmad/bmm/config.yaml`; store `{user_name}`, `{communication_language}`, `{output_folder}` as session variables.
2. **Load the BMAD workflow engine**: `_bmad/core/tasks/workflow.xml` — read its entire contents.
3. **Pass workflow config**: `_bmad/bmm/workflows/4-implementation/code-review/workflow.yaml` as `workflow-config`.
4. **Set story path**: `story_path` / `story_file` = `_bmad-output/implementation-artifacts/stories/{story_key}.md`
5. **Apply domain skills** — use the standards loaded in Phase 2.5 to validate code against conventions (e.g., zone-dotnet, zone-frontend). The adversarial reviewer must challenge implementation against these standards.
6. **Execute** all steps (1 through 5) of the code-review `instructions.xml` (`_bmad/bmm/workflows/4-implementation/code-review/instructions.xml`) without pausing.

**YOLO mode — report and track** (these override ALL workflow prompts and interactive steps):
- Skip ALL user confirmations — auto-approve every gate.
- **No code fixes**: NEVER fix application code. Only report findings and create action items for tracking.
- **File List discrepancy override**: "Files changed but not in story File List" findings from the workflow's Step 3 item 1 are pre-resolved by Phase 2.7 — if the workflow still raises any as MEDIUM, do NOT count them toward issue totals, do NOT create action items for them, and do NOT include them in `**Issues Found:**` counts. They are already logged under `### Auto-Resolved Reporting Discrepancies`.
- At Step 4 (Present findings): Skip the interactive `<ask>` and auto-select **option 2** ("Create action items"). Output the findings report (CRITICAL/HIGH/MEDIUM/LOW sections) and append to the story under "Senior Developer Review (AI)". Then add "Review Follow-ups (AI)" subsection to Tasks/Subtasks with each CRITICAL, HIGH, and MEDIUM finding as: `- [ ] [AI-Review][Severity] Description [file:line]`. Skip LOW findings (informational only). Exclude auto-resolved File List discrepancies from action items. Set `fixed_count = 0`, `action_count = number of action items created`. Proceed to Step 5.
- Never pause for user input. Drive all choices toward completion.
- If a submodule was skipped in Phase 2 (branch not found), review the submodules that were checked out; do not HALT.

**HALT protocol** — two tiers (code-review never fixes code, so no Tier 2):

| Tier | Condition | Action |
|------|-----------|--------|
| **Tier 1** — Submodule-level failures | Individual git command fails or diff parsing errors for a specific submodule | Retry once; if still failing, skip that submodule with log; continue reviewing remaining submodules |
| **Tier 3** — Fundamental blockers | Story file inaccessible or unreadable; all submodules skipped (handled in Phase 2) | ESCALATE-JIRA immediately — classify blocker (`STORY_FILE_MISSING \| BRANCH_NOT_FOUND`), append to `{blocker_summary}`, skip to Phase 4.9 with `status: "1"` |

---

## Phase 3.5: Edge Case Analysis (Informational)

After the code-review workflow completes, run an edge-case analysis on the diff of changed files per submodule.

1. For each submodule checked out in Phase 2, collect the diff:
   ```
   git diff {epic_branch}...{story_branch} -- .
   ```
   (Run inside each submodule directory. If `{epic_branch}` is not available, use the submodule's default branch.)

2. Feed each diff into the edge-case-hunter task:
   - Load `_bmad/core/tasks/review-edge-case-hunter.xml` — read its entire contents.
   - Execute the task with the diff as input content.
   - Collect the JSON findings output.

3. Append findings to the story file at `{story_file_path}` under a new `### Edge Case Analysis` section (after "Senior Developer Review (AI)" if present, otherwise at the end of the file).

4. **Informational only** — edge-case findings do NOT affect the PASS/FAIL gate. They are advisory context for the developer.

5. If the edge-case-hunter produces no findings or errors, skip appending and proceed to Phase 4.

---

## Phase 4: Commit and Push Super-Repo

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py commit-superrepo \
  --story-key {story_key} --jira-key {jira_key} \
  --title "{bmad_title}" --repo-root .
```

Capture JSON output. If `action` is `"skipped"`, no _bmad-output/ changes were staged — this is not an error.

---

## Phase 4.6: Attach Story File to Jira (Conditional — PASS only)

**Skip this phase** if review did not PASS (CRITICAL + HIGH + MEDIUM > 0).

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py attach-story \
  --jira-key {jira_key} --story-file {story_file_path} --repo-root .
```

Attaches the story file to the Jira issue with filename `story_report_{story_stem}.md` where `{story_stem}` is the story file name without extension. Best-effort — non-fatal on failure.

---

## Phase 4.7: Post Jira Comment (Unconditional)

**Always runs**. Best-effort — non-fatal on failure.

**Before the PASS/FAIL branch**, set `{code_review_report_body}` to the findings output generated during Phase 3 of this session — specifically the CRITICAL/HIGH/MEDIUM/LOW sections and action items written to `### Senior Developer Review (AI)` by the current run of the code-review workflow. Use the in-session output directly rather than re-reading the accumulated file section, to avoid including findings from prior review runs on the same story. Truncate to Jira's comment size limit (~32 KB) if needed. If no findings were produced in this session, set to empty string.

**If PASS** (CRITICAL + HIGH + MEDIUM = 0 and no Tier 3 blockers):

Run:
```
python3 .claude/skills/jira-agile/scripts/jira_agile.py add-comment {jira_key} \
  --format markdown --body-stdin <<'EOF'
### ✅ AI Code Review passed

- Story: `{story_key}`
- Issues: CRITICAL={critical_count}, HIGH={high_count}, MEDIUM={medium_count}, LOW={low_count}
- Story file: `{story_file_path}`
- Final story report: `story_report_{story_stem}.md`

{code_review_report_body}
EOF
```

Where `{story_stem}` is the story file name without extension (derived from `{story_file_path}`).

**If FAIL or blocked**:

Run:
```
python3 .claude/skills/jira-agile/scripts/jira_agile.py add-comment {jira_key} \
  --format markdown --body-stdin <<'EOF'
### ⚠️ AI Code Review failed

- Story: `{story_key}`
- Issues: CRITICAL={critical_count}, HIGH={high_count}, MEDIUM={medium_count}, LOW={low_count}

{code_review_report_body}

{blocker_lines}
EOF
```

Where:
- `{blocker_lines}` = empty string if `{blocker_summary}` is empty, else `## Blockers` followed by `{blocker_summary}` as markdown bullet lines.
- Issue counts are parsed from the story file's `**Issues Found:**` line (or 0 if review was skipped/blocked).

---

## Phase 4.8: Jira Transition (Unconditional)

**Always runs**. Determine `{outcome}`: `blocked` if `{blocker_summary}` is non-empty; `pass` if CRITICAL + HIGH + MEDIUM = 0; `fail` otherwise. Run (best-effort, non-fatal):
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py transition-jira \
  --jira-key {jira_key} --skill zone-code-review --outcome {outcome} --repo-root .
```

Always proceed to Phase 5.

---

## Phase 5: Output Status

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py status \
  --story-file {story_file_path}
```

The script emits the sentinel line directly:
```
###ZONE-REVIEW-RESULT###{"status":"<0|1>","unchecked":<N>}###ZONE-REVIEW-RESULT###
```

---

## Critical Guardrails

| Rule | Detail |
|------|--------|
| YOLO mode | All workflow confirmations auto-approved; all choices drive toward completion |
| No code fixes | NEVER fix application code; report findings AND create action items for CRITICAL/HIGH/MEDIUM issues. EXCEPTION: auto-add git-diff files missing from story File List in Phase 2.7 (bookkeeping only, before workflow runs) |
| Checkout only | NEVER create submodule branches; only checkout existing branches (remote or local) |
| Submodule checkout first | Checkout story branches in referenced submodules BEFORE the code-review workflow runs |
| Submodule init | Only initialize submodules that the story file references in Tasks/Subtasks |
| Super-repo branch | NEVER create a new branch or checkout another branch — stay on current branch |
| Super-repo staging | NEVER `git add` any `modules/*` paths — only `_bmad-output/` artifacts |
| Headless/CI | Zero user interaction — all decisions automated — JSON-only final output |
| Commit message | Always use the format: `{jira_key}: {bmad_title} - code review report` |
| Git PUSH | Ensure all local commits are pushed automatically. No further instructions required |
| CI output | Result emitted as `###ZONE-REVIEW-RESULT###...###ZONE-REVIEW-RESULT###` sentinel in stdout — TeamCity greps for it |
| Status criteria | Status `"0"` = PASS (no CRITICAL/HIGH/MEDIUM issues); `"1"` = FAIL (unchecked > 0 or review incomplete). `unchecked` = CRITICAL + HIGH + MEDIUM count. Auto-resolved File List discrepancies (Phase 2.7) are excluded from all counts |
| Jira transition | Outcome resolved via workflow-transitions.yaml; best-effort, non-fatal |
| Jira attachment | Attach story file as `story_report_{stem}.md`; best-effort (non-fatal) |
| Phase 4.6/4.7 | Run only when review PASSES (CRITICAL + HIGH + MEDIUM = 0) |
| Phase 4.9 | **Always runs** — unconditional Jira comment with ✅/⚠️ review result; never skipped |
| Blocker summary | `{blocker_summary}` initialized in Phase 2; appended by Tier 3 ESCALATE-JIRA events; posted to Jira in Phase 4.9 |
| Expected dirty submodule state | After Phase 2, `git status` will show `M modules/<name>` — this is intentional (submodule checked out to story branch). Never treat this as a blocker or ask the user; continue to Phase 2.5 |

---

## Key Files Referenced

| Purpose | Path |
|---------|------|
| Automation script | `.claude/skills/zone-code-review/scripts/zone_review.py` |
| Jira key map | `_bmad-output/implementation-artifacts/jira-key-map.yaml` |
| Story files | `_bmad-output/implementation-artifacts/stories/{story_key}.md` |
| Sprint status | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| BMAD config | `_bmad/bmm/config.yaml` |
| Workflow engine | `_bmad/core/tasks/workflow.xml` |
| Code-review workflow | `_bmad/bmm/workflows/4-implementation/code-review/workflow.yaml` |
| Code-review instructions | `_bmad/bmm/workflows/4-implementation/code-review/instructions.xml` |
| Code-review command | `.claude/commands/bmad-bmm-code-review.md` |
| Submodule→skill map | `.claude/skills/zone-code-review/submodule-skill-map.yaml` |
| Edge-case-hunter task | `_bmad/core/tasks/review-edge-case-hunter.xml` |
| Domain skills | `.claude/skills/{skill-name}/SKILL.md` (loaded dynamically in Phase 2.5) |
