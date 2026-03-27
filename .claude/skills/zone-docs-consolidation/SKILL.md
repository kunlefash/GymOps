---
name: zone-docs-consolidation
description: Consolidate completed BMAD initiative artifacts into durable, repo-ready documentation for the ZonePay super-repo. Use when an initiative, epic, story, migration, rollout, or cross-module change has been implemented and the resulting docs must be grounded in actual code, config, tests, infra, and repository conventions instead of planning artifacts alone.
version: 1.0.0
triggers:
  keywords:
    - documentation consolidation
    - consolidate docs
    - distill bmad artifacts
    - repo docs
    - durable documentation
    - implementation docs
  intents:
    - consolidate_initiative_documentation
    - convert_bmad_artifacts_to_docs
    - update_repo_documentation_from_implementation
---

# Zone Documentation Consolidation

Convert completed BMAD initiative artifacts into durable documentation that matches the actual ZonePay codebase, submodule layout, and existing doc patterns.

Use this after implementation or verification work is materially complete. This is not a planning skill and not a generic document-project scan.

## Non-Negotiable Rules

1. Inspect the codebase first. Never write docs from BMAD artifacts alone.
2. Treat implementation as the primary source of truth: code, config, tests, CI, deployment files, Helm values, migrations, and API specs.
3. Use BMAD artifacts only as supporting context for intent, scope, and acceptance criteria.
4. Prefer updating existing docs over creating duplicates.
5. Separate durable docs from archived planning and execution artifacts.
6. Validate every important claim against concrete files whenever possible.
7. Flag uncertainty and implementation-vs-plan mismatches explicitly.
8. Never put secrets into docs. Use placeholders and Vault or env references.
9. If conventions, structure, or patterns changed, update the relevant `AGENTS.md` as well as human-facing docs.

## Required Inputs

- The BMAD initiative scope: story, epic, PRD, migration, rollout, or feature area.
- Relevant artifact paths under `_bmad-output/` if they exist.
- The affected modules or code areas.

If the user does not provide all of this, infer scope from the repo and proceed.

## Repository Grounding Procedure

Always do this before writing or editing documentation:

1. Read root [AGENTS.md](../../AGENTS.md) and [CLAUDE.md](../../CLAUDE.md).
2. Confirm repo shape from `.gitmodules` and `git submodule status`.
3. Identify the affected module type:
   - .NET service or library under `modules/zone.*` or `modules/zonepay.*`
   - frontend app
   - smart-contract repo
   - Helm or Liquibase infra repo
   - QA automation repo
   - CI or orchestration repo
4. Read the module-level `AGENTS.md` when present.
5. Inspect existing durable docs before creating anything new:
   - root `docs/`
   - module `README.md`
   - module-local `docs/`
   - deployment/readiness docs such as `deploy/README.md`
   - API specs such as `doc/apispec.yaml` or Swagger YAML
   - runbooks, release notes, migration guides, testing guides
6. Inspect the implementation files that prove the behavior:
   - source code
   - config files
   - tests
   - pipelines
   - Helm charts or values
   - Liquibase changelogs or SQL scripts
   - contract code and deployment scripts
7. Only then read BMAD artifacts under `_bmad-output/` to recover rationale, scope, or acceptance language.

## Observed Repo Conventions

These are present in this repo today and should be treated as default behavior.

### Repo shape

- This is a super-repo with many Git submodules under `modules/`.
- Root `docs/` is the main durable cross-module documentation area.
- Per-module documentation also exists and is often the right place for implementation-specific details.
- `_bmad/` contains workflow machinery.
- `_bmad-output/` contains planning, implementation, and test artifacts. These are archive and workflow outputs, not the default home for durable docs.
- `repo-review/` is an AI knowledge base and review/synthesis area. It is useful context, but not the default canonical destination for implementation docs.

### Root documentation taxonomy

- `docs/index.md`: central entry point.
- `docs/architecture/*.md`: platform and cross-module architecture, development, deployment, topology, route matrices, technology stack.
- `docs/registry/*.yaml`: machine-readable inventories such as services, endpoints, contracts, permissions.
- `docs/journeys/...`: user or system journeys with `README.md` plus `flow.yaml`.
- `docs/domain/*.md`: domain semantics tied to behavior.
- `docs/api-contracts-<module>.md`: module API summaries.
- `docs/data-models-<module>.md`: module data model summaries.
- `docs/deep-dive-<topic>.md`: exhaustive, topic-specific distillations.

### Module documentation patterns

- Many modules have `README.md` at module root.
- Several .NET modules have rich `AGENTS.md` files that require updates when architecture, patterns, structure, build, or testing conventions change.
- Some modules keep local docs close to implementation:
  - `modules/zone.pggateway/docs/`
  - `modules/zone.zonepay/deploy/README.md`
  - `modules/zone.smartcontracts.sui/*.md`
  - `modules/zonedc.settlement/scripts/releases/*/release-note.md`
  - `modules/zone.admin.api/doc/apispec.yaml`

### Naming and formatting

- Root durable markdown docs usually use lowercase kebab-case filenames.
- Registry files are YAML and commonly include `version` and `last_updated`.
- Journey folders use numbered names plus `README.md` and `flow.yaml`.
- Module README capitalization is inconsistent (`README.md`, `README.MD`, `Readme.md`). Do not normalize naming unless explicitly asked.

## Recommended Conventions

Use these only when the repo has no clear existing place for the information.

- If a module has no local `docs/` folder and the content is module-specific, update its `README.md` first.
- If the content is agent-operational rather than human-facing and the module has `AGENTS.md`, update that file too.
- If a new cross-module durable doc is needed under root `docs/`, prefer lowercase kebab-case and add an entry to `docs/index.md`.
- If a new machine-readable inventory is needed, place it under `docs/registry/` as YAML.
- If a user-facing or operator flow spans multiple services, prefer `docs/journeys/` or `docs/domain/` over a random standalone markdown file.

## Durable vs Archive Classification

Classify each finding before you write anything.

### Durable documentation

Promote to durable docs when the information is still true after the initiative closes and will help future engineers operate, change, test, deploy, or integrate the system.

Examples in this repo:

- actual architecture and topology
- stable module responsibilities
- API surface verified from controllers or OpenAPI specs
- data model or migration structure verified from code and changelogs
- deployment and environment behavior verified from Helm, compose, or pipelines
- runbooks grounded in existing commands or scripts
- business/domain semantics verified from code paths
- recurring testing or CI expectations

### Archive-only material

Leave in `_bmad-output/` when the content is mainly temporary planning or execution history.

Examples:

- PRD text, epics, readiness reports, change proposals
- story files and acceptance narration
- ATDD checklists and automation summaries
- sprint status snapshots
- one-off review notes that are superseded by durable docs

### Mixed cases

If an artifact contains both durable truth and temporary narrative:

1. Extract the durable, implementation-verified facts into repo docs.
2. Keep the original BMAD artifact as historical record.
3. In the durable doc, do not copy speculative or stale planning language.

## Mapping Findings to Target Docs

Choose the target based on scope and ownership.

### Cross-module or platform-wide changes

Update root `docs/` when the change affects more than one module or explains system-wide behavior.

Use:

- `docs/architecture/` for architecture, deployment, development, topology, route maps
- `docs/registry/` for inventories and machine-readable maps
- `docs/domain/` for semantics and business meaning
- `docs/journeys/` for flow narratives plus machine-readable call chains
- `docs/index.md` when adding or materially changing durable docs

### Module-specific implementation or operations

Update the affected module when the knowledge belongs to that repo alone.

Use:

- module `README.md` for overview, setup, usage, local architecture, contribution basics
- module `AGENTS.md` for coding patterns, architecture conventions, test and build expectations
- module-local `docs/` for focused subsystem docs
- `deploy/README.md` or nearby ops docs for local runtime and environment setup
- existing API spec files where the module already uses them

### API or contract documentation

- Prefer existing OpenAPI or Swagger files when present.
- If root `docs/api-contracts-<module>.md` already exists, update it rather than creating a second summary.
- For smart contracts, update root registries or function maps only when behavior affects platform-wide understanding. Keep module-internal contract details near the contract repo.

### Migration and infrastructure documentation

- For Liquibase content, document changelog structure and operational implications near the migration repos, then update root architecture or deployment docs only if the change is cross-cutting.
- For Helm and deployment packaging, keep service-specific details near `zone.helm`, `zonepay.helmtemplate`, or `zonepay.helmvalues`; reserve root deployment docs for platform-wide deployment shape.

### CI and automation

- Update module-local CI docs when the change is repo-specific, such as TeamCity DSL or test automation frameworks.
- Update root docs only when the CI rule affects the platform-wide workflow.

## Execution Workflow

1. Define the implemented scope from code first, not from story text.
2. Build an evidence list with file paths for each claim you expect to document.
3. Compare implementation against BMAD artifacts and note any divergence.
4. Locate existing durable docs for the same topic.
5. Decide: update existing doc, add missing section, or create a new doc only if necessary.
6. Write concise durable documentation that states what exists now.
7. Remove or avoid duplicate explanations when a canonical doc already exists.
8. Update indexes or registries that point to the changed documentation.
9. If patterns or conventions changed, update the relevant `AGENTS.md`.
10. Summarize what was promoted, what stayed archived, and where uncertainty remains.

## Evidence Standard

Before documenting a claim, verify it against at least one concrete source, preferably more than one for high-impact topics.

Preferred evidence order:

1. implementation code
2. config and manifests
3. tests
4. generated specs or registries
5. BMAD artifacts

Never present BMAD intent as fact when the code disagrees.

## Handling Mismatches

This repo already shows documentation drift in places, including differing submodule counts and generated summaries that can become stale. Future consolidation runs must account for that.

If you find a mismatch:

- state the mismatch explicitly
- prefer the implementation-backed version in durable docs
- mention that BMAD or older docs differ
- avoid silently copying stale counts, file names, routes, or architecture claims

Example mismatch classes to watch for:

- root docs claiming the wrong module count
- generated API docs naming controllers or routes that no longer exist
- deployment docs referencing scripts or checks that are mentioned but absent
- planning artifacts describing behaviors not implemented

## Output Quality Standards

- Write for future engineers, not for sprint retrospectives.
- Keep docs specific to this repo and its submodules.
- Use exact paths, module names, and command locations that exist.
- Prefer short, verifiable statements over broad architecture prose.
- Preserve machine-readable structures when editing YAML registries or journey flow files.
- Keep human-facing docs readable without duplicating the whole implementation.

## Anti-Patterns For This Repo

- Do not treat `_bmad-output/` as the final home for durable knowledge.
- Do not move implementation detail into `repo-review/` when it belongs in `docs/` or the module repo.
- Do not create a new root doc when an existing `docs/architecture/*`, `docs/domain/*`, `docs/api-contracts-*`, or module README already covers the area.
- Do not update root docs without checking whether the authoritative detail belongs in a submodule instead.
- Do not restate BMAD plans that the code does not implement.
- Do not copy hardcoded secrets or environment values from examples; convert them to placeholders.
- Do not assume every referenced script exists. Verify it.

## Completion Checklist

- [ ] Inspected code, config, tests, and relevant module docs before editing
- [ ] Used BMAD artifacts only as supporting context
- [ ] Classified each item as durable or archive-only
- [ ] Updated existing docs where possible instead of duplicating
- [ ] Chose root vs module-local targets based on actual ownership
- [ ] Validated major claims against implementation files
- [ ] Updated `docs/index.md` or related registries if needed
- [ ] Updated relevant `AGENTS.md` if patterns or conventions changed
- [ ] Flagged implementation-vs-plan mismatches clearly
- [ ] Kept secrets out of docs

## Final Reporting Format

At the end of a consolidation run, report:

1. Scope consolidated.
2. Evidence inspected, with the key code and config areas used as source of truth.
3. Durable docs updated or created.
4. BMAD artifacts intentionally left as archive-only.
5. Mismatches or uncertainties still requiring human review.

If no durable documentation changes were justified after inspection, say so plainly and explain why the artifacts should remain archived.
