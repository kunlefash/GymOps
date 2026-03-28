---
name: zone-bug-fix
description: Captures bug requirements via BMAD quick-spec workflow, registers the bug in pipeline artifacts (epics.md, sprint-status.yaml, story-key-map.yaml), creates a GitHub Issues Bug issue, and publishes the spec to planning-artifacts. Bridges bug fixes into zone-prepare-story → zone-dev → zone-code-review without modifying downstream skills.
---

# Zone Bug Fix

Capture bug requirements through the BMAD quick-spec conversational workflow, then register the bug in all pipeline artifacts so it flows through the standard story preparation and development pipeline.

## Git Contract

Every `commit-planning` call in this skill **stages, commits, AND pushes to remote** in a single operation. The underlying `zone_dev.py commit-planning` command:
1. Stages all `_bmad-output/` changes (resets any staged `modules/` paths)
2. Commits with the provided message
3. **Pushes to remote** via `git_push_with_retry()` (rebase-first, merge-fallback, 5 retries with linear backoff)
4. Skips automatically if no staged changes exist

**Every phase that commits MUST verify the push succeeded.** If the push ultimately fails after retries, halt and inform the user.

---

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py sync-repo --repo-root .
```

Pulls the latest repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**On failure:** Stop and inform the user that the repo sync failed — the branch may be behind or have unresolved conflicts. The user must resolve these manually before re-running this skill.

---

## Phase 1: Config Loading + Snapshot

1. Load `{project-root}/_bmad/bmm/config.yaml` and store session variables: `{user_name}`, `{communication_language}`, `{planning_artifacts}`, `{implementation_artifacts}`, `{project_name}`
2. Greet the user by `{user_name}`, speaking in `{communication_language}`, and inform them the bug-fix workflow is starting
3. **Snapshot output directory**: Record the current state of `{planning_artifacts}/` — list all files matching `bugfix-*.md` with their modification timestamps. Store as session variable `{pre_workflow_snapshot}`. This is used in Phase 5 to identify only new/modified artifacts.

---

## Phase 2: BMAD Quick-Spec Workflow

1. Load and follow `{project-root}/_bmad/bmm/workflows/bmad-quick-flow/quick-spec/workflow.md`
2. Obey all step-file architecture rules: micro-file design, just-in-time loading, sequential enforcement
3. Never load multiple step files simultaneously
4. Halt at menus and wait for user input

### Bug-Specific Guidance for Step 1 (Requirement Delta)

When executing Step 1 (`step-01-understand.md`), inject these bug-specific modifications:

- **Opening question**: Ask "What bug are we fixing?" instead of "What are we building?"
- **Required capture fields** (collect during the conversational discovery):
  - **Steps to Reproduce**: Numbered sequence to trigger the bug
  - **Expected Behavior**: What should happen
  - **Actual Behavior**: What happens instead
  - **Severity**: Critical / High / Medium / Low
  - **Affected Modules**: Which `modules/` modules are involved (e.g., `zone.gymops`, `src/services`)
- Frame the "requirement delta" as: current (buggy) state → expected (fixed) state
- The investigation in Step 2 should focus on root cause analysis rather than feature design

### After Step 4 Finalization

After the quick-spec workflow completes Step 4 (finalization with `status: ready-for-dev`):

1. **Copy** the finalized tech-spec to `{planning_artifacts}/bugfix-{slug}.md` where `{slug}` is derived from the bug title (lowercase, hyphens, no special chars)
2. **Augment the frontmatter** of the copied file with bug-specific metadata:
   ```yaml
   type: bug-fix
   severity: "{severity}"
   affected_modules:
     - "{module1}"
     - "{module2}"
   ```
3. Store `{slug}`, `{title}`, `{severity}`, `{affected_modules}`, `{steps_to_reproduce}`, `{expected_behavior}`, `{actual_behavior}`, `{root_cause}`, `{acceptance_criteria}` as session variables for later phases

---

## Phase 2.5: Commit Quick-Spec Artifacts

Run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "docs(bugfix): add bug fix spec for {slug}" --repo-root .
```

Stages all `_bmad-output/` changes (excludes `modules/`), commits, and pushes with retry. Skips automatically if no changes exist.

---

## Phase 3: Register Bug in Pipeline Artifacts

This is the critical bridging phase. Uses **Epic 99** as the reserved bug-fix epic, with numeric `99.{N}` BMAD IDs for full compatibility with zone-sprint's regex patterns.

### 3.1: Generate BMAD ID

1. Resolve `{planning_artifacts}/epics.md`
2. If the file exists, scan for `## Epic 99: Bug Fixes` section
3. Find all `### Story 99.{N}:` headers within that section, take highest N + 1
4. If no `## Epic 99:` section exists, the first bug is `99.1`
5. If `epics.md` does not exist at all, create it (see Missing File Handling below) — first bug is `99.1`
6. Store as `{bmad_id}` (e.g., `99.1`) and `{N}` (e.g., `1`)

### 3.2: Append Bug Entry to epics.md

If `## Epic 99: Bug Fixes` section is missing from `epics.md`, append the section header at the end of the file:

```markdown

## Epic 99: Bug Fixes

This epic tracks bug fixes that flow through the standard story preparation and development pipeline.
```

Then append the story entry under the `## Epic 99: Bug Fixes` section:

```markdown

### Story 99.{N}: {title}

**Bug Summary:** {problem_statement}

**Repo:** modules/{module1}
**Repo:** modules/{module2}

**Steps to Reproduce:**
{steps_to_reproduce}

**Expected Behavior:** {expected_behavior}
**Actual Behavior:** {actual_behavior}
**Root Cause Analysis:** {root_cause}

**Acceptance Criteria:**
{acceptance_criteria_in_given_when_then}

**Severity:** {severity}
**Tech Spec:** {implementation_artifacts}/tech-spec-{slug}.md
```

Compatibility notes:
- `## Epic 99:` matches `EPIC_HEADING_RE = r"^##\s+Epic\s+(\d+):\s*(.+?)\s*$"` in `zone_sprint.py:21`
- `### Story 99.{N}:` matches `STORY_HEADING_RE = r"^###\s+Story\s+(\d+)\.(\d+):\s*(.+?)\s*$"` in `zone_sprint.py:22`
- `### Story 99.{N}:` matches regex in `zone_prepare_story.py:325`: `rf"### Story {re.escape(bmad_id)}:\s*.*"`
- `**Repo:** modules/{name}` enables domain skill resolution

### 3.3: Add to sprint-status.yaml

1. Resolve `{implementation_artifacts}/sprint-status.yaml`
2. If the file does not exist, create it (see Missing File Handling below)
3. Under `development_status`:
   - Add `epic-99: backlog` if not already present
   - Add `epic-99-retrospective: optional` if not already present
   - Add `{story_key}: backlog` where `{story_key} = "99-{N}-{slugified_title}"` (e.g., `99-1-payment-timeout-on-retry`)

The `{story_key}` derivation:
- Take `{bmad_id}` → replace `.` with `-` → `99-{N}`
- Append `-{slugified_title}` (lowercase, hyphens, no special chars)
- Example: bmad_id `99.1`, title "Payment Timeout on Retry" → story_key `99-1-payment-timeout-on-retry`

This satisfies:
- `zone_prepare_story.py:250`: `dev_status.get(story_key)` must be `backlog`
- `zone_sprint.py:237`: `STORY_KEY_RE = r"^(\d+)-(\d+)-"` matches `99-1-...`

### 3.4: Commit Pipeline Registration

Run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "chore(bugfix): register {bmad_id} in pipeline (epics.md + sprint-status.yaml)" --repo-root .
```

---

## Phase 4: GitHub Issues Bug Creation

### 4.1: Load Skill Config

Read `config.yaml` from this skill's directory and resolve:
- `github-issues.atlassian_server`
- `github-issues.project_key`
- `github-issues.bug_issue_type`
- `github-issues.upsert_strategy`
- `github-issues.mapping_file`
- `github-issues.require_acceptance_criteria`
- `github-issues.embed_references_inline`
- `github-issues.persist_urls`

### 4.2: Confirm GitHub Issues Project Key

Present the resolved `github-issues.project_key` to the user and require confirmation or override before any GitHub Issues write. If the user declines, skip GitHub Issues creation and proceed to Phase 5.

### 4.3: Resolve Atlassian Cloud Context

Using MCP server `github-issues.atlassian_server`:
1. Call `getAccessibleAtlassianResources` and extract `cloudId`
2. If access fails, stop GitHub Issues sync with clear error and proceed to Phase 5

### 4.4: Create or Update GitHub Issues Bug Issue

**Summary:** `Bug {bmad_id}: {title}`

**Description body** (same structure as zone-epics):

```markdown
## BMAD Source
- BMAD Type: bug
- BMAD ID: {bmad_id}
- Source File: {planning_artifacts}/epics.md

## Bug Summary
{problem_statement}

## Steps to Reproduce
{steps_to_reproduce}

## Expected Behavior
{expected_behavior}

## Actual Behavior
{actual_behavior}

## Root Cause Analysis
{root_cause}

## Acceptance Criteria
{acceptance_criteria_in_given_when_then}

## Severity
{severity}

## Affected Modules
{affected_modules_list}
```

**Upsert logic:**
1. Search first via `searchGitHub IssuesIssuesUsingJql`:
   ```
   project = "{project_key}" AND summary ~ "Bug {bmad_id}:" AND issuetype = "{bug_issue_type}"
   ```
2. If found: update the existing issue
3. If not found: create a new issue with issue type `github-issues.bug_issue_type`
4. Capture resulting `{github-issues_key}` and `{github-issues_url}`

### 4.5: Persist to story-key-map.yaml

1. Resolve `{implementation_artifacts}/story-key-map.yaml`
2. If the file does not exist, create it (see Missing File Handling below)
3. Load existing content

**Add epic 99 entry** (if not already present):
```yaml
- bmad_type: epic
  bmad_id: "99"
  bmad_title: "Bug Fixes"
  github-issues_key: ""
  github-issues_issue_type: "Epic"
```

**Add the bug story entry:**
```yaml
- bmad_type: story
  bmad_id: "99.{N}"
  bmad_title: "{title}"
  github-issues_key: "{github-issues_key}"
  github-issues_issue_type: "Bug"
  github-issues_url: "{github-issues_url}"
  parent_github-issues_key: ""
  parent_bmad_id: "99"
```

**Critical:** Use `bmad_type: story` — all 5 downstream scripts (`zone_prepare_story.py`, `zone_qa.py`, `zone_review.py`, `zone_dev.py`, `zone_sprint.py`) filter on `bmad_type == "story"`.

Merge rules:
- Namespace under `projects.<PROJECT_KEY>.items`
- Upsert by composite key: `(bmad_type, bmad_id)`
- Preserve entries for other project keys unchanged
- Update `active_project_key` to the confirmed project key

### 4.6: Commit GitHub Issues Mapping

Run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "chore(bugfix): persist story key mapping for {bmad_id}" --repo-root .
```

---

## Phase 5: planning-artifacts Publish

Identical pattern to zone-prd Phase 3 (sections 3.1–3.10).

### 5.0 Load Config

Read `config.yaml` from this skill's directory to obtain:
- `planning-artifacts.space_key` (default: `PMT`)
- `planning-artifacts.parent_page_id` (optional)
- `planning-artifacts.title_template` (resolve `{project_name}` from BMAD config)

### 5.1 Discover Artifacts and Confirm

Scan `{planning_artifacts}/` for `bugfix-*.md` files. Compare against `{pre_workflow_snapshot}` (recorded in Phase 1 step 3). Only files that are **new** or have a **newer modification timestamp** are candidates for publishing.

Build a list of documents to publish, each with a derived title:

| Filename pattern | Derived title |
|------------------|---------------|
| `bugfix-{name}.md` | `"{project_name} - Bug Fix {humanized_name}"` (strip `bugfix-` prefix, replace hyphens with spaces, title-case) |

**CRITICAL:** Before creating or updating any planning artifacts:

1. Present the discovered files and their derived titles to the user
2. Ask the user to confirm or override any titles
3. Confirm: **Target space key** (show default from config, allow override) and **Publish now or skip**
4. If the user declines publishing, skip to Phase 6

### 5.2 Resolve Atlassian Cloud ID

Call `getAccessibleAtlassianResources` via the Atlassian MCP (server: `Atlassian`). Extract the `cloudId` from the response. (Reuse from Phase 4 if already resolved.)

### 5.3 Resolve Space ID

Call `getplanning-artifactsSpaces` with `cloudId` and `keys: ["<space_key>"]`. Extract the `spaceId` for the target space.

### 5.4–5.6 For Each Output Document

Repeat steps 5.4 through 5.6 for each discovered document in the publish list.

#### 5.4 Parse Document into Sections

Read the document. Split the markdown at each `## ` (H2) heading boundary:
- **Preamble**: everything before the first H2 (title, author, date, frontmatter)
- **Sections**: each H2 block has a heading (the text after `## `) and a body (all content until the next H2 or end of file)

Identify the **Bug Summary** section (heading contains "Bug Summary"). All other H2 sections become child pages. Skip sections with empty bodies.

#### 5.5 Create or Update the Main Page

Search for the main page via `searchplanning-artifactsUsingCql`:
```
cql: title = "<derived_title>" AND space.key = "<space_key>" AND type = page
```

Build the main page body from three parts:
1. The **preamble** (title block, metadata, frontmatter)
2. The **Bug Summary** section content (include the H2 heading)
3. A **Table of Contents** heading (`## Contents`) followed by a markdown bulleted list where each item links to a child page title

**If a matching main page is found:** call `updateplanning-artifactsPage` with `pageId`, assembled body, `contentFormat: "markdown"`, and `versionMessage` with timestamp. Store `pageId` as `mainPageId`.

**If not found:** call `createplanning-artifactsPage` with `spaceId`, `title`, assembled body, `contentFormat: "markdown"`, and optional `parentId` from config. Store the returned page ID as `mainPageId`.

#### 5.6 Create or Update Child Pages

For each remaining section (every H2 except Bug Summary), skip sections with empty bodies.

For each section:

1. **Search for existing child page** via `searchplanning-artifactsUsingCql`:
   ```
   cql: ancestor = <mainPageId> AND title = "<Section Heading>" AND type = page
   ```
2. **If found:** call `updateplanning-artifactsPage` with `pageId`, section markdown body, `contentFormat: "markdown"`, `versionMessage` with timestamp
3. **If not found:** call `createplanning-artifactsPage` with:
   - `spaceId`
   - `title`: the section heading as-is (e.g., "Steps to Reproduce") — no project name prefix
   - `body`: the section markdown content
   - `contentFormat: "markdown"`
   - `parentId`: `mainPageId`

### 5.7 Confirm

Report all main page URLs and their child page URLs to the user for each published document.

### 5.8 Tag Documents with planning-artifacts Metadata

After a successful planning-artifacts publish, tag **each** published local document with planning-artifacts space and page ID for easy retrieval:

For each published document:

1. Ensure you have: `space_key` (from config), `mainPageId` (from 5.5 for this document), and the planning-artifacts base URL
2. Read the workflow output file and parse its existing YAML frontmatter
3. Add or update a `planning-artifacts` block in the frontmatter:
   ```yaml
   planning-artifacts:
     space_key: "<space_key>"
     main_page_id: "<mainPageId>"
     main_page_url: "<constructed_url>"
   ```
4. Write the file back, preserving all existing frontmatter and body content
5. If the user declined publishing (skipped 5.1), skip this step

### 5.9 Commit planning-artifacts Tagging Changes

If 5.8 was skipped (user declined publish), skip this step. Otherwise run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "docs(bugfix): add planning-artifacts link metadata for {slug}" --repo-root .
```

---

## Phase 6: Summary + Next Steps

### Report

Present a summary table to the user:

| Item | Value |
|------|-------|
| Bug Spec | `{planning_artifacts}/bugfix-{slug}.md` |
| Tech Spec | `{implementation_artifacts}/tech-spec-{slug}.md` |
| BMAD ID | `{bmad_id}` |
| Story Key | `{story_key}` |
| GitHub Issues Key | `{github-issues_key}` |
| GitHub Issues URL | `{github-issues_url}` |
| planning-artifacts URL | `{planning-artifacts_main_page_url}` |
| Sprint Status | `{story_key}: backlog` |

### Next Steps

```
1. Run `zone-prepare-story {github-issues_key}` → generates story file
2. (Optional) Run `zone-qa {github-issues_key} --qa-mode atdd` → generates failing acceptance tests
3. Run `zone-dev {github-issues_key}` → implements the fix
4. (Optional) Run `zone-qa {github-issues_key} --qa-mode automation` → expands test coverage
5. Run `zone-code-review {github-issues_key}` → reviews implementation
6. Run `zone-test-review {github-issues_key}` → reviews test quality, creates PRs on PASS
```

---

## Missing File Handling

Phase 3 must handle the case where pipeline artifacts don't yet exist.

### If `epics.md` does not exist

Create `{planning_artifacts}/epics.md` with minimal content:

```markdown
# Epics and Stories

## Epic 99: Bug Fixes

This epic tracks bug fixes that flow through the standard story preparation and development pipeline.

### Story 99.1: {title}
...
```

(The `...` represents the full story entry as defined in 3.2.)

### If `sprint-status.yaml` does not exist

Create `{implementation_artifacts}/sprint-status.yaml` with:

```yaml
development_status:
  epic-99: backlog
  epic-99-retrospective: optional
  {story_key}: backlog
```

### If `story-key-map.yaml` does not exist

Create `{implementation_artifacts}/story-key-map.yaml` with the full project structure:

```yaml
generated_at: "{iso_timestamp}"
active_project_key: "{project_key}"
projects:
  {project_key}:
    last_synced_at: "{iso_timestamp}"
    source_epics_file: "_bmad-output/planning-artifacts/epics.md"
    items:
      - bmad_type: epic
        bmad_id: "99"
        bmad_title: "Bug Fixes"
        github-issues_key: ""
        github-issues_issue_type: "Epic"
      - bmad_type: story
        bmad_id: "99.{N}"
        bmad_title: "{title}"
        github-issues_key: "{github-issues_key}"
        github-issues_issue_type: "Bug"
        github-issues_url: "{github-issues_url}"
        parent_github-issues_key: ""
        parent_bmad_id: "99"
```

### If `_bmad-output/` directories don't exist

Create both `_bmad-output/planning-artifacts/` and `_bmad-output/implementation-artifacts/` (and `stories/` subdirectory) before writing any files.

---

## Failure Handling

1. If repo sync fails: stop and inform user
2. If quick-spec workflow fails at any step: allow user to retry that step or abort
3. If `epics.md` parsing fails (unexpected format): show the offending content and ask user how to proceed
4. If GitHub Issues access fails: skip GitHub Issues creation, warn user, proceed to planning-artifacts
5. If planning-artifacts publish fails: warn user, complete Phase 6 summary without planning-artifacts URL
6. If any `commit-planning` push fails after retries: halt and inform the user

## Guardrails

- Follow BMAD workflow step sequencing exactly during Phase 2
- Require GitHub Issues project key confirmation before any GitHub Issues writes
- Always use `bmad_type: story` in story-key-map.yaml for bug entries (never `bmad_type: bug`)
- Always use numeric BMAD IDs under Epic 99 (`99.1`, `99.2`, etc.) for regex compatibility
- Never modify existing epic/story entries in `epics.md` — only append under `## Epic 99:`
- Never modify existing entries in `sprint-status.yaml` — only add new keys
- Preserve all existing `story-key-map.yaml` project namespaces when adding bug entries
