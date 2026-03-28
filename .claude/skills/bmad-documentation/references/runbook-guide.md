# Runbook Writing Guide — GymOps

How to write, place, and classify operational runbooks from BMAD initiative stories.

---

## What Belongs in a Runbook

A runbook documents a **repeatable operational procedure** that a DevOps engineer or App Admin can follow without additional context. Content that qualifies:

- Database migration steps (schema application, data export/import, cutover, rollback)
- Kubernetes/Helm deployment procedures (rollout, rollback, pod restart sequences)
- Vault secret rotation or institution onboarding steps
- Smart contract upgrade procedures (Besu Diamond Proxy, Sui package upgrades)
- Kafka topic provisioning or consumer group management
- Incident response procedures with specific runbook triggers

Content that does NOT belong in a runbook:
- Planning rationale (stays in BMAD artifacts)
- Architecture explanations (belongs in `docs/architecture/` or ADRs)
- One-time setup steps only relevant during initial platform deployment

---

## Directory Placement

**New runbooks**: `docs/runbooks/{slug}.md`

**Existing operational content**: `docs/operations/` already exists and contains:
- `docs/operations/postgresql-migration-runbook.md` (from Story 6-1, HIGH issue: not yet committed as of 2026-02-24)
- `docs/operations/grafana-postgresql-conversion.md`

**Rule**: Check `docs/operations/` before creating a new file in `docs/runbooks/`. If a relevant runbook exists there, update it and add a cross-reference from `docs/runbooks/index.md` rather than creating a duplicate.

---

## Runbook Sections (Required)

Use `templates/runbook-entry.md` as the base. All sections are required unless explicitly marked optional.

### 1. Header metadata
- **Last Verified**: date the procedure was last tested end-to-end
- **Owner**: team or role responsible (not a person — people change)
- **Estimated Duration**: realistic wall-clock time
- **Risk Level**: Low / Medium / High — inform the operator's preparation
- **Related Initiative**: GitHub Issues epic key for traceability
- **Related Stories**: story IDs for tooling cross-references

### 2. Purpose
One paragraph. Answers: what does this operation do, when is it used, and who runs it.

### 3. Prerequisites
Checkbox list. Each item must be verifiable — include the command or check that confirms it. Never list a prerequisite that can't be verified (e.g. "team is ready").

### 4. Pre-Operation Checklist
Table of check / command / expected result. Executable before starting the main steps.

### 5. Steps
Numbered H3 sections. Each step must have:
- Clear action (imperative verb: "Run", "Update", "Verify")
- Command block with the actual command or script path
- Expected outcome (what success looks like)
- Estimated duration for that step
- "If this step fails" guidance — never leave the operator without a next action

### 6. Validation
Table of validation checks to run after all steps complete. Include specific thresholds from architecture documentation where available.

### 7. Rollback
Required for any High or Medium risk runbook. Must include:
- Rollback triggers (specific, measurable conditions)
- Step-by-step rollback procedure
- Post-rollback decision tree (within vs. after maintenance window)
- Rollback window expiry (if applicable)

### 8. Post-Operation Monitoring
Table of metrics, where to check them, and alert thresholds. Include recommended observation period before declaring success.

### 9. Known Limitations (conditional)
Use when the runbook references tooling that is not yet implemented. Table of limitation / workaround / future story reference. Remove section when all tooling is implemented.

### 10. Compliance Note (conditional)
Required when the runbook touches a compliance-sensitive module. See SKILL.md §Compliance Rules.

---

## Worked Example: PostgreSQL Migration Runbook

**Source story**: `_bmad-output/implementation-artifacts/stories/6-1-migration-runbook-documentation.md`

**Target path**: `docs/runbooks/postgres-migration.md` (or update `docs/operations/postgresql-migration-runbook.md` if it is committed)

**Evidence to verify before writing**:

| Claim | What to verify | Where to look |
|-------|---------------|---------------|
| Liquibase changelog paths | `settlementpartnerchangelog.yaml` and `settlementpartnerchangelog-postgresql.yaml` exist | `modules/gymops.version2sqlscripts/` |
| `zone.liquibase` CLI commands | Python CLI entry point and `update` command | `src/liquibase/` |
| Vault path pattern | `secret/zone/{institution}/database` with `connectionString` and `databaseType` | Config files or Vault integration tests |
| `kubectl rollout restart` targets | Deployment names in Helm values | `modules/gymops.helmvalues/` |
| Rollback triggers (error rate >5%, latency >20%) | Architecture document — cross-reference with Grafana dashboard names | `_bmad-output/planning-artifacts/architecture.md` §Migration Rollback |

**Key open issues from Story 6-1 review** (address before publishing):
- HIGH: `docs/operations/postgresql-migration-runbook.md` was not committed — verify current git status before deciding whether to create a new file or commit the existing one
- MEDIUM: Placeholder inconsistency between `[institution]` and `institution=[code]` — standardize to `{institution}` in runbook
- MEDIUM: Add explicit Liquibase CLI command example (e.g. `zone.liquibase update --changelog-file settlementpartnerchangelog-postgresql.yaml`)
- LOW: Remove stray `|` pipe characters from Post-Migration Monitoring section

**Compliance Note**: YES — touches `gymops.settlement` and `zone.pggateway`. Vault-secured connection strings are required by CBN PSV 2025. CBN notification not required for a migration operational procedure that keeps the same security posture.

---

## GymOps Operational Contexts

Runbooks are expected in these areas based on the platform's operational surface:

| Context | Typical Trigger | Risk Level |
|---------|----------------|-----------|
| Database migration (SQL Server → PostgreSQL) | Institution onboarding / platform upgrade | High |
| Helm chart deployment / rollback | Sprint release, hotfix | Medium |
| Smart contract upgrade (Besu Diamond Proxy) | Settlement logic change | High |
| Smart contract upgrade (Sui package) | ZONECOIN or registry update | High |
| Kafka topic provisioning | New service or event type | Low |
| Vault secret rotation | Periodic security rotation, institution offboard | Medium |
| Institution onboarding | New bank, OFI, or settlement partner | Medium |
| Grafana dashboard provisioning | New `database_provider` dimension | Low |

---

## Verification Rule

**Never publish a runbook command that doesn't exist in the repo.** For every command, script path, or CLI tool referenced:

1. Confirm the file exists: glob or read the path.
2. If it doesn't exist yet (e.g. tooling in a future story), mark it explicitly:
   > **NOT YET IMPLEMENTED** — tooling available after Story 6.2. Use manual alternative: `pg_dump -h {host} -U {user} {database} > backup.sql`
3. Never present NOT-YET-IMPLEMENTED steps as ready-to-run.

---

## Slug Derivation

- Lowercase kebab-case from the operation name
- Max 4 words
- Examples:
  - "PostgreSQL Migration" → `postgres-migration`
  - "Vault Secret Rotation" → `vault-secret-rotation`
  - "Institution Onboarding" → `institution-onboarding`
  - "Besu Contract Upgrade" → `besu-contract-upgrade`

---

## Anti-Patterns

- Do not include planning rationale — that belongs in ADRs or `_bmad-output/`.
- Do not list a command without its expected output or success criterion.
- Do not omit rollback steps for High/Medium risk runbooks.
- Do not reference Grafana dashboard names without verifying they exist.
- Do not create a new `docs/runbooks/` file if `docs/operations/` already has the relevant content.
- Do not include real credentials, connection strings, or Vault tokens — always use `{institution}` and path pattern placeholders.
