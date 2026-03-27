# ADR Writing Guide — ZonePay

How to write, number, and classify Architecture Decision Records for the ZonePay super-repo.

---

## When to Write an ADR

Write an ADR for any decision that:
- Constrains future implementation choices (e.g. "all queries must use X pattern")
- Selects one approach from multiple viable alternatives
- Has compliance or regulatory implications
- Will require explanation in future code reviews or onboarding
- Changes a cross-module interface or integration contract

Do NOT write an ADR for:
- Routine implementation details that follow an existing pattern
- Single-file local decisions with no cross-module impact
- Temporary workarounds explicitly marked for replacement

---

## ADR Format

Each ADR uses these fields. All are required except Compliance Note (conditional).

### Status
One of: `Proposed` | `Accepted` | `Deprecated` | `Superseded by ADR-{NNNN}`

### Date
ISO 8601: `YYYY-MM-DD`. Use the date the decision was accepted (or last amended), not the date of writing.

### Initiative
The Jira epic key and title. Provides the decision's traceability back to a sprint/planning artifact.

### Modules Affected
List all `modules/{submodule}` entries impacted. Be specific — this drives the compliance check.

### Context
Why this decision was needed. What constraint, problem, or trade-off forced a choice. Keep factual. Do not paste planning narrative. 2–5 sentences.

### Decision
What was decided. Name the specific pattern, interface, configuration key, or architectural approach. Include a minimal code sample or table if the pattern is non-obvious.

### Consequences
Split into Positive, Negative/Trade-offs, and Neutral. State what follows from the decision for engineers operating and extending the system. Avoid marketing language.

### Compliance Note
Conditional — include only when Modules Affected includes a compliance-sensitive module. See SKILL.md §Compliance Rules for the full trigger list and format.

---

## Numbering

- ADRs are numbered globally across all initiatives. Do not reset per epic.
- Format: `ADR-{NNNN}` with zero-padded 4-digit number.
- File path: `docs/adr/ADR-{NNNN}-{slug}.md`
- Slug: lowercase kebab-case, derived from ADR title, max 5 words.
- To find the next number: read `docs/adr/index.md` or glob `docs/adr/ADR-*.md`.

---

## Worked Example 1: ADR-0001 — Database Abstraction Strategy

**Source**: `_bmad-output/planning-artifacts/architecture.md` §ADR-001

**Evidence verified against**: `modules/zone.framework/src/Zone.Framework/Database/IDbConnectionFactory.cs`, `modules/zone.framework/src/Zone.Framework/Database/DatabaseType.cs`, DI registration in `Program.cs` of affected services.

**Key content summary**:

- **Decision**: `IDbConnectionFactory` abstraction with Vault-only connection string sourcing. Provider resolved via priority: ENV `DATABASE_PROVIDER` → config `DatabaseType` key → connection string inference (`Host=` = PostgreSQL, otherwise SQL Server).
- **Modules Affected**: `zone.framework`, `zonepay.settlement`, `zone.pggateway`, `zone.cardlesstransactionprocessing`
- **Compliance Note required**: YES — touches `zonepay.settlement` and `zone.pggateway`. CBN PSV 2025 requires payment system operators to use secure credential storage. Vault enforces this; connection strings are never in config files. CBN notification not required (internal security architecture change).

**Evidence standard check**: Before writing this ADR, the agent read:
1. `IDbConnectionFactory` interface implementation
2. `DatabaseType` enum definition
3. At least one `Program.cs` that registers the factory
4. Vault path used in configuration (`kv/zoneswitch/` or `secret/zone/{institution}/database`)

---

## Worked Example 2: ADR-0005 — CI/CD Matrix Testing Strategy

**Source**: `_bmad-output/planning-artifacts/architecture.md` §ADR-005 (Amended 2026-01-20)

**Evidence verified against**: `modules/zone.framework/tests/Zone.Tests/Integration/` — `DockerAvailability`, `SqlServerContainerFixture`, xUnit Collection Fixtures, `[SkippableFact]` usage.

**Key content summary**:

- **Decision**: Three-tier hybrid testing strategy in TeamCity. Foundation tests (IDbConnectionFactory, IProcedureCaller, ISqlQuery) use Testcontainers for both DBs and FAIL the build chain. Critical tests (settlement report stored procedures) run in parallel build configs. Standard tests use Testcontainers with standard failure handling.
- **Amendment note**: Testing patterns must reuse existing Zone.Framework fixtures (`SqlServerContainerFixture`, `DockerAvailability`, `[SkippableFact]`). Document the amendment in the ADR Consequences section.
- **Modules Affected**: `zone.framework`, `zone.ci` (TeamCity DSL)
- **Compliance Note required**: NO — CI/CD testing strategy is not compliance-sensitive.

**Evidence standard check**: Before writing this ADR, the agent read:
1. `DockerAvailability.cs` or equivalent in zone.framework tests
2. `SqlServerContainerFixture.cs`
3. At least one test using `[SkippableFact]` and a Collection Fixture
4. The TeamCity build configuration DSL for the affected projects (if accessible)

---

## ZonePay-Specific Decision Categories

Group ADRs by these categories when writing the initiative's first ADR (for context in the `docs/adr/index.md` Category column):

| Category | Examples |
|----------|---------|
| **Database provider** | Connection factory, EF Core registration, Dapper dialect |
| **Migration strategy** | Liquibase dual changelog, stored procedure maintenance |
| **Messaging pattern** | Kafka topic naming, RabbitMQ routing, Redis pub/sub |
| **Blockchain settlement** | Sui contract invocation, Besu Diamond Proxy, settlement batch |
| **Auth mechanism** | Vault token strategy, JWT claims, institution resolution |
| **Deployment topology** | Helm chart structure, per-institution values, K8s namespace |
| **Testing strategy** | Testcontainer fixtures, CI matrix, ATDD approach |
| **Regulatory compliance** | Vault credential security, audit trail, PCI DSS alignment |

---

## Evidence Standard (from zone-docs-consolidation)

Before writing an ADR, verify the decision against at least one of:

1. Implementation code (highest priority)
2. Config files or manifests
3. Tests that exercise the pattern
4. Generated specs or registries
5. BMAD artifacts (lowest priority — never sole source)

If the implementation disagrees with the BMAD artifact, use the implementation as truth and note the discrepancy in the ADR Consequences section under "Mismatch with original design".

---

## Anti-Patterns

- Do not write an ADR for a decision that was planned but not implemented.
- Do not copy BMAD architecture prose verbatim without reading the code.
- Do not skip the compliance check for modules in the compliance-sensitive list.
- Do not omit amendment dates when an ADR was updated after initial acceptance.
- Do not number ADRs from 1 in a new initiative if prior ADRs exist in `docs/adr/`.
