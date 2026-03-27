---
name: zone-test-design
description: Activates the TEA Master Test Architect agent persona (Murat), runs the BMAD TEA test-design workflow, and publishes the resulting test design documents to Confluence. Use when creating system-level or epic-level test design plans as part of Zone's Agentic SDLC process.
---

# Zone Test Design

Create comprehensive test design documents through the BMAD TEA workflow under the Master Test Architect agent persona, then publish them to Confluence.

## Phase 0: Sync Super-Repo

Run:
```
python3 .claude/skills/zone-dev/scripts/zone_dev.py sync-superrepo --repo-root .
```

Pulls the latest super-repo branch (rebase with merge fallback) so all `_bmad-output/` artifacts are up to date before work begins.
**On failure:** Stop and inform the user that the super-repo sync failed — the branch may be behind or have unresolved conflicts. The user must resolve these manually before re-running this skill.

---

## Phase 1: TEA Agent Persona Activation

Before running the workflow, adopt the TEA Master Test Architect persona.

1. Load the full agent file at `{project-root}/_bmad/tea/agents/tea.md`
2. Adopt the persona: **Murat**, Master Test Architect — including role, identity, communication_style, and principles defined in that file
3. Load `{project-root}/_bmad/tea/config.yaml` and store session variables: `{user_name}`, `{communication_language}`, `{document_output_language}`, `{test_design_output}`, `{test_artifacts}`
4. Also load `{project-root}/_bmad/bmm/config.yaml` and store `{project_name}` (needed for Confluence title resolution)
5. Greet the user by `{user_name}`, speaking in `{communication_language}`, using the TEA Master Test Architect's communication style
6. Inform the user the test-design workflow is starting — skip the full TEA menu and go straight to the test-design workflow
7. **Snapshot output directory**: Before the workflow begins, record the current state of `{test_design_output}` — list all `*.md` files with their modification timestamps. Store as session variable `{pre_workflow_snapshot}`. This is used in Phase 3 to identify only new/modified artifacts.

Key persona attributes to maintain throughout all phases:

| Attribute | Value |
|-----------|-------|
| Role | Master Test Architect + Quality Advisor |
| Style | Blends data with gut instinct, "strong opinions, weakly held" |
| Principles | Risk-based testing with depth scaling to impact, fixture architecture, ATDD |

## Phase 1.5: Zone Test Infrastructure Context

Before launching the TEA test-design workflow, load and hold the following platform-specific context for the entire session. Every workflow step that discusses test levels, tooling, code examples, or implementation recommendations MUST be informed by these rules.

### E2E/API Test Repository (MANDATORY)

`zoneqa_automation` (`modules/zoneqa_automation/`) is the **single canonical Playwright repository** for all E2E and API tests across the entire Zone payment platform. `zone.clientdashboard-automation` is **deprecated** — if any loaded project artifact references it, treat it as `zoneqa_automation` in the generated output.

### Test Routing Rules (Apply to Every Coverage Plan and Execution Strategy)

| Test Level | Target Location | Notes |
|------------|----------------|-------|
| E2E | `modules/zoneqa_automation/tests/cardless/pwa/` | Browser-driven flows |
| API | `modules/zoneqa_automation/tests/cardless/api/` | HTTP/REST tests |
| Unit | Source submodule (e.g., `zone.zonepay`, `zone.zonepaypwa`) | Language-native: xUnit (.NET), Vitest (frontend), Hardhat (Solidity) |
| Integration | Source submodule | Same as unit |

When assigning test levels in the Coverage Matrix (Step 4) and generating output documents (Step 5), explicitly note the target repository for each E2E and API scenario.

### zoneqa_automation Conventions (Apply to Tooling, Code Examples, Infrastructure Sections)

When the generated documents include code examples, test infrastructure recommendations, factory patterns, or tooling references for E2E/API tests, use these conventions:

- **POM pattern**: Page objects extend `BasePage` from `pageObjectClass/basePage.js`; call `super(page)` in every constructor
- **Locators**: Use `.first()` on any locator that may match multiple elements; never use raw `.click()` — always `this.waitAndClick()`/ `this.waitAndFill()`
- **API auth**: Use `getHeadersForBank(request, institution)` from `apiManager/apiBase.js` — never fetch tokens inline
- **Multi-institution coverage**: Wrap cross-tenant scenarios in a loop over `['BANKA', 'BANKB', 'OFI']`
- **File naming**: `camelCase.spec.js` (not `.ts`, not kebab-case)
- **Reporting annotations**: Tag tests with Testiny annotation format for test management traceability
- **Emoji logging**: Use consistent emoji markers (`✅` pass, `❌` fail, `⚠️` warning, `ℹ️` info) in test output

### Deprecation Rule

If any input artifact (PRD, ADR, epic, story, prior test design) mentions `zone.clientdashboard-automation`:
1. Note the deprecation explicitly in the generated document's Assumptions section
2. Replace all tooling/infrastructure references with `zoneqa_automation` equivalents
3. Do NOT reproduce `zone.clientdashboard-automation` patterns (Index Facade POM, Allure reporting, PascalCase naming) in new test design output

---

## Phase 2: BMAD TEA Test-Design Workflow

1. Load and follow `{project-root}/_bmad/tea/workflows/testarch/test-design/workflow.md`
2. Obey all step-file architecture rules: micro-file design, just-in-time loading, sequential enforcement
3. Never load multiple step files simultaneously
4. Halt at menus and wait for user input
5. Output directory: `{test_design_output}` (resolves to `_bmad-output/test-artifacts/test-design/`)
6. Maintain the TEA Master Test Architect persona throughout all workflow steps

## Phase 3: Confluence Publish

After the workflow completes, execute this publish sequence.

### 3.0 Commit Workflow Changes

Run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "docs(test-design): add/update test design documents" --repo-root .
```
Stages all `_bmad-output/` changes (excludes `modules/`), commits, and pushes with retry. Skips automatically if no changes exist.

### 3.1 Load Config

Read `config.yaml` from this skill's directory (`.claude/skills/zone-test-design/config.yaml`) to obtain:
- `confluence.space_key` (default: `PMT`)
- `confluence.parent_page_id` (optional)
- `confluence.title_prefix` (resolve `{project_name}` from BMAD config)

### 3.2 Discover Output Files and Confirm with User

Scan `{test_design_output}` (resolves to `_bmad-output/test-artifacts/test-design/`) for markdown files produced by the workflow. Compare against `{pre_workflow_snapshot}` (recorded in Phase 1 step 7). Only files that are **new** or have a **newer modification timestamp** are candidates for publishing. This prevents republishing stale artifacts from previous workflow runs.

**Exclude** `test-design-progress.md` (workflow state tracking file, not a deliverable).

Build a list of documents to publish, each with a derived title based on filename:

| Filename pattern | Derived title |
|------------------|---------------|
| `test-design-architecture.md` | `"{project_name} - Test Design Architecture"` |
| `test-design-qa.md` | `"{project_name} - Test Design QA"` |
| `test-design-*-handoff.md` | `"{project_name} - Test Design Handoff"` |
| `test-design-epic-{N}.md` | `"{project_name} - Test Design Epic {N}"` |

**CRITICAL:** Before creating or updating any Confluence pages:

1. Present the discovered files and their derived titles to the user
2. Ask the user to confirm or override any titles
3. Confirm: **Target space key** (show default from config, allow override) and **Publish now or skip**
4. If the user declines publishing, stop here

### 3.3 Resolve Atlassian Cloud ID

Call `getAccessibleAtlassianResources` via the Atlassian MCP (server: `Atlassian`). Extract the `cloudId` from the response.

### 3.4 Resolve Space ID

Call `getConfluenceSpaces` with `cloudId` and `keys: ["<space_key>"]`. Extract the `spaceId` for the target space.

### 3.5–3.7 For Each Output Document

Repeat steps 3.5 through 3.7 for each discovered document in the publish list.

#### 3.5 Parse Document into Sections

Read the document. Split the markdown at each `## ` (H2) heading boundary:
- **Preamble**: everything before the first H2 (frontmatter, title, intro text)
- **Sections**: each H2 block has a heading (the text after `## `) and a body (all content until the next H2 or end of file)

All H2 sections become child pages. Skip sections with empty bodies.

#### 3.6 Create or Update the Main Page

Search for the main page via `searchConfluenceUsingCql`:
```
cql: title = "<derived_title>" AND space.key = "<space_key>" AND type = page
```

Build the main page body from three parts:
1. The **preamble** (title block, author, date)
2. The first H2 section content if it is an executive summary or introduction (include the H2 heading)
3. A **Table of Contents** heading (`## Contents`) followed by a markdown bulleted list where each item links to a child page title

TOC format example:
```markdown
## Contents

- [Test Strategy Overview](Test Strategy Overview)
- [Risk Assessment Matrix](Risk Assessment Matrix)
- [Test Coverage Model](Test Coverage Model)
```

**If a matching main page is found:** call `updateConfluencePage` with `pageId`, assembled body, `contentFormat: "markdown"`, and `versionMessage` with timestamp. Store `pageId` as `mainPageId`.

**If not found:** call `createConfluencePage` with `spaceId`, `title`, assembled body, `contentFormat: "markdown"`, and optional `parentId` from config. Store the returned page ID as `mainPageId`.

#### 3.7 Create or Update Child Pages

For each H2 section (skipping sections with empty bodies and any section already included in the main page body):

1. **Search for existing child page** via `searchConfluenceUsingCql`:
   ```
   cql: ancestor = <mainPageId> AND title = "<Section Heading>" AND type = page
   ```
2. **If found:** call `updateConfluencePage` with `pageId`, section markdown body, `contentFormat: "markdown"`, `versionMessage` with timestamp
3. **If not found:** call `createConfluencePage` with:
   - `spaceId`
   - `title`: the section heading as-is (e.g., "Risk Assessment Matrix") — no project name prefix
   - `body`: the section markdown content
   - `contentFormat: "markdown"`
   - `parentId`: `mainPageId`

### 3.8 Confirm

Report all main page URLs and their child page URLs to the user for each published document.

### 3.9 Tag Documents with Confluence Metadata

After a successful Confluence publish, tag each local document with Confluence space and page ID for easy retrieval and linking:

1. For each published document, ensure you have: `space_key` (from config), `mainPageId` (from 3.6), and the Confluence base URL (from `getAccessibleAtlassianResources` or construct as `https://{site}.atlassian.net/wiki/spaces/{space_key}/pages/{mainPageId}`)
2. Read the workflow output file and parse its existing YAML frontmatter
3. Add or update a `confluence` block in the frontmatter:
   ```yaml
   confluence:
     space_key: "<space_key>"
     main_page_id: "<mainPageId>"
     main_page_url: "<constructed_url>"
   ```
4. Write the file back, preserving all existing frontmatter and body content
5. If the user declined publishing (skipped at 3.2), skip this step

### 3.10 Commit Confluence Tagging Changes

If 3.9 was skipped (user declined publish), skip this step. Otherwise run:
```bash
python3 .claude/skills/zone-dev/scripts/zone_dev.py commit-planning \
  --message "docs(test-design): tag test design documents with Confluence publish metadata" --repo-root .
```
Stages all `_bmad-output/` changes (excludes `modules/`), commits, and pushes with retry. Skips automatically if no changes exist.
