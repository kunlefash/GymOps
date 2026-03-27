# Story Creator -- BMAD Phase 4 Story Generation

> Wraps the BMAD `create-story` workflow to autonomously generate comprehensive story files with full developer context. May be invoked as a subagent by the zone-sprint orchestrator (supports parallel execution).

## Purpose

This engine file creates the next story from the backlog, loading all BMAD-required context (epics, architecture, PRD, UX, previous stories, git history) and producing a story file that gives the dev subagent everything needed for flawless implementation. It follows the BMAD create-story workflow without modifying any `_bmad/` files.

## Pre-Conditions

- `sprint-status.yaml` exists (run sprint-planner first if not)
- At least one story in `backlog` status
- BMAD planning artifacts (epics, architecture, PRD) exist in `_bmad-output/planning-artifacts/`

## Execution Protocol

When this engine file is invoked, the executing agent MUST follow these steps exactly:

### Step 1: Load Configuration and Determine Target Story

```
1. Read {project-root}/_bmad/bmm/config.yaml -> resolve all variables
2. Read {project-root}/.claude/skills/zone-sprint/config.yaml (if exists) -> resolve execution paths
3. Set {sprint_status} = {project-root}/_bmad-output/implementation-artifacts/sprint-status.yaml
4. Set {story_dir} = {project-root}/_bmad-output/implementation-artifacts/stories

5. If a specific story key was provided by the orchestrator:
   - Parse the story key (e.g., "1-2-user-authentication")
   - Extract epic_num, story_num, story_title
   - GOTO Step 2

6. Otherwise, auto-discover from sprint-status.yaml:
   - Read the COMPLETE sprint-status.yaml file
   - Find the FIRST story (top to bottom) where:
     * Key matches pattern: number-number-name
     * NOT an epic key or retrospective
     * Status equals "backlog"
   - If no backlog story found: HALT -- all stories created or sprint complete
   - Extract epic_num, story_num, story_key from found entry
```

### Step 2: Multi-User Coordination (optional)

```
If coordination/locking is not used, skip this step and proceed to Step 3.
```

### Step 3: Mark Epic In-Progress (if first story in epic)

```
1. Check if this is the first story in epic {epic_num}
   - Look for pattern {epic_num}-1-* in the story key
2. If first story AND epic status is "backlog":
   - Update sprint-status.yaml: epic-{epic_num} = "in-progress"
3. If epic is "done": HALT -- cannot create story in completed epic
```

### Step 4: Exhaustive Artifact Analysis

**CRITICAL: This is the most important step. Thorough context prevents developer mistakes.**

Use parallel subagents (generalPurpose type) to analyze artifacts simultaneously:

#### 4a. Epic Analysis
```
1. Load epic files from {planning_artifacts}/
2. Extract Epic {epic_num} complete context:
   - Epic objectives and business value
   - ALL stories in this epic (cross-story context)
   - Target story requirements, user story statement, ACs
   - Technical requirements and constraints
   - Dependencies on other stories/epics
```

#### 4b. Architecture Analysis
```
1. Load architecture document from {planning_artifacts}/
   - Could be single file or sharded to folder
2. Extract story-relevant requirements:
   - Technical stack (languages, frameworks, versions)
   - Code structure (folder organization, naming conventions)
   - API patterns, database schemas, security requirements
   - Performance requirements, testing standards
   - Integration patterns
```

#### 4c. PRD and UX Analysis
```
1. Load PRD from {planning_artifacts}/ (if exists)
2. Load UX design from {planning_artifacts}/ (if exists)
3. Extract story-relevant user flows, wireframes, interaction patterns
```

#### 4d. Previous Story Intelligence (optional for parallel execution)
```
If story_num > 1:
1. Check if previous story file exists at {story_dir}/{epic_num}-{previous_num}-*.md
2. If it EXISTS: load and extract:
   - Dev notes and learnings
   - Review feedback and corrections
   - Files created/modified and patterns used
   - Testing approaches that worked/didn't
   - Problems encountered and solutions found
3. If it does NOT exist (e.g. parallel execution): proceed without previous story intelligence.
   Add WARN to Dev Notes Known Pitfalls: "Previous story not yet created; run sequentially for cross-story context."
```

#### 4e. Git Intelligence
```
If previous story file exists AND git repository detected:
1. Get last 5 commit titles
2. Analyze recent commits for:
   - Files created/modified
   - Code patterns and conventions used
   - Library dependencies added/changed
   - Architecture decisions implemented
Otherwise skip this step.
```

#### 4f. Known Pitfalls / Pattern Injection
```
1. If a known-pitfalls or patterns file exists at .claude/skills/zone-sprint/references/known-pitfalls.md (or similar path), read it
2. Extract patterns relevant to the affected modules (from epic/architecture analysis)
3. Include as "Known Pitfalls" in story Dev Notes
4. Otherwise omit Known Pitfalls or leave empty
```

### Step 5: Web Research for Latest Tech Specifics

```
1. From architecture analysis, identify specific libraries/frameworks
2. For each critical technology, use Context7 or web search:
   - Latest stable version and key changes
   - Security vulnerabilities or updates
   - Deprecations and migration considerations
3. Include findings in story Dev Notes
```

### Step 5.5: Golden Example Reference

```
1. Read `.claude/skills/zone-sprint/references/good-story-example.md`
2. This file sets the MANDATORY baseline for information density, technical depth, and strict formatting. Do NOT summarize or shorten your output to be less detailed than this example.
```

### Step 6: Assemble Story Parameters

```
1. Assemble the following components in memory based on your exhaustive analysis, matching the detail level of the golden example:
   
   A. User Story Statement:
      - As a [role], I want [action], So that [benefit].
   
   B. Acceptance Criteria:
      - Sourced strictly from epics and PRD. BDD formatted (`Given/When/Then`).
      - MUST explicitly cover EVERY distinct user role, edge case, and error state mentioned in the PRD's RBAC matrix or functional requirements.

   C. Tasks / Subtasks:
      - MUST be categorized into explicit implementation headers across the stack. Example headers:
        * Task 1: Backend
        * Task 2: Dashboard (React)
        * Task 3: PWA (Next.js)
        * Task 4: Tests
      - Under each header, provide specific, prescriptive checklist items.
   
   D. Dev Notes (Comprehensive):
      - This section must replace everything between Tasks and the Dev Agent Record.
      - MUST include the following mandatory subsections exactly as formatted in the golden example:
        * `### Architecture Requirements` (Multi-tenant constraints, integration notes)
        * `### Security Constraints` (RBAC, Vault, data isolation)
        * `### Library/Framework Versions`
        * `### NuGet Package Dependencies` (if `{nuget_deps}` context was provided by the orchestrator)
        * `### File Structure Targets` (List every targeted file using `[NEW]` or `[MODIFY]` tags. Every file MUST have a short 1-sentence summary explaining why it is touched. See golden example.)
        * `### Testing Requirements`
        * `### Cross-Story Dependencies` (If applicable)
        * `### Known Pitfalls`
        * `### Project Structure Notes` (Alignment with standard structure, detected conflicts)
        * `### References` (Cite all technical details with source paths and sections. Example: `- [Source: docs/architecture/prd.md#Section]`)

      **NuGet Package Dependencies assembly** (only when `{nuget_deps}` is provided):
      - After `### Library/Framework Versions`, add `### NuGet Package Dependencies`
      - For each entry in `{nuget_deps}.dependencies`, include:
        * **Source:** {upstream_repo} ({build_tag})
        * **Resolved Version:** {resolved_version}
        * **Branch:** {branch}
        * List each package with `→ {resolved_version}`
        * If `resolved_version` is null: use "TBD — resolve at implementation time via `nuget-resolver` skill"
        * Footer: "If build fails due to missing package, wait 2 minutes and retry (CI may still be publishing)."

2. Write these components EXACTLY as formulated into temporary files in `/tmp/`:
   - `/tmp/statement.txt`
   - `/tmp/ac.txt`
   - `/tmp/tasks.txt`
   - `/tmp/dev-notes.txt`
```

### Step 6.5: Create Story File via Utility

```
1. Execute the `story_writer.py` utility to format the file and update status:
   ```bash
   python3 .claude/skills/zone-sprint/scripts/story_writer.py write <story_key> \
       --repo-root {project-root} \
       --title "<story_title>" \
       --statement-file /tmp/statement.txt \
       --ac-file /tmp/ac.txt \
       --tasks-file /tmp/tasks.txt \
       --dev-notes-file /tmp/dev-notes.txt
   ```
```

### Step 7: Validate Story Quality

```
Note: sprint-status.yaml is automatically updated by the story_writer script.

1. Read BMAD checklist:
   {project-root}/_bmad/bmm/workflows/4-implementation/create-story/checklist.md
2. Validate the generated `{story_dir}/{story_key}.md`:
   - [ ] Story has clear user story statement
   - [ ] All ACs are specific, testable, and cover ALL relevant roles exhaustively
   - [ ] Tasks/subtasks are categorized by stack layers (Backend, Dashboard, PWA, Tests)
   - [ ] Dev Notes include Architecture, File Structure Targets, and Library Versions
   - [ ] Previous learnings are incorporated
   - [ ] Testing requirements are clear
3. PROGRAMMATIC GATE: If validation fails (e.g. missing categorized headers, skipped a role in ACs, or summarized too heavily compared to the golden example), you MUST rewrite the temporary files and re-run `story_writer.py` to fix the issues before proceeding.
```

### Step 8: Update Sprint Status

```
Note: This step is now handled automatically by `story_writer.py`.
You only need to verify that `sprint-status.yaml` reflects the status changes:
1. Story status changed to `ready-for-dev`
2. Epic status changed to `in-progress` (if it was `backlog`)
```

### Step 9: Report and Hand Off

```
Output:
- Story ID, key, file path
- Status: ready-for-dev
- Summary of context loaded
- Known pitfalls injected (if any)
```

## Post-Conditions

- Story file exists at `{story_dir}/{story_key}.md` with comprehensive context
- `sprint-status.yaml` updated: story marked as `ready-for-dev`
- Epic marked as `in-progress` if this is its first story
- The dev-dispatcher has everything needed to implement the story

## Error Handling

| Condition | Action |
|-----------|--------|
| No backlog stories | HALT -- sprint complete or run sprint-planner |
| Epic files not found | HALT -- run BMAD Phase 2-3 first |
| Architecture doc missing | WARN -- create story with available context, note gap |
| Previous story not found | WARN -- proceed without previous story intelligence (expected in parallel mode) |
| Story file already exists | Check if status allows re-creation, warn if overwriting |
