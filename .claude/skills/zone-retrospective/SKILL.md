---
name: zone-retrospective
description: Headless CI skill that generates a pre-analysis brief for a completed epic by directly synthesizing story file data. Triggered automatically when all epic stories reach 'done'. Does NOT invoke the BMAD retrospective workflow — that is Mode 2 (interactive facilitated session).
version: 1.0.0
triggers:
  keywords:
    - zone-retrospective
    - retro-analysis-ci
    - headless-retro-analysis
  intents:
    - execute_retro_analysis_headless
    - ci_retro_analysis
---

# Zone Retrospective — Headless CI Pre-Analysis Skill

Autonomous, CI-friendly skill that takes an epic Jira key, verifies all stories are done, and synthesizes a pre-analysis brief directly from story file data. Does NOT invoke `_bmad/bmm/workflows/` — that is Mode 2 (interactive facilitated session, triggered via `/retrospective`).

**Input**: `epic_jira_key` (e.g. `CLSDLC-1`)
**Output**: `###ZONE-RETRO-RESULT###{"status":"0","epic_key":"CLSDLC-1","analysis_file":"..."}###ZONE-RETRO-RESULT###` on success, `status:"1"` on failure.

**Output document**: `_bmad-output/implementation-artifacts/epic-{N}-retro-analysis-{date}.md`
**Document header**: `> Auto-Generated Pre-Analysis Brief — Not a Final Retrospective`

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-retrospective/scripts/zone_retrospective.py sync-superrepo --repo-root .
```

Pulls the latest super-repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.

**HALT protocol (Phase 0 failure):** If exit code is non-zero, set `{blocker_summary}` to `"SYNC_FAILED: super-repo sync failed — branch may be behind or have conflicts"`, then post a Jira comment on `{epic_jira_key}` (Phase 4.5) and exit with `status:"1"`. Do NOT proceed to Phase 1.

---

## Phase 0.5: Pre-Execution Workspace Check

Before any operations, verify the workspace is clean:
```
git status --porcelain
```

If `.log` files appear at repo root OR unexpected `modules/*` modifications appear → set `{blocker_summary}` = `"WORKSPACE_DIRTY: unexpected pre-existing dirty state — <list of dirty paths>"`, post Jira comment, exit `status:"1"`.

**YOLO mode**: Never ask the user — classify automatically and either continue or halt.

---

## Phase 1: Resolve Epic and Verify Completion

Run:
```
python3 .claude/skills/zone-retrospective/scripts/zone_retrospective.py resolve-epic \
  --jira-key {epic_jira_key} --repo-root .
```

Capture JSON output as session variables: `{epic_bmad_id}`, `{epic_title}`, `{epic_slug}`, `{story_file_paths}` (list), `{analysis_file}`, `{prev_retro_path}` (may be null), `{next_epic_bmad_id}` (may be null), `{implementation_artifacts}`.

**HALT protocols:**

| Error | Condition | Action |
|-------|-----------|--------|
| `ANALYSIS_ALREADY_EXISTS` | JSON contains `"action":"ANALYSIS_ALREADY_EXISTS"` | Emit sentinel with `status:"0"` immediately — idempotent exit. No further phases needed. |
| `EPIC_NOT_COMPLETE` | Exit code non-zero, error contains EPIC_NOT_COMPLETE | Set `{blocker_summary}`, post Phase 4.5 Jira comment on `{epic_jira_key}`, exit `status:"1"` |
| `KEY_NOT_FOUND` | Exit code non-zero, error contains KEY_NOT_FOUND | Set `{blocker_summary}`, post Phase 4.5 Jira comment, exit `status:"1"` |
| `SPRINT_STATUS_MISSING` | Exit code non-zero, error contains SPRINT_STATUS_MISSING | Set `{blocker_summary}`, post Phase 4.5 Jira comment, exit `status:"1"` |

---

## Phase 2: Mark Analysis Pending

Run:
```
python3 .claude/skills/zone-retrospective/scripts/zone_retrospective.py mark-analysis-pending \
  --epic-bmad-id {epic_bmad_id} --repo-root .
```

Adds `epic-{N}-retro-analysis: pending` to `sprint-status.yaml` using ruamel.yaml (preserves STATUS DEFINITIONS comment block). Commits and pushes the change.

**If this step fails**: log the error and continue — the analysis is more important than the status marker.

---

## Phase 3: Direct Headless Analysis

This phase drives the analysis entirely in-context. Do NOT invoke `workflow.xml`, `instructions.md`, or any BMAD workflow engine — those are reserved for Mode 2.

### 3.1 Load Context

1. **Load SM persona**: Read `_bmad/bmm/agents/sm.md` — internalize the Scrum Master lens for retrospective synthesis.
2. **Load BMAD config**: Read `_bmad/bmm/config.yaml` — note `{user_name}`, `{project_name}`, `{communication_language}`.

### 3.2 Extract Story Data

For each file path in `{story_file_paths}`:
1. Read the story file.
2. Extract **ONLY** the following sections (skip all others to stay within the 10K token budget per story):
   - `## Dev Agent Record` (or equivalent implementation notes section)
   - `### Senior Developer Review (AI)` (AI code review findings)
   - `### Human Code Review` (human reviewer feedback)
   - `### Technical Debt` (or debt items listed in action items)
3. Collect per story: title, jira_key, key wins (things that went well), struggles/blockers, AI review findings (CRITICAL/HIGH/MEDIUM issues), human review themes, debt items.

### 3.3 Synthesize Cross-Story Patterns

Across all stories, identify:
- **Recurring wins**: patterns of success that appeared in 2+ stories
- **Recurring struggles**: blockers or pain points that appeared in 2+ stories
- **Review feedback themes**: most common CRITICAL/HIGH/MEDIUM categories from AI and human reviews
- **Tech debt inventory**: aggregated debt items grouped by type (architecture, testing, documentation, performance, security)

### 3.4 Previous Retro Follow-Through (if `{prev_retro_path}` is not null)

1. Read the file at `{prev_retro_path}`.
2. Extract the "AI-Generated Action Item Candidates" section.
3. For each action item, determine whether this epic's stories addressed it (evidence from story data) or not.
4. Classify each as: ✅ Addressed | ⚠️ Partially addressed | ❌ Not addressed | N/A (out of scope).

### 3.5 Next Epic Dependencies (if `{next_epic_bmad_id}` is not null)

1. Search `{implementation_artifacts}` for the next epic's planning file. Look for files matching `epic-{next_epic_bmad_id}*.md` or `{next_epic_bmad_id}*.md` in the parent `_bmad-output/planning-artifacts/` directory.
2. If found, read it and extract: stated dependencies on current epic, technical prerequisites, risks flagged.
3. If not found, note "Next epic planning file not available".

### 3.6 Generate Action Item Candidates

Generate 5–10 SMART action item candidates based on the synthesized data. Label all as **"Unvalidated Candidates"** — they require team validation in the facilitated retrospective (Mode 2).

Format each as:
```
- [ ] [Unvalidated] {SMART description} — Source: {story_key or "cross-epic pattern"}
```

Focus on: process improvements, recurring pain points, debt items with highest impact, patterns from review feedback.

### 3.7 Write Analysis Document

Write the pre-analysis brief to `{analysis_file}`:

```markdown
> Auto-Generated Pre-Analysis Brief — Not a Final Retrospective

# Epic {epic_bmad_id} Retrospective Pre-Analysis
**Epic**: {epic_title}
**Jira Key**: {epic_jira_key}
**Generated**: {current_date}
**Stories Analysed**: {count}

---

## Epic Metrics

| Metric | Value |
|--------|-------|
| Stories completed | {count} |
| Story keys | {comma-separated jira keys} |
| AI review issues (CRITICAL) | {total across all stories} |
| AI review issues (HIGH) | {total across all stories} |
| AI review issues (MEDIUM) | {total across all stories} |
| Tech debt items identified | {total count} |

---

## Synthesized Patterns

### Wins (Things That Went Well)
{recurring successes — bullet list}

### Struggles (Things That Were Hard)
{recurring blockers/pain points — bullet list}

---

## Review Feedback Patterns

### Most Common AI Review Themes
{top themes with frequency — bullet list}

### Most Common Human Review Themes
{top themes with frequency — bullet list}

---

## Tech Debt Inventory

{Grouped by type: Architecture | Testing | Documentation | Performance | Security}

---

## Previous Retro Action-Item Follow-Through

{Only present if prev_retro_path was loaded. Table with: Action | Status | Evidence}

{If no previous retro: "No previous retrospective found for this project."}

---

## Next Epic Dependencies

{Dependencies extracted from next epic planning file, or "Next epic planning file not available."}

---

## AI-Generated Action Item Candidates (Unvalidated)

> These are AI-generated candidates only. Validate and prioritise during the facilitated retrospective session.

{5–10 action items in checkbox format}
```

If writing fails, set `{blocker_summary}` to `"WRITE_FAILED: could not write analysis file to {analysis_file}: {error}"`.

---

## Phase 4: Commit and Push Super-Repo

Run:
```
python3 .claude/skills/zone-retrospective/scripts/zone_retrospective.py commit-superrepo \
  --epic-bmad-id {epic_bmad_id} --jira-key {epic_jira_key} \
  --title "{epic_title}" --repo-root .
```

Stages only `_bmad-output/` (never `modules/*`), commits, pushes with retry. Capture JSON output. If `action` is `"skipped"`, no changes were staged — not an error.

---

## Phase 4.5: Post Jira Comment on Epic (Best-Effort)

**Always runs**. Non-fatal on failure.

**If SUCCESS** (no blocker_summary):

Run:
```
python3 .claude/skills/jira-agile/scripts/jira_agile.py add-comment {epic_jira_key} \
  --format markdown --body-stdin <<'EOF'
### ✅ AI Retro Pre-Analysis complete

- Epic: `{epic_jira_key}` — {epic_title}
- Stories analysed: {count}
- Analysis file: `{analysis_file}`

The pre-analysis brief is available as a Jira attachment. Use it as pre-read before the facilitated retrospective session (`/retrospective epic={epic_bmad_id}`).
EOF
```

**If BLOCKED** (blocker_summary is non-empty):

Run:
```
python3 .claude/skills/jira-agile/scripts/jira_agile.py add-comment {epic_jira_key} \
  --format markdown --body-stdin <<'EOF'
### ⚠️ AI Retro Pre-Analysis blocked

The automated retro pre-analysis could not complete.

**Blocker**: {blocker_summary}

Resolve the blocker and re-run the `aiRetroAnalysis` pipeline with `EPIC_JIRA_KEY={epic_jira_key}`.
EOF
```

On failure to post: log warning and continue. Never fail the pipeline due to Jira comment failure.

---

## Phase 4.6: Attach Analysis Document to Jira Epic (Best-Effort)

**Skip if `{blocker_summary}` is non-empty** (no analysis file was written).

Run:
```
python3 .claude/skills/zone-code-review/scripts/zone_review.py attach-story \
  --jira-key {epic_jira_key} --story-file {analysis_file} --repo-root .
```

Attaches the analysis file to the epic Jira issue. Non-fatal on failure.

---

## Phase 5: Mark Analysis Done

Run:
```
python3 .claude/skills/zone-retrospective/scripts/zone_retrospective.py mark-analysis-done \
  --epic-bmad-id {epic_bmad_id} --repo-root .
```

Sets `epic-{N}-retro-analysis: done` in `sprint-status.yaml`. Then commit and push the status update:

Run:
```
python3 .claude/skills/zone-retrospective/scripts/zone_retrospective.py commit-superrepo \
  --epic-bmad-id {epic_bmad_id} --jira-key {epic_jira_key} \
  --title "{epic_title}" --repo-root .
```

Non-fatal if the sprint-status update fails — the analysis file already exists.

---

## Phase 5.5: Jira Transition (Best-Effort)

Run (non-fatal, degrade gracefully):
```
python3 .claude/skills/zone-prepare-story/scripts/zone_prepare_story.py transition-jira \
  --jira-key {epic_jira_key} --skill zone-retrospective \
  --outcome {outcome} --repo-root .
```

Where `{outcome}` = `blocked` if `{blocker_summary}` is non-empty, else `success`.

Always proceed to Phase 6 regardless of outcome.

---

## Phase 6: Emit Sentinel

Emit the terminal sentinel line to stdout:
```
###ZONE-RETRO-RESULT###{"status":"<0|1>","epic_key":"{epic_jira_key}","analysis_file":"{analysis_file}"}###ZONE-RETRO-RESULT###
```

`status:"0"` = success (analysis complete or already existed); `status:"1"` = blocked/failed.

---

## Critical Guardrails

| Rule | Detail |
|------|--------|
| YOLO mode | All decisions automated — zero user interaction |
| No workflow.xml | Phase 3 drives analysis directly — NEVER invoke BMAD workflow engine or instructions.md |
| No submodule checkout | All artifacts live in super-repo `_bmad-output/`; never touch `modules/` |
| Super-repo staging | NEVER `git add` any `modules/*` paths — only `_bmad-output/` artifacts |
| ANALYSIS_ALREADY_EXISTS | Exit immediately with `status:"0"` — idempotent across retries |
| EPIC_NOT_COMPLETE | Hard blocker — post Jira comment, exit `status:"1"` |
| Document header | MUST include `> Auto-Generated Pre-Analysis Brief — Not a Final Retrospective` |
| ruamel.yaml | Used for sprint-status.yaml edits to preserve STATUS DEFINITIONS comment block |
| Phase 4.5/4.6 | Non-fatal — Jira failures never fail the pipeline |
| Commit message | Format: `{jira_key}: {epic_title} - retro analysis complete` |
| SKILL_MAX_ATTEMPTS=1 | Retries would just hit ANALYSIS_ALREADY_EXISTS — always use 1 attempt |
| Mode 2 unchanged | `/retrospective` command runs unmodified via existing BMAD workflow — this skill is Mode 1 only |

---

## Key Files Referenced

| Purpose | Path |
|---------|------|
| Automation script | `.claude/skills/zone-retrospective/scripts/zone_retrospective.py` |
| Jira key map | `_bmad-output/implementation-artifacts/jira-key-map.yaml` |
| Sprint status | `_bmad-output/implementation-artifacts/sprint-status.yaml` |
| Story files | `_bmad-output/implementation-artifacts/stories/{story_key}.md` |
| Analysis output | `_bmad-output/implementation-artifacts/epic-{N}-retro-analysis-{date}.md` |
| BMAD config | `_bmad/bmm/config.yaml` |
| SM persona | `_bmad/bmm/agents/sm.md` |
| Workflow transitions | `.claude/skills/_common/workflow-transitions.yaml` |
| Attach script | `.claude/skills/zone-code-review/scripts/zone_review.py` |
| Jira agile script | `.claude/skills/jira-agile/scripts/jira_agile.py` |
| Transition script | `.claude/skills/zone-prepare-story/scripts/zone_prepare_story.py` |
