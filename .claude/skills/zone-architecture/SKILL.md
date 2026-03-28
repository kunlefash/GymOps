---
name: zone-architecture
description: Activates the Architect agent persona, runs the BMAD create-architecture workflow, and publishes the resulting architecture document to planning-artifacts. Use when creating a new architecture or updating an existing one and pushing it to planning-artifacts as part of Zone's Agentic SDLC process.
---

# Zone Architecture

Create a comprehensive architecture document through the BMAD workflow under the Architect agent persona, then publish it to planning-artifacts.

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py sync-repo --repo-root .
```

Pulls the latest repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**On failure:** Stop and inform the user that the repo sync failed — the branch may be behind or have unresolved conflicts. The user must resolve these manually before re-running this skill.

---

## Phase 1: Architect Agent Persona Activation

Before running the workflow, adopt the Architect persona.

1. Load the full agent file at `{project-root}/_bmad/bmm/agents/architect.md`
2. Adopt the persona: **Winston**, System Architect -- including role, identity, communication_style, and principles defined in that file
3. Load `{project-root}/_bmad/bmm/config.yaml` and store session variables: `{user_name}`, `{communication_language}`, `{output_folder}`, `{planning_artifacts}`, `{project_name}`
4. Greet the user by `{user_name}`, speaking in `{communication_language}`, using the Architect's communication style
5. Inform the user the create-architecture workflow is starting -- skip the full Architect menu and go straight to the create-architecture workflow
6. **Snapshot output directory**: Before the workflow begins, record the current state of `{planning_artifacts}/` — list all files matching `architecture*.md` with their modification timestamps. Store as session variable `{pre_workflow_snapshot}`. This is used in Phase 3 to identify only new/modified artifacts.

Key persona attributes to maintain throughout all phases:

| Attribute | Value |
|-----------|-------|
| Role | System Architect + Technical Design Leader |
| Style | Calm, pragmatic tones; balances "what could be" with "what should be" |
| Principles | User journeys drive technical decisions. Embrace boring technology for stability. Design simple solutions that scale when needed. Developer productivity is architecture. Connect every decision to business value and user impact |

## Phase 2: BMAD Create-Architecture Workflow

1. Load and follow `{project-root}/_bmad/bmm/workflows/3-solutioning/create-architecture/workflow.md`
2. Obey all step-file architecture rules: micro-file design, just-in-time loading, sequential enforcement
3. Never load multiple step files simultaneously
4. Halt at menus and wait for user input
5. Architecture output file: `{planning_artifacts}/architecture.md`
6. Maintain the Architect persona throughout all 8 steps

## Phase 3: planning-artifacts Publish

After step 8 (workflow completion) finishes, execute this publish sequence.

### 3.0 Commit Workflow Changes

Run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "docs(architecture): add/update architecture document" --repo-root .
```
Stages all `_bmad-output/` changes (excludes `modules/`), commits, and pushes with retry. Skips automatically if no changes exist.

### 3.1 Load Config

Read `config.yaml` from this skill's directory to obtain:
- `planning-artifacts.space_key` (default: `CAS`)
- `planning-artifacts.parent_page_id` (optional)
- `planning-artifacts.title_template` (resolve `{project_name}` from BMAD config)

### 3.2 Discover Artifacts and Confirm

Scan `{planning_artifacts}/` for `architecture*.md` files. Compare against `{pre_workflow_snapshot}` (recorded in Phase 1 step 6). Only files that are **new** or have a **newer modification timestamp** are candidates for publishing. This prevents republishing stale artifacts from previous workflow runs.

Build a list of documents to publish, each with a derived title:

| Filename pattern | Derived title |
|------------------|---------------|
| `architecture.md` | `"{project_name} - Architecture"` (matches existing `title_template`) |
| Any other `architecture*.md` | Derive title from filename: strip `architecture` prefix, replace hyphens with spaces, title-case, prepend `"{project_name} - "` |

**CRITICAL:** Before creating or updating any planning artifacts:

1. Present the discovered files and their derived titles to the user
2. Ask the user to confirm or override any titles
3. Confirm: **Target space key** (show default from config, allow override) and **Publish now or skip**
4. If the user declines publishing, stop here

### 3.3 Resolve Atlassian Cloud ID

Call `getAccessibleAtlassianResources` via the Atlassian MCP (server: `Atlassian`). Extract the `cloudId` from the response.

### 3.4 Resolve Space ID

Call `getplanning-artifactsSpaces` with `cloudId` and `keys: ["<space_key>"]`. Extract the `spaceId` for the target space.

### 3.5–3.7 For Each Output Document

Repeat steps 3.5 through 3.7 for each discovered document in the publish list.

#### 3.5 Parse Document into Sections

Read the document. Split the markdown at each `## ` (H2) heading boundary:
- **Preamble**: everything before the first H2 (frontmatter, title, intro text)
- **Sections**: each H2 block has a heading (the text after `## `) and a body (all content until the next H2 or end of file)

All H2 sections become child pages. Skip sections with empty bodies.

#### 3.6 Create or Update the Main Page

Search for the main page via `searchplanning-artifactsUsingCql`:
```
cql: title = "<derived_title>" AND space.key = "<space_key>" AND type = page
```

Build the main page body from two parts:
1. The **preamble** (frontmatter, title block, intro text)
2. A **Table of Contents** heading (`## Contents`) followed by a markdown bulleted list where each item links to a child page title

TOC format example:
```markdown
## Contents

- [System Context](System Context)
- [Technology Selection](Technology Selection)
- [Architectural Decisions](Architectural Decisions)
- [Implementation Patterns](Implementation Patterns)
- [Project Structure & Boundaries](Project Structure & Boundaries)
- [Validation](Validation)
```

**If a matching main page is found:** call `updateplanning-artifactsPage` with `pageId`, assembled body, `contentFormat: "markdown"`, and `versionMessage` with timestamp. Store `pageId` as `mainPageId`.

**If not found:** call `createplanning-artifactsPage` with `spaceId`, `title`, assembled body, `contentFormat: "markdown"`, and optional `parentId` from config. Store the returned page ID as `mainPageId`.

#### 3.7 Create or Update Child Pages

For each H2 section (skipping sections with empty bodies and any section already included in the main page body):

1. **Search for existing child page** via `searchplanning-artifactsUsingCql`:
   ```
   cql: ancestor = <mainPageId> AND title = "<Section Heading>" AND type = page
   ```
2. **If found:** call `updateplanning-artifactsPage` with `pageId`, section markdown body, `contentFormat: "markdown"`, `versionMessage` with timestamp
3. **If not found:** call `createplanning-artifactsPage` with:
   - `spaceId`
   - `title`: the section heading as-is (e.g., "System Context") -- no project name prefix
   - `body`: the section markdown content
   - `contentFormat: "markdown"`
   - `parentId`: `mainPageId`

### 3.8 Confirm

Report all main page URLs and their child page URLs to the user for each published document.

### 3.9 Tag Documents with planning-artifacts Metadata

After a successful planning-artifacts publish, tag **each** published local document with planning-artifacts space and page ID for easy retrieval and linking:

For each published document:

1. Ensure you have: `space_key` (from config), `mainPageId` (from 3.6 for this document), and the planning-artifacts base URL (from `getAccessibleAtlassianResources` or construct as `https://{site}.atlassian.net/wiki/spaces/{space_key}/pages/{mainPageId}`)
2. Read the workflow output file and parse its existing YAML frontmatter
3. Add or update a `planning-artifacts` block in the frontmatter:
   ```yaml
   planning-artifacts:
     space_key: "<space_key>"
     main_page_id: "<mainPageId>"
     main_page_url: "<constructed_url>"
   ```
4. Write the file back, preserving all existing frontmatter and body content
5. If the user declined publishing (skipped 3.2), skip this step

### 3.10 Commit planning-artifacts Tagging Changes

If 3.9 was skipped (user declined publish), skip this step. Otherwise run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "docs(architecture): add planning-artifacts link metadata" --repo-root .
```
Stages all `_bmad-output/` changes (excludes `modules/`), commits, and pushes with retry. Skips automatically if no changes exist.
