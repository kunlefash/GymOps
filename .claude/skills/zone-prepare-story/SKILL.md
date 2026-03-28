---
name: zone-prepare-story
description: Headless CI skill that resolves a story key to a BMAD story, loads domain skills, executes the create-story workflow in YOLO mode, commits/pushes to repo, transitions GitHub Issues to In Progress, and attaches the story file to the story.
version: 1.0.0
triggers:
  keywords:
    - zone-prepare-story
    - prepare-story-ci
    - headless-prepare-story
  intents:
    - execute_prepare_story_headless
    - ci_prepare_story
---

# Zone Prepare Story — Headless CI Story-Preparation Skill

Autonomous, CI-friendly skill that takes a story key, resolves it to a BMAD story ID, loads domain skills from epic references, runs the full create-story workflow without user interaction, commits results to the super repo, and transitions the story to In Progress.

**Input**: `%github-issues_key%` (e.g. `CLSDLC-25`)
**Output**: `###ZONE-PREPARE-STORY-RESULT###{"status":"0|1","story_key":"..."}###ZONE-PREPARE-STORY-RESULT###`

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py sync-repo --repo-root .
```

Pulls the latest repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**HALT protocol (Phase 0 failure):** If exit code is non-zero, set `{blocker_summary}` to `"SYNC_FAILED: repo sync failed — branch may be behind or have conflicts"` then run Phase 4.7 (post blocked comment) and Phase 5 (GitHub Issues transition to Blocked) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 1.



---

## Phase 1: Resolve GitHub Issues Key

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py resolve \
  --story-key %github-issues_key% --repo-root .
```

Capture JSON output as session variables: `{bmad_id}`, `{bmad_title}`, `{story_key}`, `{story_file_path}`, `{github-issues_key}`, `{parent_github-issues_key}`, `{initiative_branch}`, `{epic_branch}`.
- Does NOT require story file to exist (create-story produces it).
- Validates sprint-status.yaml: story must be in `backlog` status.
**HALT protocol (Phase 1 failure):** If exit code is non-zero, classify the blocker from the script's error output:
- `INVALID_STATUS` — story exists but is not in `backlog` (e.g. `done`, `in-progress`, `in-review`) — the error message will contain the current status
- `KEY_NOT_FOUND` — story key not present in `story-key-map.yaml`
- `SPRINT_STATUS_MISSING` — `sprint-status.yaml` is absent or malformed

Set `{blocker_summary}` to `"<BLOCKER_TYPE>: <error message from script>"` then run Phase 4.7 (post blocked comment) and Phase 5 (GitHub Issues transition to Blocked) using `%github-issues_key%` as the issue key, then exit with status `"1"`. Do NOT proceed to Phase 2.



---

## Phase 2: Resolve Domain Skills

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py resolve-domain-skills \
  --bmad-id {bmad_id} --repo-root .
```

Capture JSON output as `{domain_skills}` — list of `{skill, path, exists}` objects and `{modules}` list.
- Parses `_bmad-output/planning-artifacts/epics.md` to find the story section for `{bmad_id}` (e.g., "2.1" → searches for `### Story 2.1:`)
- Extracts `**Repo:** modules/{name}` references from that story section
- Maps module names → domain skills via `module-skill-map.yaml`
- Non-fatal if epics file missing or no modules found — proceed without domain skills.

---

## Phase 2.5: Load Domain Skills

For each entry in `{domain_skills}` where `exists` is `true`:
1. Read the SKILL.md file at the entry's `path`.
2. Internalize the coding standards, architectural patterns, and conventions described.
3. **Context budget rule**: Only load each skill's main `SKILL.md` — do NOT pre-load referenced sub-documents or supplementary files. Load those on-demand during Phase 3 when a specific task needs them.

If `{domain_skills}` is empty (no mappings found or map file missing), proceed to Phase 3 without loading any domain skills.

---

## Phase 2.7: Checkout Submodule Research Branches

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py checkout-modules \
  --modules '{modules_json}' --epic-branch {epic_branch} --initiative-branch {initiative_branch} --repo-root .
```

Checks out the best available branch in each referenced module for code research:
- If `{epic_branch}` exists on the module's remote, checkout that branch (most specific context).
- Otherwise, if `{initiative_branch}` exists on the module's remote, checkout that branch.
- Otherwise, fall back to the module's default branch (from `.gitconfig`, typically `development`).
- **Read-only**: Never creates branches, never pushes. Only checks out existing remote branches.
- Non-fatal: if a module fails, log and continue.

This ensures the create-story workflow in Phase 3 reads the most current codebase — including code from prior stories in the same epic or prior epics merged into the initiative branch.

If both `{epic_branch}` and `{initiative_branch}` are empty/null, modules are checked out to their default branches.

---

## Phase 2.8: Resolve NuGet Dependencies

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py resolve-nuget-deps \
  --modules '{modules_json}' \
  --branch "{epic_branch}" \
  --initiative-branch "{initiative_branch}" \
  --repo-root .
```

Where `{modules_json}` is a JSON array of module paths from Phase 2 (e.g., `["src/framework", "src/gymops"]`).

Capture JSON output as `{nuget_deps}`.

If `has_nuget_deps` is `true`: store `{nuget_deps}` for injection into Dev Notes during Phase 3.
If `has_nuget_deps` is `false`: proceed without NuGet context.

**Note**: If no build tag is found for an upstream repo (CI hasn't run yet), the output includes a warning and no resolved version — the story will note that the version needs to be determined at implementation time.

---

## Phase 3: Execute Create-Story Workflow (YOLO Mode)

Invoke the BMAD create-story workflow. The workflow generates a detailed story file with dev notes, architecture requirements, and implementation guidance.

1. **Load SM persona** — read `_bmad/bmm/agents/sm.md`; adopt this persona.
2. **Load config** — read `_bmad/bmm/config.yaml`; store `{user_name}`, `{communication_language}`, `{output_folder}` as session variables.
3. **Load the BMAD workflow engine**: `_bmad/core/tasks/workflow.xml` — read its entire contents.
4. **Pass workflow config**: `_bmad/bmm/workflows/4-implementation/create-story/workflow.yaml` as `workflow-config`.
5. **Pre-set story target** = `{bmad_id}` (e.g., "2.1") — this satisfies the **"user provided the epic and story number"** branch of Step 1's bypass check (e.g., "2-4", "1.6", "epic 1 story 5"). `{{story_path}}` must NOT be set — the story file does not exist yet, and pointing Step 1 at a non-existent path would cause immediate validation failures. If Step 1 nonetheless enters the discovery loop (e.g., BMAD format change), YOLO should auto-respond with `{bmad_id}` as the story number and proceed.
6. **Apply domain skills** — use the standards loaded in Phase 2.5 when generating dev notes (architecture requirements, file structure, testing patterns, library/framework specifics).
7. **Inject NuGet context** — if `{nuget_deps}` from Phase 2.8 has `has_nuget_deps: true`:
   - Read the file `.claude/tmp/nuget-deps-context.md` (written by Phase 2.8)
   - Append its entire contents into the Dev Notes section of the story file, after the architecture requirements subsection
   - This file contains the pre-formatted `### NuGet Package Dependencies` subsection — include it verbatim
   - If the file does not exist, skip this step
8. **Execute** all steps (1 through 6) of the create-story `instructions.xml` (`_bmad/bmm/workflows/4-implementation/create-story/instructions.xml`) without pausing.

**YOLO mode** (these override ALL workflow prompts and interactive steps):
- Skip ALL user confirmations — auto-approve every gate.
- Skip ALL `<ask>` prompts — auto-select sensible defaults.
- Skip ALL `<template-output>` pauses — save and proceed immediately.
- Skip optional steps.
- Auto-select "all" improvements at checklist validation (Step 6).
- **HALT protocol** — three tiers based on blocker type. Initialize `{blocker_summary}` as empty string at the start of Phase 3; append Tier 3 events to it as they occur.

  | Tier | Condition | Action |
  |------|-----------|--------|
  | **Tier 3** — Step 1 HALTs | No backlog stories in sprint_status; epic status = `done`; invalid epic status; user selects "run sprint-planning first" (prerequisites missing) | ESCALATE-GitHub Issues immediately — classify blocker type (`NO_BACKLOG_STORIES \| EPIC_COMPLETE \| INVALID_EPIC_STATUS \| PREREQUISITES_MISSING`), append to `{blocker_summary}`, skip to Phase 4.7 with `status: "1"` — story cannot be created |
  | **Tier 1** — Step 5/6 validation | Template validation errors, checklist failures | FIX-THEN-SKIP — 2 fix attempts with different approaches, then skip with log |
  | **Tier 1** — Step 4 web research | Web search unavailable or times out | Retry once, then proceed without web results — partial story is better than no story |
- **DO execute web research** (Step 4) — adds value to story quality.
- Never pause for user input. Drive all choices toward completion.

After workflow completes, verify story file exists at `_bmad-output/implementation-artifacts/stories/{story_key}.md`.

---

## Phase 4: Commit & Push Super-Repo

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py commit-repo \
  --story-key {story_key} --story-key {github-issues_key} \
  --title "{bmad_title}" --repo-root .
```

Capture JSON output. If `action` is `"skipped"`, no `_bmad-output/` changes were staged — this is not an error.

---

## Phase 4.5: Attach Story File

**Skip this phase** if the story file was not created (a Tier 3 ESCALATE-GitHub Issues event fired in Phase 3 — `{blocker_summary}` is non-empty and story file does not exist at `{story_file_path}`).

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py attach-story \
  --story-key {github-issues_key} --story-file {story_file_path} --repo-root .
```

Attaches the generated story `.md` file directly to the story so team members can access it from GitHub Issues without checking the repo.

**Best-effort**: log warning if attachment fails, do NOT fail the skill.

---

## Phase 4.7: Post GitHub Issues Comment

Branch on `{blocker_summary}`:

**Full success** (`{blocker_summary}` is empty — story created normally):
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ✅ AI Context Story preparation completed

- Story file attached: `{story_filename}`
EOF
```
Where `{story_filename}` is the basename of `{story_file_path}` (e.g., `story-2.1.md`).

**Blocked** (`{blocker_summary}` is non-empty — Tier 3 ESCALATE-GitHub Issues fired, story not created):
```
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-comment {github-issues_key} \
  --format markdown --body-stdin <<'EOF'
### ⚠️ AI Context Story preparation blocked

- Story file was not created
- Action: Manual intervention required before story can be prepared

### Blockers
{blocker_summary}
EOF
```

**Best-effort**: log warning if comment fails, do NOT fail the skill.

---

## Phase 5: GitHub Issues Transition

Set `{outcome}` = `blocked` if `{blocker_summary}` is non-empty, else `success`. Run (best-effort, non-fatal):
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py transition-github-issues \
  --story-key {github-issues_key} --skill zone-prepare-story --outcome {outcome} --repo-root .
```

---

## Phase 6: Output Status

Run:
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py status \
  --story-key {story_key} --story-file {story_file_path} --repo-root .
```

The script emits the sentinel line directly:
```
###ZONE-PREPARE-STORY-RESULT###{"status":"<0|1>","story_key":"..."}###ZONE-PREPARE-STORY-RESULT###
```

Status `"0"` when story file exists with `Status: ready-for-dev`; `"1"` otherwise.

---

## Critical Guardrails

| Rule | Detail |
|------|--------|
| Domain skills | Load from epics **Repo:** references via module-skill-map.yaml |
| Submodule checkout (read-only) | Checkout initiative or default branch in modules for code research (Phase 2.7) — NEVER create branches or push to modules |
| Super-repo only | Only stage/commit `_bmad-output/` artifacts |
| Stay on branch | Never create/checkout branches — stay on current |
| Never stage modules | Never `git add` any `modules/*` paths |
| YOLO mode | All workflow confirmations auto-approved |
| Headless/CI | Zero user interaction — all decisions automated — JSON-only final output |
| GitHub Issues transition | Outcome resolved via workflow-transitions.yaml; best-effort, non-fatal |
| GitHub Issues attachment | Best-effort — attach story file to issue, warn on failure |
| Commit message | Always use the format: `{github-issues_key}: {bmad_title} - story preparation complete` |
| Git PUSH | Ensure all local commits are pushed automatically. No further instructions required |
| CI output | Result emitted as `###ZONE-PREPARE-STORY-RESULT###...###ZONE-PREPARE-STORY-RESULT###` sentinel in stdout — TeamCity greps for it |
| Status criteria | Status `"0"` = story file exists with `Status: ready-for-dev`; `"1"` = missing or wrong status |

---

## Key Files Referenced

| Purpose | Path |
|---------|------|
| Automation script | `.claude/skills/zone-prepare-story/scripts/zone_prepare_story.py` |
| story key map | `_bmad-output/implementation-artifacts/story-key-map.yaml` |
| Sprint status | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| Story output dir | `_bmad-output/implementation-artifacts/stories/` |
| Epics file | `_bmad-output/planning-artifacts/epics.md` |
| SM agent persona | `_bmad/bmm/agents/sm.md` |
| BMAD config | `_bmad/bmm/config.yaml` |
| Workflow engine | `_bmad/core/tasks/workflow.xml` |
| Create-story workflow | `_bmad/bmm/workflows/4-implementation/create-story/workflow.yaml` |
| Create-story instructions | `_bmad/bmm/workflows/4-implementation/create-story/instructions.xml` |
| Submodule-skill map | `.claude/skills/zone-prepare-story/module-skill-map.yaml` |
| Domain skills | `.claude/skills/{skill-name}/SKILL.md` (loaded dynamically in Phase 2.5) |
| GitHub Issues transition script | `.claude/skills/github-issues-agile/scripts/github-issues_agile.py` |
| NuGet resolver config | `.claude/skills/nuget-resolver/config.yaml` |
