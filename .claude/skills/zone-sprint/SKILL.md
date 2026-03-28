---
name: zone-sprint
description: Deterministic sprint construction for Zone Agentic SDLC. Reads sprint-status and BMAD planning artifacts, builds a dependency matrix of backlog stories, estimates story points, selects sprint scope with epic-completion bias to a target budget, then executes Wave 1 BMAD story generation by dispatching each story to a generalPurpose subagent (one per story, in parallel) that follows `.claude/skills/zone-sprint/references/story-creator.md`, before GitHub Issues updates and sprint creation through github-issues-agile tooling.
---

# Zone Sprint

Plan and apply sprint scope from BMAD artifacts with deterministic selection and explicit dependency handling.

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py sync-repo --repo-root .
```

Pulls the latest repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**On failure:** Stop and inform the user that the repo sync failed — the branch may be behind or have unresolved conflicts. The user must resolve these manually before re-running this skill.

---

## Prerequisites

1. BMAD artifacts exist:
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/planning-artifacts/epics.md`
- `_bmad-output/implementation-artifacts/story-key-map.yaml`
2. Skill config exists: `config.yaml`
3. Story workflow reference exists:
- `references/story-creator.md`
4. BMAD command docs exist:
- `.claude/commands/bmad-agent-bmm-sm.md`
- `.claude/commands/bmad-bmm-create-story.md`
5. For GitHub Issues execution steps, required env vars:
- `ATLASSIAN_EMAIL`
- `ATLASSIAN_API_TOKEN`
- `ATLASSIAN_CLOUD_ID`

If GitHub Issues prerequisites fail, stop before GitHub Issues updates and report exact missing prerequisites.

## Phase 1: Build Proposal

### Phase 1a: Estimation Subagent Dispatch (zone-estimator)

Before running the planner, dispatch a generalPurpose subagent to estimate backlog stories using the zone-estimator skill:

1. Load backlog story keys from `sprint-status.yaml` (entries with status `backlog`).
2. Load the estimation dispatch prompt from `templates/estimation-dispatch-prompt.md`.
3. Invoke the Task tool:
   - `subagent_type`: `generalPurpose`
   - `prompt`: Assemble from template with `{project-root}`, `{sprint_status}`, `{epics_path}`, `{story_dir}`, `{story_keys}` (newline-separated backlog keys)
   - `description`: `Estimate backlog stories using zone-estimator`
4. Wait for subagent to complete.
5. Parse subagent response (JSON object mapping story_key to estimation result).
6. Write the result to `_bmad-output/implementation-artifacts/story-estimates.yaml` (or path from `planning.estimates_file` in config).

**Parallelization:** Optionally dispatch one subagent per story (parallel) for faster results; each returns a single story's estimate, then aggregate into the YAML file.

**Fallback:** If estimation subagent is skipped (e.g. for quick iteration), the planner falls back to the keyword heuristic when `--estimates-file` is not provided.

### Phase 1b: Run Planner

Run planner with precomputed estimates:

```bash
python3 .claude/skills/zone-sprint/scripts/zone_sprint.py plan --repo-root /apps/gymops.global --estimates-file _bmad-output/implementation-artifacts/story-estimates.yaml
```

Or without estimates (uses keyword heuristic fallback):

```bash
python3 .claude/skills/zone-sprint/scripts/zone_sprint.py plan --repo-root /apps/gymops.global
```

Planner behavior:
1. Load backlog from `sprint-status.yaml` in epic/story order.
2. Infer dependency matrix from story sequencing in each epic.
3. Mark blocked and unblocked pending backlog stories.
4. Resolve target story points from config (or `--target-points` override).
5. Estimate Fibonacci story points: from `--estimates-file` (zone-estimator output mapped to Fibonacci) or keyword heuristic fallback.
6. Select sprint scope with epic-completion bias under target.
7. Output proposal payload including selected stories, wave order, and preflight checks.
8. Retain the `dependency_matrix` dict from the planner JSON output for use in Phase 5.5. This matrix is keyed by bmad_id and contains dependency/blocked-by relationships for all candidate stories.

## Phase 2: Confirm Scope With User

Present to user from the planner output:
1. Proposed sprint name, duration, and target points.
2. Selected epics/stories with points and dependencies.
3. Total selected points vs target.
4. Blocked stories and reasons.

Do not mutate files or GitHub Issues until user explicitly confirms.

## Phase 3: Freeze Confirmed Scope Inputs

After user confirmation:
1. Re-run `plan` deterministically to ensure selected scope is unchanged.
2. Capture selected Wave 1 story keys in epic/story order.
3. Confirm target files for story generation:
- `_bmad-output/implementation-artifacts/sprint-status.yaml`
- `_bmad-output/implementation-artifacts/stories/`

Important:
- Do not use `python3 .claude/skills/zone-sprint/scripts/zone_sprint.py apply` for story creation.
- Phase 4 is a hybrid workflow and must be executed by following the reference guide and invoking the python writer.

## Phase 4: Execute Story-Creator Workflow (Subagent Dispatch, Wave 1)

This phase dispatches each Wave 1 story to a separate generalPurpose subagent. Each subagent follows `.claude/skills/zone-sprint/references/story-creator.md` and invokes `story_writer.py`. The orchestrator does NOT execute the story-creator protocol inline.

Execution contract:
1. Load the story-creator dispatch prompt from `templates/story-creator-dispatch-prompt.md` (or use the inline structure below).
2. For each selected Wave 1 story key, invoke the Task tool:
   - `subagent_type`: `generalPurpose`
   - `prompt`: Assemble from template with `{story_key}`, `{project-root}` (e.g. `/apps/gymops.global`), `{story_dir}` = `_bmad-output/implementation-artifacts/stories`
   - `description`: `Create story {story_key}`
3. Dispatch all stories **in parallel** (invoke Task for each story key concurrently).
4. Wait for all subagents to complete (or fail).
5. On subagent failure: apply error semantics below.
6. Stop after story creation phase (no dev-dispatch/review/PR auto-progression).

Dispatch prompt must include:
- Mission: Create a BMAD story file by following the story-creator execution protocol
- Story key: Explicit `{story_key}` provided by orchestrator
- Protocol path: `.claude/skills/zone-sprint/references/story-creator.md`
- Branch: Use "specific story key provided by orchestrator" in Step 1; do NOT auto-discover
- Project root: `{project-root}`
- Output: Story file at `{story_dir}/{story_key}.md`, sprint-status updated via `story_writer.py`

Error and skip behavior:
1. Fail fast on hard-stop conditions from the reference workflow (for example missing required epic artifacts).
2. Warn and continue for non-fatal gaps explicitly marked WARN by the reference workflow.

Resume/Repair semantics:
1. Re-run workflow only for Wave 1 stories that are missing/incomplete/failed.
2. Skip stories already validated and already `ready-for-dev`.

## Phase 4.5: Commit Sprint Artifacts (Mandatory Before GitHub Issues)

Execute this step after Phase 4 story generation and before Phase 5 GitHub Issues updates.

1. Stage the following paths (relative to repo root):
   - `_bmad-output/implementation-artifacts/sprint-status.yaml`
   - `_bmad-output/implementation-artifacts/stories/`

2. Run:
   ```bash
   python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
     --message "chore(bmad): persist sprint stories and status before GitHub Issues updates" --repo-root .
   ```
   Stages all `_bmad-output/` changes (excludes `modules/`), commits, and pushes with retry. Skips automatically if no changes exist. Proceed to Phase 5.

3. Ensure commit completes successfully before invoking any GitHub Issues tooling.

## Phase 5: GitHub Issues Story Updates and Sprint Creation

Runs only after successful Phase 4 story generation.

1. Set story points for selected GitHub Issues stories. **Track each result** (success/failure and points value) for use in Phase 5.5:
```bash
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py set-estimation <board_id> <ISSUE-KEY> <POINTS>
```
2. Create sprint. **Capture the full JSON response** (especially `id`, `self`, and `state` fields) for use in Phase 5.5:
```bash
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py create-sprint <board_id> "<SPRINT_NAME>" --goal "<GOAL>" --start-date "<ISO>" --end-date "<ISO>"
```
3. Add selected issues to sprint:
```bash
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py add-to-sprint <sprint_id> <ISSUE-KEY...>
```
4. Verify sprint contents:
```bash
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py get-sprint-issues <sprint_id> --fields "key,summary,status"
```
5. Transition all selected Wave 1 issues from "To Do" to "Ready for Dev":
```bash
python3 .claude/skills/github-issues-agile/scripts/github-issues_agile.py transition-issue <ISSUE-KEY> "Ready for Dev" \
  --comment-format markdown --comment-stdin <<'EOF'
Sprint planned.

- Next status: `Ready for Dev`
- Notes: Story is ready for development
EOF
```
Run for each selected issue. Track success/failure per issue. If a transition fails for a specific issue (e.g., status is already beyond "To Do", or "Ready for Dev" is not a valid transition), log a warning and continue with remaining issues — do not fail the entire phase.

For dependency-matrix notes not supported by `github-issues_agile.py`, use Atlassian GitHub Issues MCP update/comment operations with planner output as source payload.

## Phase 5.5: Persist Sprint GitHub Issues Metadata and Push

Runs after Phase 5 GitHub Issues operations complete. Persists sprint metadata into `story-key-map.yaml` so the planner can compute correct sprint indices on subsequent runs.

**Step 1: Extract sprint ID** from the `create-sprint` JSON response captured in Phase 5 step 2. Required fields: `id`, `self`, `state`. If the sprint ID is unavailable (e.g. create-sprint failed or response was not captured), skip Phase 5.5 entirely and warn the user.

**Step 2: Build history entry** with this schema:

```yaml
sprint_planning_history:
  - sprint_index: 1
    persisted_at: "2026-02-25T14:30:00Z"
    github-issues_sprint_id: 42
    github-issues_sprint_url: "https://..."
    sprint_name: "Sprint 1 2026-02-25"
    sprint_goal: "Deliver highest-value unblocked stories..."
    start_date: "2026-02-25"
    end_date: "2026-03-10"
    state: "future"
    board_id: 298
    target_story_points: 43
    selected_story_points: 33
    issues:
      - github-issues_key: "CASDLC-9"
        bmad_id: "1.1"
        story_points_set: 3
    verification:
      status: "verified|partial|failed"
      issues_found_in_sprint: 2
      verified_at: "2026-02-25T14:32:00Z"
    dependency_matrix:
      "1.1":
        story_key: "1-1-some-slug"
        title: "Story title"
        dependencies: []
        blocked_by: []
        unblocked_at_plan_time: true
        selectable: true
        story_points: 3
      "1.2":
        story_key: "1-2-another-slug"
        title: "Another story"
        dependencies: ["1.1"]
        blocked_by: ["1.1"]
        unblocked_at_plan_time: false
        selectable: true
        story_points: 5
```

Field notes:
- `sprint_index`: Current sprint number (from planner output, i.e. `len(sprint_planning_history) + 1`).
- `persisted_at`: ISO-8601 UTC timestamp of when this entry is written.
- `github-issues_sprint_id`, `github-issues_sprint_url`, `state`: From the `create-sprint` response (`id`, `self`, `state`).
- `sprint_name`, `sprint_goal`, `start_date`, `end_date`, `board_id`: From planner output / Phase 5 inputs.
- `target_story_points`: The sprint budget from config/planner.
- `selected_story_points`: Sum of points for selected stories.
- `issues`: Populated from selected stories. `story_points_set` is the points value if `set-estimation` succeeded for that story, or `null` if it failed.
- `verification.status`: `"verified"` if all issues found in sprint, `"partial"` if some missing, `"failed"` if the verification call errored or returned zero issues.
- `verification.issues_found_in_sprint`: Count from Phase 5 step 4 (`get-sprint-issues`).
- `verification.verified_at`: ISO-8601 UTC timestamp of verification.
- `dependency_matrix`: Full `dependency_matrix` dict from the planner output (retained in Phase 1b step 8), keyed by bmad_id. Include only entries for stories that were candidates (backlog) at plan time — not done/skipped stories.

**Step 3: Append** the entry to `projects.<project_key>.sprint_planning_history` in `_bmad-output/implementation-artifacts/story-key-map.yaml`. Create the `sprint_planning_history` list if absent. Also update `last_synced_at` at the project level. Do not modify `items` or other existing sections.

**Step 4: Commit and Push**

Replace `N` with the actual sprint index, then run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "chore(bmad): persist GitHub Issues sprint metadata [sprint-N]" --repo-root .
```
Stages all `_bmad-output/` changes (excludes `modules/`), commits, and pushes with retry. Skips automatically if no changes exist. If push ultimately fails, the script emits a JSON error — report the failure to the user.

**Error handling**: If the YAML write fails, print the full history entry as YAML to stdout so the user can manually append it to `story-key-map.yaml`.

## Implementation Notes

1. Read dependency rules from `references/dependency-rules.md`.
2. Read estimation rules from `references/estimation-rules.md` (zone-estimator + effort-to-points mapping; fallback keyword heuristic).
3. Phase 1a estimation prompt: `templates/estimation-dispatch-prompt.md`; zone-estimator skill: `.claude/skills/zone-estimator/SKILL.md`.
4. Keep deterministic output for same inputs.
5. Preserve mapping namespaces by project key; never overwrite other project sections.
6. Phase 4 execution authority is `references/story-creator.md`.
