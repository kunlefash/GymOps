---
name: zone-dev
description: Headless CI skill that resolves a story key to a BMAD story, executes the dev-story workflow in YOLO mode, and commits/pushes changes per sub-repo and repo.
version: 2.0.0
triggers:
  keywords:
    - zone-dev
    - dev-story-ci
    - headless-dev
  intents:
    - execute_dev_story_headless
    - ci_dev_story
---

# Zone Dev — Headless CI Dev-Story Skill

Autonomous, CI-friendly skill that takes a story key, resolves it to a BMAD story, runs the full dev-story workflow without user interaction, and commits results to the appropriate branches.

**Input**: `%github-issues_key%` (e.g. `BMAD-152`)
**Output**: `###ZONE-DEV-RESULT###{"status":"0","unchecked":0}###ZONE-DEV-RESULT###` on success, `###ZONE-DEV-RESULT###{"status":"1","unchecked":N}###ZONE-DEV-RESULT###` on failure.

**NOTE**: When working on multiple modules, you should dispatch the tasks to subagents per module/repo. This will greatly improve speed.

---

## Pre-Warm Mode

If this prompt contains `PHASES 0-2 PRE-RESOLVED`, the pipeline has already
executed Phases 0-2.5. In this case:

1. **Skip Phases 0, 1, 2, 2.5** — do NOT run sync-repo, resolve,
   prepare-branches, or read domain skill files.
2. **Extract session variables** from the JSON in `PHASES 0-2 PRE-RESOLVED`:
   - `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_branch}`,
     `{story_file_path}`, `{github-issues_key}`, `{epic_branch}`, `{initiative_branch}`, etc.
3. **Internalize domain skills** from the `DOMAIN SKILLS` section.
4. If `prewarm_status` is `"partial"`, review `prepare_branches` output for
   errors and work with successfully prepared modules only.
5. **Begin at Phase 3** (or the first non-preparation phase).

If no `PHASES 0-2 PRE-RESOLVED` marker exists, execute all phases from Phase 0.

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py sync-repo --repo-root .
```

Pulls the latest repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**HALT protocol (Phase 0 failure):** If exit code is non-zero, set `{blocker_summary}` to `"SYNC_FAILED: repo sync failed — branch may be behind or have conflicts"`, then run Phase 4.5 (post blocked GitHub Issues comment) and Phase 5.5 (GitHub Issues transition to Blocked) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.


---

## Phase 1: Resolve GitHub Issues Key to Story

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py resolve \
  --story-key %github-issues_key% --repo-root .
```

Capture JSON output as session variables: `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_branch}`, `{story_file_path}`, `{github-issues_key}`, `{epic_branch}`, `{parent_github-issues_key}`, `{initiative_branch}`.
**HALT protocol (Phase 1 failure):** If exit code is non-zero, classify the blocker from the script's error output:
- `KEY_NOT_FOUND` — story key not present in `story-key-map.yaml`
- `STORY_FILE_MISSING` — story file path resolved but file does not exist (story not yet prepared)
- `INVALID_STATUS` — story is not in an actionable status for dev (e.g. already `done` or `in-review`)
- `SPRINT_STATUS_MISSING` — `sprint-status.yaml` is absent or malformed

Set `{blocker_summary}` to `"<BLOCKER_TYPE>: <error message from script>"`, then run Phase 4.5 (post blocked GitHub Issues comment) and Phase 5.5 (GitHub Issues transition to Blocked) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 2.


---

## Phase 2: Prepare Submodule Story Branches

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py prepare-branches \
  --story-file {story_file_path} --story-branch {story_branch} \
  --epic-branch {epic_branch} --initiative-branch {initiative_branch} --repo-root .
```

Capture JSON output. Verify `count > 0` — at least one module was prepared.
Also capture `{domain_skills}` — the list of domain skill objects resolved from the prepared modules.
All subsequent dev work in Phase 3 will now land directly on the story branch in each module.

---

## Phase 2.5: Load Domain Skills

For each entry in `{domain_skills}` where `exists` is `true`:
1. Read the SKILL.md file at the entry's `path`.
2. Internalize the coding standards, architectural patterns, and conventions described.
3. **Context budget rule**: Only load each skill's main `SKILL.md` — do NOT pre-load referenced sub-documents or supplementary files. Load those on-demand during Phase 3 when a specific task needs them.

If `{domain_skills}` is empty (no mappings found or map file missing), proceed to Phase 3 without loading any domain skills.

---

## Phase 3: Execute Dev-Story Workflow (YOLO Mode)

1. **Load the Dev Agent persona** — apply `/bmad-agent-bmm-dev`:
   a. Load and read `_bmad/bmm/agents/dev.md` (the full dev agent persona).
   b. Load and read `_bmad/bmm/config.yaml` — store `{user_name}`, `{communication_language}`, `{output_folder}` as session variables.
   c. Embody the dev agent persona (role: Senior Software Engineer, identity: strict adherence to story details and team standards).
   d. **Skip interactive steps** (greeting, menu display, waiting for user input) — YOLO mode overrides these.
   e. **Apply domain skill standards** — all code written in Phase 3 MUST conform to the coding standards loaded in Phase 2.5. When working in a module, follow the patterns from its mapped domain skill (e.g., App Router architecture for Next.js modules, React 18.3 + MUI patterns for frontend modules). If a domain skill references a supplementary document needed for the current task, load it on-demand.
2. Load the BMAD workflow engine: `_bmad/core/tasks/workflow.xml` — read its entire contents.
3. Pass `_bmad/bmm/workflows/4-implementation/dev-story/workflow.yaml` as `workflow-config`.
4. Set BOTH `story_file` AND `story_path` workflow config variables to the resolved story path from Phase 1:
   `_bmad-output/implementation-artifacts/stories/{story_key}.md`
   Both variables must point to the same path. `instructions.xml` Step 1 checks `{{story_path}}` to bypass interactive story-discovery — without it set, Step 1's bypass branch never triggers and the agent falls into the interactive discovery loop (which in YOLO mode auto-picks "Run create-story" → stall).
5. **YOLO mode rules** — these override ALL workflow prompts, gates, AND HALT conditions:
   - Skip ALL user confirmations — auto-approve every gate.
   - Drive ALL choices toward completion — never pause, never ask, never defer.
   - If a step offers options, pick the one that moves toward done.
   - If a validation fails, attempt to fix it automatically and continue.
   - **Three-tier HALT protocol** — HALT triggers are classified by tier and handled differently. NEVER terminate the workflow early.

     | Tier | HALT Trigger | Response |
     |------|-------------|----------|
     | **Tier 1 — Self-Healable** | Test failures, compile errors, lint issues, style violations | FIX-THEN-SKIP: 2 fix attempts, log each, skip if both fail |
     | **Tier 2 — Transient** | 3 consecutive task implementation failures, framework detection failure | FIX-THEN-SKIP (2 additional attempts), then ESCALATE-GitHub Issues if still failing |
     | **Tier 3 — Fundamental Blockers** | Ambiguous requirements, missing config/secrets, new out-of-scope dependencies, Step 9 DoD gate failures, story file inaccessible | ESCALATE-GitHub Issues immediately (1 fix attempt is sufficient to confirm irresolvable) |

     **Tier 3 HALT triggers from `instructions.xml`**:
     - Step 1: story file inaccessible → Tier 3
     - Step 1: task/subtask requirements ambiguous → Tier 3
     - Step 5: new dependencies required beyond story scope → Tier 3
     - Step 5: required configuration is missing → Tier 3
     - Step 9: any task is incomplete (at DoD gate) → Tier 3
     - Step 9: definition-of-done validation fails → Tier 3

     **FIX-THEN-SKIP protocol** (Tier 1 & Tier 2):
     (1) Make at least 2 distinct fix attempts, each with a different approach.
     (2) Log each attempt: "FIX-ATTEMPT [TaskN] #N: [approach tried] — [result]".
     (3) Only after 2 logged failures, skip and log: "SKIP [TaskN]: [reason] after 2 fix attempts".

     **ESCALATE-GitHub Issues protocol** (Tier 2 confirmed irresolvable; Tier 3 immediately after 1 attempt):
     (1) Classify blocker type: `REQUIREMENT_GAP | CONFIG_MISSING | DEPENDENCY_NEEDED | DOD_FAILURE | INFRA_GAP`.
     (2) Append to `{blocker_summary}` session variable: type, reason, affected task IDs, action needed.
     (3) Leave affected tasks unchecked. Continue with remaining tasks.
     (4) **Guardrail**: Events are collected in `{blocker_summary}` — the actual GitHub Issues comment is posted in Phase 4.5 (not inline). A GitHub Issues API failure in Phase 4.5 MUST NOT stop the workflow.
   - **Never defer items**: Do not mark items as "deferred" or skip them because they are complex. Attempt every task and subtask. If one truly cannot be completed, leave it unchecked and move to the next — but attempt it first.
   - **Cross-module persistence**: When tasks span multiple modules (e.g., writing tests in src/components, integrating with src/lib), switch context to each module as needed. All modules were prepared in Phase 2.
   - **Never wrap up early**: Do not produce a completion summary, emit the sentinel, or move to Phase 4 until every item in the work queue has been attempted. Processing 2 of 7 items is not "done".
6. Execute ALL steps (1 through 10) of the dev-story workflow instructions (`instructions.xml`) without pausing. Iterate the task loop (Step 8 → Step 5) until EVERY task and subtask has been attempted — do not exit the loop early for any reason other than all items being checked or attempted.
7. **Validate and build work queue** — After `instructions.xml` Step 3 completes, validate its output and build the work queue. **Consume Step 3's computed state AND apply the following YOLO supplement for human review items (`instructions.xml` is unaware of `[Human-Review]`):**
   - If `{{review_continuation}}` is `true` (Step 3 detected a `Senior Developer Review (AI)` section):
     work queue = `{{pending_review_items}}` (unchecked `[AI-Review]` items Step 3 identified) PLUS any unchecked `[ ]` Tasks/Subtasks not yet addressed — this PLUS set explicitly includes any `[Human-Review]` items (they live directly in Tasks/Subtasks, not in a subsection).
   - If `{{review_continuation}}` is `false`:
     work queue = all unchecked `[ ]` items from Main Tasks/Subtasks (including any `[Human-Review]` items).
   **YOLO supplement**: Regardless of `{{review_continuation}}`, scan Tasks/Subtasks for lines matching `- [ ] [Human-Review]`. If any are found and not already in the work queue, append them. This supplements `instructions.xml` Step 3 which does not detect human review items.
   Assign sequence numbers `[1/N]`, `[2/N]`, ... to the final combined list.
   **If all main tasks are checked but `[AI-Review]` or `[Human-Review]` items remain unchecked, those ARE your work queue — do not skip them.**
8. **Serial task loop** — Process items strictly in sequence:
   a. Pick the next unchecked item from the work queue.
   b. **If the item has `[AI-Review]` prefix** (AI code review follow-up): extract severity, description, and file:line. Apply the fix, run tests, and mark `[x]` in both "Review Follow-ups (AI)" and the matching action item in "Senior Developer Review (AI)". Follow the RED→GREEN→VALIDATE protocol (skip EXPAND for simple fixes). Log: "REVIEW-FIX [Severity]: description — [approach]".
      **If the item has `[Human-Review]` prefix** (human PR review follow-up): extract severity, description, and file:line. Apply the fix, run tests, and mark `[x]` in Tasks/Subtasks only (there is no second section — human review findings live only in `### Human Code Review` which contains narrative, not a parallel action-item list). Follow the RED→GREEN→VALIDATE protocol (skip EXPAND for simple fixes). Log: "HUMAN-REVIEW-FIX [Severity]: description — [approach]".
   c. **If the item is a regular task/subtask**: execute this strict protocol (augments instructions.xml Steps 5→6→7→8):

      **INTENT** — Before writing any code, log in Dev Agent Record:
      "INTENT [TaskN]: [exact task description from story]. Files: [list]. Test scenarios: [list]."
      This is your contract — do not deviate from it.

      **RED** — Write failing tests for the task functionality. Run them NOW — they MUST fail.
      If tests pass immediately, they are wrong — delete and rewrite to assert not-yet-implemented behavior.
      **ATDD note**: If `zone-qa` has already run in ATDD mode for this story, failing acceptance tests already exist on the story branch (`agent/story/`). For those modules: (1) run existing tests to confirm they fail, (2) skip writing new RED-phase tests for acceptance criteria already covered, (3) focus on making those tests pass in the GREEN step. Write new RED tests only for implementation-level details not covered by the ATDD tests.
      Log: "RED [TaskN]: X tests written, all failing — [test names]"

      **GREEN** — Implement MINIMAL code to make tests pass. Run tests — they must now pass.
      Log: "GREEN [TaskN]: X/X passing — [command used]"

      **REFACTOR** — Improve structure while keeping tests green. Follow domain skill standards.

      **EXPAND** — (maps to instructions.xml Step 6) Add supplementary test coverage:
      edge cases, integration tests, E2E flows per story requirements.
      Do NOT re-create RED-phase tests. Run all — must pass.

      **VALIDATE** — (maps to instructions.xml Step 7) Run the FULL test suite (not just this task's tests).
      Capture pass/fail/skip counts from runner output.
      Log: "SUITE [TaskN]: X passed, Y failed, Z skipped — [command]"
      If any failures: STOP and fix before proceeding.

      **MARK** — (maps to instructions.xml Step 8) Only mark [x] if ALL of these are true:
      (a) RED, GREEN, SUITE logs exist in Dev Agent Record for this task
      (b) SUITE shows 0 failures
      (c) Implementation matches the INTENT statement — no extra features, no missing features
      (d) Every file in File List for this task actually exists on disk (verify with ls/stat)
      (e) Completion notes include: test file paths, test names, counts (unit/integration/E2E separate)

      If you cannot run tests (no runner/framework), log that fact and leave the task unchecked.
      Do NOT claim tests pass without running them.
   d. If the item is completed, check it `[x]`. If it truly cannot be completed (e.g., missing infrastructure not available in any module), leave it `[ ]` and log the reason in Dev Agent Record.
   e. Move to the next item. **Do not stop, summarize, or wrap up until the queue is empty.**
   f. Commit and push the changes to the sub--repo as soon as every item is completed in the sub-repo following the module and subrepo rules.
   g. After the last item, proceed to step 9.
9. **Execute Step 10 DoD checklist (DoD-only mode)** — Before finalising artifacts, invoke `instructions.xml` Step 10 in DoD-only mode:
   - Execute the enhanced DoD checklist (`checklist.md`) — validate all criteria against the completed work.
   - Write the completion summary to Dev Agent Record → Completion Notes section.
   - **SKIP** the interactive parts of Step 10: user greeting, asking for explanations, suggesting next steps.
   DoD gate failures here are **Tier 3** — collect in `{blocker_summary}`, do NOT attempt further fixes.

   Then ensure all BMAD artifacts are updated:
   - Story file: task checkboxes checked (including Review Follow-ups), dev agent record, file list, change log, status → `review`.
   - If `[AI-Review]` follow-ups were resolved in this session, add Change Log entry: "Addressed AI code review findings — N items resolved".
   - If `[Human-Review]` follow-ups were resolved in this session, add Change Log entry: "Addressed human review findings — N items resolved".
   - `_bmad-output/implementation-artifacts/sprint-status.yaml`: story status updated.

---

## Phase 4: Commit and Push Per Sub-Repo

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-modules \
  --modules '<JSON array of module paths from Phase 2>' \
  --story-branch {story_branch} --story-key {github-issues_key} \
  --title "{bmad_title}" --repo-root .
```

Capture JSON output. Log `committed_count` and `skipped_count`. Submodules with no changes are skipped (not an error).

---

## Phase 4.5: Post GitHub Issues Dev Completion Comment

Before running the comment command, prepare two values:

**Extract `{committed_module_list}`**: From Phase 4's `commit-modules` JSON output, collect the `name` field of every module entry where `action` is `"committed"`, joined as a comma-separated string (e.g., `src/lib, zone.gymops`). If no modules were committed or Phase 4 output is unavailable, use `"none"`.

**Extract `{dev_agent_record_body}`**: From the content written to `## Dev Agent Record` during Phase 3 of this session, collect only what was generated by the current run — scoped to the task IDs in the current session's work queue (from Phase 3 step 7). Include:
- The checked `[x]` task and subtask items from Main Tasks that were marked complete in this session (include the task description line, e.g. `- [x] Task 1: ...`)
- The checked `[x] [AI-Review]` items from "Review Follow-ups (AI)" that were resolved in this session (include the full item line with severity and file:line reference)
- The checked `[x] [Human-Review]` items from Tasks/Subtasks that were resolved in this session (include the full item line with severity and file:line reference)
- INTENT/RED/GREEN/REFACTOR/EXPAND/VALIDATE/SUITE/SKIP/FIX-ATTEMPT/REVIEW-FIX log lines for those task IDs
- Completion Notes entries for those task IDs (test file paths, test names, pass/fail counts)
- File List entries for those task IDs (files created or modified)

Do NOT include pre-existing entries from prior runs or tasks that were already checked before this session began. Preserve verbatim formatting including `[TaskN]` prefixes. Truncate to 32 KB if the combined output exceeds that limit. If no entries were logged in this session, set to empty string.

Run (best-effort, non-fatal):
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ✅ Zone Dev completed

- Story: `{story_key}`
- Status: {status_text}
- Branch: `agent/story/{github-issues_key}-{story_key}`
- Submodules changed: {committed_module_list}

{dev_agent_record_body}

{blocker_summary}
EOF
```

Where:
- `{status_text}` = `"All tasks complete"` if `{unchecked_count}` is 0, else `"{unchecked_count} tasks unchecked — see Dev Agent Record"`.
- `{blocker_summary}` = empty string if no blockers, else:
  `## Blockers` followed by one markdown bullet per ESCALATE-GitHub Issues event.
  Format each blocker as: `- [{task_id}] **{type}**: {reason}. Action needed: {guidance}.`

The same enrichment (branch, module list, dev agent record body) applies to the blocked/partial comment variant. If the story file is inaccessible at that point, omit `{dev_agent_record_body}`.

**Guardrail**: A non-zero exit code from this command MUST NOT stop the workflow. Log the failure and continue to Phase 5.

---

## Phase 5: Commit and Push Super-Repo

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-repo \
  --story-key {story_key} --story-key {github-issues_key} \
  --title "{bmad_title}" --repo-root .
```

Capture JSON output. If `action` is `"skipped"`, no _bmad-output/ changes were staged — this is not an error.

---

## Phase 5.5: GitHub Issues Transition

Set `{outcome}` = `blocked` if `{unchecked_count}` > 0, else `success`. Run (best-effort, non-fatal):
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py transition-github-issues \
  --story-key {github-issues_key} --skill zone-dev --outcome {outcome} --repo-root .
```

---

## Phase 6: Output Status

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py status \
  --story-file {story_file_path}
```

The script emits the sentinel line directly:
```
###ZONE-DEV-RESULT###{"status":"<0|1>","unchecked":<N>}###ZONE-DEV-RESULT###
```

---

## Critical Guardrails

| Rule | Detail |
|------|--------|
| YOLO mode | All workflow confirmations auto-approved; all choices drive toward completion |
| Submodule branches first | Checkout story branches in all referenced modules BEFORE the dev-story workflow runs, so all code changes land on the correct branch |
| Submodule init | Only initialize modules that the story file references in Tasks/Subtasks |
| Initiative branch first | If the epic belongs to an initiative (per sprint-status.yaml `initiatives` section), ensure initiative branch exists on remote (from module default branch) before creating epic branches; push immediately after creation |
| Epic branch first | Ensure epic branch exists on remote (from initiative branch if tagged, otherwise module default branch) before creating new story branches; push immediately after creation; skip if story branch already exists |
| Branch safety | Pull latest from story branch if it exists remotely; create off epic branch if not |
| Super-repo branch | NEVER create a new branch or checkout another branch — stay on current branch |
| Super-repo staging | NEVER `git add` any `modules/*` paths — only `_bmad-output/` artifacts |
| Headless/CI | Zero user interaction — all decisions automated — JSON-only final output |
| Commit message | Always use the format: `{github-issues_key}: {bmad_title} - <suffix>` |
| Git PUSH | Ensure the always local commits are pushed automatically. no further instructions required |
| HALT override | Three-tier protocol: Tier 1 (self-healable: test/compile/lint failures) → FIX-THEN-SKIP (2 attempts); Tier 2 (transient: consecutive impl. failures, framework detection) → FIX-THEN-SKIP then ESCALATE-GitHub Issues; Tier 3 (fundamental: ambiguous requirements, missing config, out-of-scope dependencies, Step 9 DoD gate failures, inaccessible story) → ESCALATE-GitHub Issues immediately. Never terminate the workflow early. |
| Evidence-based TDD | Every task MUST have INTENT, RED, GREEN, and SUITE log entries in Dev Agent Record before marking [x]. Never claim tests pass without runner output evidence. |
| File verification | Every File List entry must correspond to a file that exists on disk. Verify with ls/stat before marking task complete. |
| CI output | Result emitted as `###ZONE-DEV-RESULT###...###ZONE-DEV-RESULT###` sentinel in stdout — TeamCity greps for it |
| Status criteria | Status `"0"` ONLY when all story checkboxes are `[x]`; any unchecked item = status `"1"` |
| No early wrap-up | Do not summarize, emit sentinel, or move to Phase 4 until every task in the work queue has been attempted |
| Review follow-ups | `[AI-Review]` tasks in "Review Follow-ups (AI)" and `[Human-Review]` tasks in Tasks/Subtasks are both part of the work queue — enumerate and process them like any other task; do not skip or declare "all tasks done" while they remain unchecked |
| Frontend deps in CI | When installing dependencies in frontend modules (src/components, zone.gymopspwa, zone.gymops.qrrouter), use `npm ci` for npm modules and `yarn install --frozen-lockfile` for Yarn modules. Never run `npm install` or plain `yarn install` in CI — this regenerates lock files. |

---

## Key Files Referenced

| Purpose | Path |
|---------|------|
| Automation script | `.claude/skills/zone-dev/scripts/zone_dev.py` |
| story key map | `_bmad-output/implementation-artifacts/story-key-map.yaml` |
| Story files | `_bmad-output/implementation-artifacts/stories/{story_key}.md` |
| Sprint status | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| BMAD config | `_bmad/bmm/config.yaml` |
| Workflow engine | `_bmad/core/tasks/workflow.xml` |
| Dev-story workflow | `_bmad/bmm/workflows/4-implementation/dev-story/workflow.yaml` |
| Dev-story instructions | `_bmad/bmm/workflows/4-implementation/dev-story/instructions.xml` |
| Dev agent persona | `_bmad/bmm/agents/dev.md` |
| Dev agent command | `.claude/commands/bmad-agent-bmm-dev.md` |
| Dev-story command | `.claude/commands/bmad-bmm-dev-story.md` |
| Submodule→skill map | `.claude/skills/zone-dev/module-skill-map.yaml` |
| Domain skills | `.claude/skills/{skill-name}/SKILL.md` (loaded dynamically in Phase 2.5) |
