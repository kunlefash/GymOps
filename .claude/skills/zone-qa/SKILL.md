---
name: zone-qa
description: Headless CI skill that resolves a story key to a BMAD story, generates acceptance/E2E/API/unit tests using TEA ATDD or BMM automation workflows, and commits/pushes test files per sub-repo and repo.
version: 1.0.0
triggers:
  keywords:
    - zone-qa
    - qa-ci
    - headless-qa
    - test-generation
  intents:
    - execute_qa_headless
    - ci_test_generation
    - atdd_test_generation
    - test_automation
---

# Zone QA — Headless CI Test Generation Skill

Autonomous, CI-friendly skill that takes a story key, resolves it to a BMAD story, generates tests using either ATDD or automation mode, and commits results to the appropriate branches. In automation mode, if no new coverage gaps are found, the run may complete as validation-only instead of generating new test files.

**Input**: `%github-issues_key%` (required story key), `%qa_mode%` (optional: `atdd|automation`)
**Output**: `###ZONE-QA-RESULT###{"status":"0","qa_mode":"atdd|automation","test_count":N,"test_types":["e2e","api","unit"]}###ZONE-QA-RESULT###` on success, `###ZONE-QA-RESULT###{"status":"1","qa_mode":"...","test_count":0,"test_types":[]}###ZONE-QA-RESULT###` on failure.

For `automation` mode:
- `test_count` means newly generated tests from Phase 3, not existing tests merely executed during validation.
- A successful run with `test_count: 0` is allowed only when the outcome is validation-only and no unchecked story tasks remain.

**NOTE**: When working on multiple modules, you may dispatch bounded tasks to subagents per module/repo only inside Phase 3 after branch preparation has completed successfully. Never use subagents to overlap phases or to start module work before the Phase 2 gate has been satisfied.

## Phase Execution Contract

Phases `0` through `6` are strictly sequential.

- Do not start any command from Phase `N+1` until the Phase `N` command has finished, its exit code has been checked, and its required outputs have been validated.
- Never run commands from different phases concurrently.
- `prepare-branches` is a hard barrier for all module work.
- Do not run module tests, `dotnet test`, workflow commands, framework detection, subagent work, or implementation-oriented file inspection inside a prepared module until `prepare-branches` has returned successfully and `count > 0` has been confirmed.
- If `prepare-branches` is still running, wait. Do not speculate, preload Phase 3 work, or launch module validation in parallel.

## Modes

| Mode | When | Branch Pattern | Description |
|------|------|----------------|-------------|
| **ATDD** | Before `zone-dev` | `agent/story/{github-issues_key}-{story_key}` | Generates failing acceptance tests first; dev then implements code to make them pass |
| **automation** | After `zone-dev` | Reuses `agent/story/{github-issues_key}-{story_key}` | Generates tests to expand test coverage on existing implementation |

Mode is determined by the `qa_mode` field in the story file frontmatter/metadata. Default: `automation`.

---

## Pre-Warm Mode

If this prompt contains `PHASES 0-2 PRE-RESOLVED`, the pipeline has already
executed Phases 0-2.5. In this case:

1. **Skip Phases 0, 1, 2, 2.5** — do NOT run sync-repo, resolve,
   prepare-branches, or read domain skill files.
2. **Extract session variables** from the JSON in `PHASES 0-2 PRE-RESOLVED`:
   - `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_branch}`,
     `{story_file_path}`, `{github-issues_key}`, `{qa_mode}`, `{epic_branch}`, `{initiative_branch}`, etc.
3. **Internalize domain skills** from the `DOMAIN SKILLS` section.
4. If `prewarm_status` is `"partial"`, review `prepare_branches` output for
   errors and work with successfully prepared modules only.
5. **Begin at Phase 3** (or the first non-preparation phase).

If no `PHASES 0-2 PRE-RESOLVED` marker exists, execute all phases from Phase 0.

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-qa/scripts/zone_qa.py sync-repo --repo-root .
```

Pulls the latest repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**HALT protocol (Phase 0 failure):** If exit code is non-zero, set `{blocker_summary}` to `"SYNC_FAILED: repo sync failed — branch may be behind or have conflicts"`, then run Phase 5 (post blocked GitHub Issues comment) and Phase 5.5 (GitHub Issues transition to Blocked) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.


---

## Phase 1: Resolve GitHub Issues Key to Story

Run:
```
python3 .claude/skills/zone-qa/scripts/zone_qa.py resolve \
  --story-key %github-issues_key% [--qa-mode atdd|automation] --repo-root .
```

Capture JSON output as session variables: `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_file_path}`, `{github-issues_key}`, `{qa_mode}`, `{epic_branch}`, `{parent_github-issues_key}`, `{initiative_branch}`.

The `{qa_mode}` is resolved in this order:
1. supplied `--qa-mode` argument (if provided)
2. `qa_mode` in story file frontmatter/metadata
3. default `automation`

**HALT protocol (Phase 1 failure):** If exit code is non-zero, classify the blocker from the script's error output:
- `KEY_NOT_FOUND` — story key not present in `story-key-map.yaml`
- `STORY_FILE_MISSING` — story file not found (story not yet prepared by zone-prepare-story)
- `INVALID_STATUS` — story is not in a testable status
- `SPRINT_STATUS_MISSING` — `sprint-status.yaml` absent or malformed

Set `{blocker_summary}` to `"<BLOCKER_TYPE>: <error message from script>"`, then run Phase 5 (post blocked GitHub Issues comment) and Phase 5.5 (GitHub Issues transition to Blocked) using `%github-issues_key%` as the issue key and `{qa_mode}` = the supplied `--qa-mode` arg or `"automation"`, then exit with status `"1"`. Do NOT proceed to Phase 2.


---

## Phase 2: Prepare Submodule Branches

Run:
```
python3 .claude/skills/zone-qa/scripts/zone_qa.py prepare-branches \
  --story-file {story_file_path} --qa-mode {qa_mode} \
  --story-key {github-issues_key} --story-key {story_key} \
  --epic-branch {epic_branch} --initiative-branch {initiative_branch} --repo-root .
```

Capture JSON output. Initialize `{blocker_summary}` as empty string.
Also capture `{domain_skills}` — the list of domain skill objects resolved from the prepared modules.

Verify `count > 0` — at least one module was prepared. If count == 0:
- **Tier 3 ESCALATE-GitHub Issues**: classify blocker based on mode:
  - ATDD mode: `EPIC_BRANCH_MISSING` — could not create test branches (epic branch not found)
  - automation mode: `BRANCH_NOT_FOUND` — no story branch found in any module
- Append to `{blocker_summary}`: e.g., `BRANCH_NOT_FOUND: story branch '{story_branch}' not found in any module (attempted: <list>)`.
- Skip Phases 2.5, 3, 4 — proceed directly to Phase 5 with `status: "1"`.

Only after `prepare-branches` completes and `count > 0` is confirmed may the agent enter Phase 2.5 or Phase 3.
If `count == 0`, skip directly to Phase 5. Do not run any module command.

**Branch behavior by mode**:
- **ATDD mode**: Creates `agent/story/{github-issues_key}-{story_key}` branches on test modules (from epic branch or default). Uses the same branch namespace as zone-dev so the handoff is seamless.
- **automation mode**: Checks out existing `agent/story/{github-issues_key}-{story_key}` branches (already created by zone-dev). Submodules where the story branch does not exist are skipped.

---

## Phase 2.5: Load Domain Skills

For each entry in `{domain_skills}` where `exists` is `true`:
1. Read the SKILL.md file at the entry's `path`.
2. Internalize the coding standards, test patterns, and conventions described.
3. **Context budget rule**: Only load each skill's main `SKILL.md` — do NOT pre-load referenced sub-documents or supplementary files. Load those on-demand during Phase 3 when a specific task needs them.

Additionally:
- Load TEA config from `_bmad/tea/config.yaml` — store TEA module settings.
- Load the TEA agent persona from `_bmad/tea/agents/tea.md`.

If `{domain_skills}` is empty (no mappings found or map file missing), proceed to Phase 3 without loading any domain skills.

---

## Phase 3: Execute Test Generation Workflow (YOLO Mode)

Phase 3 begins only after Phase 2 and Phase 2.5 are complete. Do not begin workflow execution, framework detection, module inspection, or test commands until the Phase 2 prepare-branches barrier has completed successfully and `count > 0` is confirmed.

### Mode Selection

| `{qa_mode}` | Primary Workflow |
|------|-----------------|
| `atdd` | TEA `testarch-atdd` (`_bmad/tea/workflows/testarch/atdd/workflow.yaml`) for story `{story_key}` |
| `automation` | TEA `testarch-automate` (`_bmad/tea/workflows/testarch/atdd/workflow.yaml`) for story `{story_key}` |

### Test Framework Auto-Detection per Submodule

Load `.claude/skills/zone-qa/test-framework-map.yaml` to resolve each module's test framework, version, and conventions. Match the module name against the `pattern` field (pipe-delimited). Use the matched entry's `framework`, `domain_skill`, and `conventions` to configure test generation for that module.

If no pattern matches, fall back to the domain skill loaded in Phase 2.5 for test conventions.

### E2E/API Test Repo Routing (Pre-Workflow — MANDATORY)

Apply the following routing rules **before** executing the TEA workflow. This is a hard requirement: E2E and API tests MUST NOT be written into source modules.

1. **Identify the E2E test repo**: From the Phase 2 `prepare-branches` output, find the module entry with `"role": "e2e_test_repo"`. This is always `tests/e2e`. If it is absent from the output (e.g., directory does not exist in this environment), log a warning and skip E2E/API test generation for those test types only — do not block unit/integration test generation.

2. **Test type routing rules**:

| Test Type | Target Submodule | Directory |
|-----------|-----------------|-----------|
| E2E (Playwright browser) | `tests/e2e` | `tests/cardless/pwa/` |
| API (Playwright request) | `tests/e2e` | `tests/cardless/api/` |
| Unit / Component | Source module (e.g., `zone.gymopspwa`, `zone.gymops`) | Per source module conventions |
| Integration | Source module | Per source module conventions |

3. **Convention injection for E2E/API tests** — when the TEA workflow generates E2E or API tests targeting `tests/e2e`, the following zone-qa-automation conventions MUST be applied. Treat these as absolute constraints, not suggestions:
   - **File naming**: `camelCase.spec.js` (not `.ts`, not kebab-case, not PascalCase)
   - **Page objects**: MUST extend `BasePage` from `pageObjectClass/basePage.js`; always call `super(page)` in constructor
   - **Locators**: always use `.first()` on any locator that could match multiple elements
   - **Interactions**: use `this.waitAndClick(locator)` and `this.waitAndFill(locator, text)` — never bare `.click()` or `.fill()`
   - **API auth**: MUST use `getHeadersForBank(request, institution)` from `apiManager/apiBase.js` — never fetch tokens inline
   - **Data-driven**: wrap tests in a multi-institution loop over `['BANKA', 'BANKB', 'OFI']` for cross-tenant coverage
   - **Testiny annotations**: add `test.info().annotations.push({ type: '<testiny_id>', description: '...' })` for traceability
   - **Logging**: use emoji markers consistently — `✅` success, `❌` failure, `⚠️` warning, `🔵` info/step

4. **Convention injection for unit/integration tests** — keep `{project-root}` as the source module and follow the source module's domain skill (zone-dotnet for Jest, zone-frontend for Vitest, etc.).

5. **Subagent context preamble** — when dispatching TEA subagents for E2E or API test generation, prepend the following to the subagent context before the subagent's own step file instructions:
   > "The target repository for all E2E and API tests is `modules/tests/e2e/`. Do NOT write test files into the source module. Use `tests/cardless/pwa/` for E2E tests and `tests/cardless/api/` for API tests. Follow the zone-qa-automation skill conventions: BasePage POM inheritance, `getHeadersForBank()` for API auth, multi-institution loops (BANKA/BANKB/OFI), `camelCase.spec.js` file names, and emoji logging."

### Execution Steps
1. IF `{qa_mode}`=`atdd` THEN FOLLOW the instructions in `.claude/commands/bmad-tea-testarch-atdd.md` file strictly. This  workflow is template-based and follows a step-file architecture. Follow it religiously.
2. IF `{qa_mode}`=`automation` THEN FOLLOW the instructions in `.claude/commands/bmad-tea-testarch-automate.md` file strictly. This workflow is template-based and  follows a step-file architecture. Follow it religiously.
---

## Phase 4: Commit and Push Per Sub-Repo

Run:
```
python3 .claude/skills/zone-qa/scripts/zone_qa.py commit-modules \
  --modules '<JSON array of module paths from Phase 2>' \
  --story-key {github-issues_key} --title "{bmad_title}" \
  --suffix "test generation complete" --qa-mode {qa_mode} \
  --story-key {story_key} --repo-root .
```

Capture JSON output. Log `committed_count` and `skipped_count`. Submodules with no changes are skipped (not an error).

Then commit repo:
```
python3 .claude/skills/zone-qa/scripts/zone_qa.py commit-repo \
  --story-key {github-issues_key} --title "{bmad_title}" \
  --suffix "test generation complete; module updates" --repo-root .
```

Capture JSON output. If `action` is `"skipped"`, no _bmad-output/ changes were staged — this is not an error.

---

## Phase 4.5: Attach Test Artifact to GitHub Issues (Best-Effort)

Determine the artifact path based on `{qa_mode}`:
- **ATDD**: `_bmad-output/test-artifacts/atdd-checklist-{story_key}.md`
- **automation**: `_bmad-output/test-artifacts/automation-summary.md`

If the file exists, attach it to the story. Set `{artifact_attached}` = `true` on success, `false` otherwise.

Run (best-effort, non-fatal):
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py attach-file {github-issues_key} \
  {artifact_path} --filename {artifact_filename}
```

Where:
- ATDD: `{artifact_filename}` = `atdd-checklist-{story_key}.md`
- automation: `{artifact_filename}` = `automation-summary-{story_key}.md`

If the file does not exist or the attach call fails, set `{artifact_attached}` = `false`, log the failure, and continue — non-fatal.

---

## Phase 5: GitHub Issues Comment (Best-Effort)

Post a comment to the story summarizing test generation results. Branch on `{blocker_summary}`:

**Full success with new tests** (`{blocker_summary}` is empty and Phase 3 created new tests):
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ✅ zone-qa ({qa_mode}) completed

- Outcome: {test_count} tests generated ({test_types})
- Branch: `agent/story/{github-issues_key}-{story_key}`
- Artifact: {artifact_filename} attached to issue ✅  ← include only when {artifact_attached} is true; omit this line when false
EOF
```

**Validation-only success** (`{blocker_summary}` is empty and Phase 3 created no new tests because coverage was already sufficient):
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ✅ zone-qa ({qa_mode}) completed

- Outcome: Validation only; no new tests were needed
- Branch: `agent/story/{github-issues_key}-{story_key}`
- Artifact: {artifact_filename} attached to issue ✅  ← include only when {artifact_attached} is true; omit this line when false
EOF
```

**Blocked** (`{blocker_summary}` is non-empty — Tier 3 fired, no tests generated):
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ⚠️ zone-qa ({qa_mode}) blocked

- Outcome: No tests were generated
- Action: Manual intervention required

### Blockers
{blocker_summary}
EOF
```

**Best-effort**: If the comment call fails (e.g., no GitHub Issues connection in CI), log the failure and continue — non-fatal.

---

## Phase 5.5: GitHub Issues Transition

Set `{outcome}` = `blocked` if `{blocker_summary}` is non-empty, else `success`. Run (best-effort, non-fatal):
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py transition-github-issues \
  --story-key {github-issues_key} --skill zone-qa-{qa_mode} --outcome {outcome} --repo-root .
```

---

## Phase 6: Output Status

Run:
```
python3 .claude/skills/zone-qa/scripts/zone_qa.py status \
  --story-file {story_file_path} --qa-mode {qa_mode} \
  --test-count {test_count} --test-types '{test_types_json}' \
  [--validation-only] \
  --repo-root .
```

Where `{test_count}` is the integer count of newly generated tests tracked during Phase 3, and `{test_types_json}` is the JSON array string (e.g. `'["unit"]'`).
Pass `--validation-only` only for successful `automation` reruns where no new test files were created and the run only validated existing coverage.

The script emits the sentinel line directly:
```
###ZONE-QA-RESULT###{"status":"<0|1>","qa_mode":"<atdd|automation>","test_count":<N>,"test_types":["e2e","api","unit"]}###ZONE-QA-RESULT###
```

---

## Critical Guardrails

| Rule | Detail |
|------|--------|
| YOLO mode | All workflow confirmations auto-approved; all choices drive toward completion |
| Mode determines branches | Both ATDD and automation use `agent/story/` branches; ATDD creates them, automation reuses existing ones |
| Submodule branches first | Checkout/create test branches in all referenced modules BEFORE the test generation workflow runs |
| No cross-phase parallelism | Never run commands from different phases concurrently. Phase 2 must fully complete before any Phase 3 action begins |
| Prepare-branches barrier | In automation mode, no module validation, build, or test command may run until `prepare-branches` has returned success and target branches are confirmed |
| Submodule init | Only initialize modules that the story file references in Tasks/Subtasks |
| Initiative branch first | If the epic belongs to an initiative, ensure initiative branch exists on remote before creating epic branches |
| Epic branch first | Ensure epic branch exists on remote before creating new QA branches; push immediately after creation |
| Branch safety | Pull latest from branch if it exists remotely; create off epic branch if not |
| Super-repo branch | NEVER create a new branch or checkout another branch — stay on current branch |
| Super-repo staging | NEVER `git add` any `modules/*` paths — only `_bmad-output/` artifacts |
| Headless/CI | Zero user interaction — all decisions automated — JSON-only final output |
| Commit message | Always use the format: `{github-issues_key}: {bmad_title} - <suffix>` |
| Git PUSH | Ensure all local commits are pushed automatically. No further instructions required |
| HALT override | Three-tier protocol: Tier 3 (fundamental blockers) → ESCALATE-GitHub Issues immediately, append to `{blocker_summary}`, skip to Phase 5 with `status: "1"`; Tier 2 (transient failures) → retry once with different approach, skip after 2 attempts; Tier 1 (self-healable) → retry once, skip item with log, continue — never terminate the workflow early |
| blocker_summary | Initialized as empty string in Phase 2; Tier 3 classifiers appended on escalation; Phase 5 branches on empty vs non-empty to emit ✅ success or ⚠️ blocked comment |
| Test framework detection | Auto-detect test framework per module using domain skill mappings |
| ATDD tests must fail | In ATDD mode, generated tests MUST be failing (not-yet-implemented behavior). If tests pass immediately, they are wrong |
| automation tests must pass | In automation mode, generated tests MUST pass against existing implementation |
| Validation-only truthfulness | In automation mode, never describe executed existing tests as newly generated tests. If no new test files were created, report the run as validation-only |
| CI output | Result emitted as `###ZONE-QA-RESULT###...###ZONE-QA-RESULT###` sentinel in stdout — TeamCity greps for it |
| No early wrap-up | Do not summarize, emit sentinel, or move to Phase 4 until every test scenario has been attempted |
| Frontend deps in CI | When installing dependencies in frontend modules (src/components, zone.gymopspwa, zone.gymops.qrrouter), use `npm ci` for npm modules and `yarn install --frozen-lockfile` for Yarn modules. Never run `npm install` or plain `yarn install` in CI — this regenerates lock files. |

### Sequencing Example

- Forbidden: run `prepare-branches` and `dotnet test` in parallel.
- Required: run `prepare-branches`, wait for completion, confirm `count > 0`, then start validation or workflow execution inside the prepared module branches.

---

## Key Files Referenced

| Purpose | Path |
|---------|------|
| Automation script | `.claude/skills/zone-qa/scripts/zone_qa.py` |
| story key map | `_bmad-output/implementation-artifacts/story-key-map.yaml` |
| Story files | `_bmad-output/implementation-artifacts/stories/{story_key}.md` |
| Sprint status | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| BMAD config | `_bmad/bmm/config.yaml` |
| Workflow engine | `_bmad/core/tasks/workflow.xml` |
| TEA ATDD workflow | `_bmad/tea/workflows/testarch/atdd/workflow.yaml` |
| TEA automate workflow | `_bmad/tea/workflows/testarch/automate/workflow.yaml` |
| TEA config | `_bmad/tea/config.yaml` |
| TEA agent persona | `_bmad/tea/agents/tea.md` |
| Submodule→skill map | `.claude/skills/zone-qa/module-skill-map.yaml` |
| Test framework map | `.claude/skills/zone-qa/test-framework-map.yaml` |
| Domain skills | `.claude/skills/{skill-name}/SKILL.md` (loaded dynamically in Phase 2.5) |
| TEA test artifacts | `_bmad-output/test-artifacts/` (ATDD checklists, automation summaries) |
| GitHub Issues agile script | `.claude/skills/github-issues-agile/scripts/github-issues_agile.py` |
