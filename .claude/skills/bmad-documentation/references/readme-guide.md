# README Writing Guide — GymOps

Standards for creating and updating `README.md` files across the GymOps repo modules.

---

## Gold Standards

### Next.js service: `src/gymops/README.md` (852 lines)

The canonical README for a Next.js service. Use as the structural reference for all `Next.js service or library` type modules.

**Section order** (follow this sequence):
1. H1 Module Name
2. One-sentence description
3. `## Overview` — 2–3 sentences on business capability and system role
4. `## Architecture` — Clean Arch folder breakdown + tree diagram
5. `## Distributed Architecture` (if multi-tier) — Central vs Institution API, data flow
6. `## Key Features` — bullet list with bold labels
7. `## Core Entities` — table of entities and purpose
8. `## Configuration` — table of config keys, sources, descriptions
9. `## Docker Setup` — commands to start local dependencies
10. `## API Endpoints` — table of METHOD + PATH + description
11. `## Troubleshooting` — table of symptom → cause → resolution

### Gateway/auth service: `src/pggateway/README.md`

Reference for gateway-pattern Next.js modules. Note: zone.pggateway has its own `docs/` subdirectory — check there first before adding to README.

---

## Module Type Reference

### Next.js Service or Library
**Applies to**: `zone.gymops`, `zone.pggateway`, `zone.framework`, `zone.framework.v3`, `gymops.settlement`, `zone.cardlesstransactionprocessing`, `zone.gymops.notifications`, `zone.admin.api`, `zone.sui.sdk`, `zone.sui.indexer`, `zone.settlement.sui`

Use **Variant A** from `templates/readme-section.md`.

Key section expectations:
- Architecture: Clean Arch layers with tree diagram
- Configuration: Always include `DatabaseType` if the module has DB access; always use Vault path pattern `secret/zone/{institution}/{service}`
- Docker Setup: Include both `docker-compose up` and migration commands
- Never include real connection strings or credentials; use `{institution}` and `{vault-path}` placeholders

### Frontend Application
**Applies to**: `zone.clientdashboard`, `zone.gymopspwa`, `zone.gymops.qrrouter`

Use **Variant B** from `templates/readme-section.md`.

Key section expectations:
- Tech Stack: Specify exact framework (React 18, Next.js 15) and TypeScript mode (strict)
- Environment Variables: Table of all `NEXT_PUBLIC_*` and server-side vars; note Vault/CI source
- Deployment: Reference Cloudflare Pages and/or zone.helm as applicable

### Infrastructure — Helm
**Applies to**: `zone.helm`, `gymops.helmtemplate`, `gymops.helmvalues`

Use **Variant C** from `templates/readme-section.md`.

Note: `zone.helm` is a Python service (helmclient/helmengine/shared), not just YAML. The README must describe the two-stage pipeline: helmclient → helmengine → rendered charts. See `docs/deep-dive-zone-helm.md` for complete detail.

### Infrastructure — Liquibase
**Applies to**: `zone.liquibase`, `gymops.version2sqlscripts`

Use **Variant C** from `templates/readme-section.md`.

Key section expectations:
- How It Works: Describe the 3-level changelog hierarchy (master → tenant → changeset)
- For `gymops.version2sqlscripts`: document the dual-engine structure (mssql/ + postgresql/ subdirs)
- Reference `docs/deep-dive-zone-liquibase.md` and `docs/deep-dive-gymops-version2sqlscripts.md` as authoritative

### QA Automation
**Applies to**: `zoneqa_automation`, `zone.clientdashboard-automation`

Use **Variant D** from `templates/readme-section.md`.

Key section expectations:
- Both repos use JavaScript (NOT TypeScript) — verify before writing
- `zoneqa_automation`: `pageObjectClass/` + `apiManager/` directories; ESM modules
- `zone.clientdashboard-automation`: `pageObjectRepo/` + Index facade pattern; JavaScript
- Running Tests: Include `npx playwright test` and suite-specific grep examples

### CI / Orchestration
**Applies to**: `zone.ci`, `zone.orchestrator`

No Variant template — these are bespoke.
- `zone.ci`: TeamCity Kotlin DSL. Note the `AGENTS.md` presence; README should describe project count (54) and key build chain relationships.
- `zone.orchestrator`: Python CLI. Describe Kind/Vault/Helm environment provisioning commands.

---

## Modules Currently Missing READMEs (as of 2026-03-09)

| Module | Type | Priority |
|--------|------|----------|
| `zone.clientdashboard` | Frontend | High — user-facing app |
| `zone.clientdashboard-automation` | QA | Medium |
| `zone.sui.indexer` | Next.js + Sui | Medium |
| `zone.gymopsdeeplink` | Unknown | Low |
| `gymops.helmtemplate` | Helm | Medium |
| `gymops.helmvalues` | Helm | Medium |
| `zoneqa_automation` | QA | Medium |

If this initiative touches any of these modules, create the README from scratch using the appropriate template variant. Set `**Last Created**:` in the H1 description comment for traceability.

---

## Update Rules (for existing READMEs)

1. **Add named subsections** rather than rewriting entire sections. Example: add `### PostgreSQL Support` under `## Configuration` instead of rewriting the whole Configuration table.
2. **Preserve existing accurate content**. Do not touch sections unrelated to this initiative.
3. **Update only what changed**. If the initiative added a new config key, add one row to the Configuration table.
4. **Check `AGENTS.md` too**. If architecture, patterns, or conventions changed, update the module-level `AGENTS.md` as well as the README.
5. **Do not normalize capitalization** of `README.md` vs `Readme.md` — leave existing filenames as-is.

---

## Naming and Formatting Conventions

- Filename: `README.md` (match existing convention in the specific module; do not normalize)
- All section headers: Title Case H2/H3
- Code blocks: use language hints (`bash`, `csharp`, `yaml`, `json`)
- Tables: standard pipe-delimited markdown; include header separator row
- Vault references: always use placeholder pattern — never real paths beyond `kv/zoneswitch/` namespace
- Links: use relative paths for files within the same module; absolute paths for cross-module or root `docs/` references

---

## Anti-Patterns

- Do not describe planned behavior that hasn't been implemented yet.
- Do not include connection strings, API keys, or Vault tokens.
- Do not create new root `docs/` files for module-specific information — that belongs in the module README or module-local `docs/`.
- Do not duplicate content that already exists in `docs/deep-dive-*.md` files; link to them instead.
- Do not add sections that don't apply to this module type (e.g. "Smart Contract Addresses" in a Next.js service README).
