# Dimension Rubric

Detailed scoring criteria for each estimation dimension. Use strictly; do not rely on intuition alone.

## Dimension 1: Change Surface Area (0–3)

Scope of code impact.

| Score | Criteria | Examples |
|-------|----------|----------|
| 0 | ≤ 2 files, single module | Config change, single handler |
| 1 | Multiple files, single service | New endpoint + tests in one repo |
| 2 | Multiple modules or services | 2-3 services, shared lib + consumer |
| 3 | Cross-repo or architectural change | New pattern across 4+ repos, shared contract change |

## Dimension 2: Logic Complexity (0–3)

Implementation complexity.

| Score | Criteria | Examples |
|-------|----------|----------|
| 0 | Trivial logic | CRUD, config lookup, simple validation |
| 1 | Straightforward logic | Standard business rules, well-defined flow |
| 2 | Complex logic, edge cases, coordination | Multi-step workflow, retries, state machine |
| 3 | Algorithmic complexity, reconciliation, distributed logic | Settlement batching, consensus, distributed coordination |

## Dimension 3: Integration Complexity (0–2)

External/system interactions.

| Score | Criteria | Examples |
|-------|----------|----------|
| 0 | No integration | Pure internal logic, no external calls |
| 1 | Integration with known system | Existing internal API, documented external API |
| 2 | Integration with new, unreliable, or external system | New third-party, undocumented, flaky dependency |

## Dimension 4: Data Complexity (0–2)

Schema/data impact.

| Score | Criteria | Examples |
|-------|----------|----------|
| 0 | None | No schema changes, read-only |
| 1 | Schema change or migration | New column, new table, Liquibase changelog |
| 2 | Large migration, backfill, or consistency-sensitive | Multi-table migration, data backfill, eventual consistency |

## Dimension 5: Operational Complexity (0–2)

Deployment/testing/ops impact.

| Score | Criteria | Examples |
|-------|----------|----------|
| 0 | Simple deploy | Standard CI/CD, no special steps |
| 1 | Requires testing coordination | E2E, integration tests, staging validation |
| 2 | Complex rollout, monitoring, feature flags, rollback | Canary, feature flags, new monitoring, rollback plan |

## Raw Score and Normalization

```
raw_score = surface_area + logic_complexity + integration_complexity + data_complexity + operational_complexity
```

Max raw_score = 12.

| Raw Score | Effort Score | Approx Effort |
|-----------|--------------|---------------|
| 0–1 | 1 | ≤ 1 hour |
| 2 | 2 | 0.5 day |
| 3 | 3 | 1 day |
| 4 | 4 | 2–3 days |
| 5 | 5 | 4–5 days |
| 6 | 6 | 1–2 weeks |
| 7 | 7 | 2–3 weeks |
| 8 | 8 | 3–4 weeks |
| 9–10 | 9 | 1–2 months |
| 11–12 | 10 | multi-month / major effort |
