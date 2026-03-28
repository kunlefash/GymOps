---
name: bmad-documentation
description: >
  Headless CI skill that generates durable documentation artifacts (ADRs,
  README updates, runbooks) from completed BMAD initiative work and commits
  them to the repo. Complements zone-docs-consolidation (interactive)
  as the automated pipeline counterpart. Triggered after zone-retrospective
  confirms epic completion.
version: 1.0.0
triggers:
  keywords:
    - bmad-documentation
    - generate-docs
    - doc-generation-ci
    - initiative-docs
  intents:
    - generate_initiative_documentation
    - headless_doc_generation
---

# bmad-documentation — Headless CI Documentation Skill

Autonomous, CI-friendly skill that reads completed BMAD initiative artifacts, verifies decisions against implementation, and emits durable documentation (ADRs, runbooks, README updates) into the canonical `docs/` hierarchy. Does NOT invoke interactive BMAD workflows.

**Input**: `epic_github-issues_key` (e.g. `CLSDLC-1`), optional `initiative_title` override
**Output**: `###ZONE-DOCS-RESULT###{"status":"0","epic_key":"CLSDLC-1","artifacts":{...}}###ZONE-DOCS-RESULT###` on success, `status:"1"` on failure.

**Non-negotiable rules** (inherited from zone-docs-consolidation):
1. Inspect the codebase first. Never write docs from BMAD artifacts alone.
2. Use BMAD artifacts only as supporting context for intent, scope, and ADR rationale.
3. Verify every ADR decision and every runbook command against actual implementation files.
4. Prefer updating existing docs over creating new files.
5. Never put secrets or credentials in any generated doc — use Vault path placeholders.
6. Flag implementation-vs-plan mismatches explicitly; prefer the implementation-backed version.

---

## Phase 0 — Sync & Validate Workspace

**0.1 Pull latest repo:**
```bash
git pull --rebase origin $(git rev-parse --abbrev-ref HEAD) || git pull --no-rebase origin $(git rev-parse --abbrev-ref HEAD)
```

**0.2 Check workspace state:**
```bash
git status --porcelain
```

**HALT protocol:** If sync fails OR unexpected dirty state is found in `modules/*` (dirty module pointers not related to this initiative), set `{blocker_summary}` = `"WORKSPACE_DIRTY: <paths>"`, post GitHub Issues comment on `{epic_github-issues_key}` (see Phase 8 comment format), and exit `status:"1"`. Do NOT proceed.

---

## Phase 1 — Load Initiative Context

Load the following artifacts in order. If any required file is missing, note the gap and continue with available data.

**1.1 Sprint status — confirm epic completion:**
```
_bmad-output/implementation-artifacts/sprint-status.yaml
```
Find the epic matching `{epic_github-issues_key}`. Verify status is `complete` or `done`. If not complete, exit `status:"1"` with `blocker_summary: "EPIC_NOT_COMPLETE"`.

**1.2 Architecture document — extract ADR sections:**
```
_bmad-output/planning-artifacts/architecture.md
```
Locate every `### ADR-NNN:` section. Capture: title, status, context, decision details, consequences.

**1.3 Epics file — identify module touchpoints:**
```
_bmad-output/planning-artifacts/epics.md
```
Identify which modules (`modules/`) are in scope for this epic.

**1.4 Story files — identify runbook content and touched modules:**
```
_bmad-output/implementation-artifacts/stories/*.md
```
For each story: check for operational procedure content (migration steps, deployment instructions, monitoring setup, rollback procedures), check Task/Subtask lines referencing `modules/`, check File List for actual files changed.

**1.5 Load documentation standard:**
Read `.claude/skills/zone-docs-consolidation/SKILL.md` — internalize the evidence standard and durable-vs-archive classification rules. These govern all decisions in Phases 3–5.

---

## Phase 2 — Decision Tree

Evaluate each branch. Record which phases to execute.

```
┌─ architecture.md contains ### ADR-NNN sections?
│  YES → Execute Phase 3 (ADR generation)
│  NO  → Skip Phase 3
│
├─ Stories reference operational procedures?
│  (migration steps, deployment, monitoring, rollback, maintenance windows)
│  YES → Execute Phase 4 (runbook generation)
│  NO  → Skip Phase 4
│
├─ Stories touch modules (File List entries under modules/)?
│  YES → Check each touched module README → Execute Phase 5
│  NO  → Skip Phase 5
│
├─ Any ADR or runbook touches compliance-sensitive modules?
│  Compliance-sensitive: zone.gymops, src/services,
│  gymops.settlement, src/services, ,
│  , ,
│  src/app/api (if touching funding/liquidation paths)
│  YES → Add ## Compliance Note section to affected artifacts
│  NO  → No compliance section needed
│
└─ Always → Execute Phase 6 (index updates), Phase 7 (quality gate), Phase 8 (commit + GitHub Issues)
```

---

## Phase 3 — Generate ADR Files

For each `### ADR-NNN:` section found in architecture.md:

**3.1 Verify decision against implementation** (evidence standard):
- Read the actual source files that implement the decision (code, config, tests).
- Confirm the decision as written still reflects the current code.
- If the decision no longer holds → document the mismatch; use the implementation state as truth; note the discrepancy in the ADR under Consequences.

**3.2 Assign canonical number:**
- Map to zero-padded 4-digit sequence: ADR-001 → ADR-0001, ADR-002 → ADR-0002, etc.
- Determine the next available number by reading `docs/adr/index.md` if it exists, or by checking existing `docs/adr/` files. ADR numbers continue globally across initiatives (do not reset per epic).

**3.3 Determine slug:**
- Derive from the ADR title: lowercase, kebab-case, max 5 words.
- Example: "Database Abstraction Strategy" → `database-abstraction-strategy`.

**3.4 Render ADR file:**
Write to `docs/adr/ADR-{NNNN}-{slug}.md` using `templates/adr.md`.
Fields to populate: Status, Date (today's date), Initiative (epic story key + title), Modules Affected, Context, Decision, Consequences.

**3.5 Compliance check:**
If the ADR's affected modules include any compliance-sensitive module → add `## Compliance Note` section using the format specified in the Compliance Rules section below. Cite the specific regulatory body and rule. State whether CBN notification is required.

**3.6 Update ADR index:**
Create or update `docs/adr/index.md` — a table with columns: Number, Title, Status, Date, Initiative, Compliance. One row per ADR.

---

## Phase 4 — Generate Runbook Entries

Runbooks are output to `docs/runbooks/{slug}.md`. The existing `docs/operations/` directory also contains operational content — do NOT duplicate. If a relevant runbook already exists in `docs/operations/`, update it rather than creating a new file in `docs/runbooks/`.

For each story containing operational procedure content:

**4.1 Verify implementation** (evidence standard):
- Locate all scripts, CLI commands, Helm values, Liquibase changelogs, and Vault paths referenced in the story.
- Verify each actually exists in the repo. Commands that don't exist must be flagged as "NOT YET IMPLEMENTED" and must not be presented as ready-to-run.
- Cross-reference story File List with actual `git status` or known committed files.

**4.2 Extract operational content:**
Identify: purpose, prerequisites, step-by-step procedure, validation commands, rollback triggers and steps, post-operation monitoring.

**4.3 Derive slug:**
Lowercase kebab-case from operation name. Example: "PostgreSQL Migration" → `postgres-migration`.

**4.4 Render runbook file:**
Write to `docs/runbooks/{slug}.md` using `templates/runbook-entry.md`.
Include cross-references to related stories (e.g. "Tooling for this step: Story 6.2") for any step not yet fully implemented.

**4.5 Compliance check:**
If the runbook touches compliance-sensitive modules → add `## Compliance Note` section.

**4.6 Update runbook index:**
Create or update `docs/runbooks/index.md` — a table with columns: Runbook, Purpose, Risk Level, Last Verified, Compliance.

---

## Phase 5 — Generate README Updates

For each module touched by the initiative (identified in Phase 1 story File Lists):

**5.1 Check README existence:**
Read `modules/{module}/README.md`.

- **If missing**: Create using `templates/readme-section.md` scaffolded for the module type. Determine type from: `.csproj` files (Next.js service), `package.json` (frontend), `*.yaml` Helm charts (infra), Python files (infrastructure), `*.move` (Sui), Playwright (QA).
- **If exists**: Add or update only the sections that changed. Do NOT rewrite sections unrelated to this initiative.

**5.2 Section update rules:**
- Follow zone.gymops README section order as gold standard: Overview → Architecture → Key Features → Core Entities → Configuration → Docker Setup → API Endpoints → Troubleshooting.
- Add new configuration keys, changed architecture descriptions, new integration points introduced by this initiative.
- Prefer adding a named subsection (e.g. `### PostgreSQL Support`) over rewriting the entire Configuration section.
- Do not rewrite existing accurate sections.

**5.3 Modules currently missing READMEs** (as of 2026-03-09):
`src/components`, `src/components-automation`, `indexer`, `zone.gymopsdeeplink`, `gymops.helmtemplate`, `gymops.helmvalues`, `tests/e2e`.
If this initiative touches any of these, create the README from scratch using the appropriate template variant.

---

## Phase 6 — Update Indexes

**6.1 `docs/adr/index.md`** (if Phase 3 ran):
Already maintained inline in Phase 3.6. Final pass: verify all ADR rows are present and the index is sorted by number.

**6.2 `docs/runbooks/index.md`** (if Phase 4 ran):
Already maintained inline in Phase 4.6. Final pass: verify all runbook rows are present.

**6.3 `docs/index.md`:**
If new `docs/adr/` or `docs/runbooks/` directories were created by this run → add corresponding sections to the Quick Reference and/or Generated Documentation tables. Follow existing table formatting exactly (pipe-delimited markdown).
Do NOT touch sections unrelated to this initiative.

**6.4 `docs/ai/retrieval-index.md`:**
Add rows to the relevant section (Architecture & Design for ADRs; new "Operations" section for runbooks if it doesn't exist). Rows to add:
- `What architectural decisions were made?` → `docs/adr/index.md`
- `ADR for {topic}?` → `docs/adr/ADR-{NNNN}-{slug}.md` (one row per ADR)
- `How to run {operation}?` → `docs/runbooks/{slug}.md` (one row per runbook)
- `All runbooks?` → `docs/runbooks/index.md`

Do not duplicate rows that already exist.

---

## Phase 7 — Quality Gate

Complete this checklist before committing. For each item, verify it explicitly — do not assume.

**Evidence standard:**
- [ ] Read implementation code before writing every ADR and runbook (not just BMAD artifacts)
- [ ] Used BMAD artifacts only as supporting context, not sole source
- [ ] Verified every ADR decision still holds in current implementation
- [ ] Verified every runbook command or script path actually exists in the repo (or is explicitly flagged NOT YET IMPLEMENTED)

**Classification:**
- [ ] Each item classified as durable (promoted to docs/) or archive-only (left in _bmad-output/)
- [ ] No planning narrative promoted as durable fact

**Documentation quality:**
- [ ] Updated existing docs where possible instead of creating duplicates
- [ ] Checked docs/operations/ before creating new docs/runbooks/ files
- [ ] All file paths in generated docs are correct and resolvable
- [ ] No secrets, credentials, or real connection strings in any generated doc
- [ ] Vault path placeholders used correctly (e.g. `secret/zone/{institution}/database`)

**Compliance:**
- [ ] Compliance Note added for all artifacts touching transaction processing, ISO 8583, HSM, or smart contracts
- [ ] Compliance Note names specific regulatory body (CBN / NIBSS / PTSA) and rule
- [ ] CBN notification determination is explicit (Yes/No with reason)

**Index integrity:**
- [ ] `docs/index.md` updated if new directories or major docs created
- [ ] `docs/ai/retrieval-index.md` updated with new lookup rows
- [ ] ADR index table sorted by number
- [ ] Runbook index table reflects all generated runbooks

**Mismatch reporting:**
- [ ] All implementation-vs-plan mismatches explicitly documented in the output summary

If any item fails and is not fixable → do NOT commit. Post GitHub Issues comment with `status:"1"` and a description of the blocking issue.

---

## Phase 8 — Commit & GitHub Issues

**8.1 Stage changed files:**
```bash
git add docs/adr/ docs/runbooks/ docs/index.md docs/ai/retrieval-index.md
git add modules/*/README.md  # only modules modified by this skill
```
Do NOT stage unrelated dirty files.

**8.2 Commit:**
```bash
git commit -m "{epic_github-issues_key}: {initiative_title} - documentation generation

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```

**8.3 Push:**
```bash
git push origin $(git rev-parse --abbrev-ref HEAD)
```

**8.4 GitHub Issues doc ticket spec (output as YAML block in response):**
```yaml
project: CLSDLC
type: Task
summary: "[Doc Review] {initiative_title} documentation artifacts"
description: |
  Auto-generated documentation from BMAD initiative {epic_github-issues_key}:
  - ADRs: {adr_count} files at docs/adr/
  - Runbooks: {runbook_count} files at docs/runbooks/
  - README updates: {readme_count} modules
  Review for accuracy and completeness before marking done.
labels: [documentation, auto-generated]
parent: {epic_github-issues_key}
```

**8.5 Post GitHub Issues comment on epic** (use MCP `addCommentToGitHub IssuesIssue`):
```
bmad-documentation completed for {initiative_title}.

Artifacts generated:
- ADRs: {list of ADR-NNNN filenames}
- Runbooks: {list of runbook filenames}
- README updates: {list of module names}

Doc review ticket spec included in skill output. Assign to team lead for review.
```

**8.6 Emit sentinel:**
```
###ZONE-DOCS-RESULT###{"status":"0","epic_key":"{epic_github-issues_key}","artifacts":{"adrs":[...],"runbooks":[...],"readme_updates":[...]}}###ZONE-DOCS-RESULT###
```

---

## Compliance Rules

**Trigger condition**: Any ADR or runbook whose `Modules Affected` list includes a compliance-sensitive module requires a `## Compliance Note` section.

| Module | Compliance Domain |
|--------|------------------|
| zone.gymops | Transaction processing — CBN, NIBSS |
| src/services | Transaction processing — CBN, NIBSS |
| gymops.settlement | Settlement — CBN RTGS, NIBSS settlement windows |
| src/services | ISO 8583 routing and auth — CBN, NIBSS |
|  | Smart contract settlement — CBN |
|  | Blockchain settlement — CBN |
|  | Blockchain settlement — CBN |
| src/app/api | Sui gateway (compliance applies if touching funding/liquidation) |

**Compliance Note format** (from zone-compliance/SKILL.md):
```markdown
## Compliance Note

- **Regulatory Body**: {CBN | NIBSS | PTSA}
- **Applicable Rule**: {specific regulation or requirement, e.g. "CBN Payment System Vision 2025 — Vault-secured credential storage for all payment system operators"}
- **Impact**: {what this decision means for compliance posture}
- **CBN Notification Required**: {Yes — reason | No — reason}
```

**Judgment guidance**:
- Connection string security + Vault → CBN (PSV 2025, credential management for payment system operators). CBN notification not required for internal security architecture.
- SQL dialect + query patterns → Not compliance-sensitive unless touching audit logs or financial records.
- EF Core DI registration → Not compliance-sensitive.
- Stored procedures for settlement reports → CBN/NIBSS (settlement window integrity). CBN notification not required for implementation pattern changes.
- CI/CD test strategy → Not compliance-sensitive.
- Liquibase dual changelog → Not compliance-sensitive unless migration touches settlement or audit tables.

---

## Output Summary Format

At the end of every run, output a structured summary:

```markdown
## bmad-documentation Run Summary

**Epic**: {epic_github-issues_key} — {initiative_title}
**Date**: {YYYY-MM-DD}
**Status**: {SUCCESS | FAILED | PARTIAL}

### Artifacts Generated
| Type | File | Compliance Note? | Source |
|------|------|-----------------|--------|
| ADR | docs/adr/ADR-0001-... | Yes / No | architecture.md §ADR-001 |
| Runbook | docs/runbooks/... | Yes / No | Story 6-1 |
| README | modules/.../README.md | N/A | Story X file list |

### Index Updates
- docs/adr/index.md: {created | updated} — {N} rows
- docs/runbooks/index.md: {created | updated} — {N} rows
- docs/index.md: {ADR section added | Runbook section added | no change}
- docs/ai/retrieval-index.md: {N} rows added

### Implementation vs Plan Mismatches
{List any mismatches found, or "None found"}

### Archive-Only (not promoted)
{List BMAD artifacts intentionally left in _bmad-output/, or "N/A"}

### Quality Gate
{PASSED | FAILED — list of failed items}
```
