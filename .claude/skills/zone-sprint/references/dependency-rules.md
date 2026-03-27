# Dependency Rules

Use this model for `zone-sprint` dependency matrix generation.

## Source Artifacts

1. `_bmad-output/implementation-artifacts/sprint-status.yaml`
2. `_bmad-output/planning-artifacts/epics.md`
3. `_bmad-output/planning-artifacts/implementation-readiness-report-*.md` (latest)

## Baseline Rules

1. Treat stories as sequential within each epic.
2. Infer dependency for story `n.m` as `n.(m-1)` when `m > 1`.
3. Do not infer cross-epic hard dependencies unless explicitly provided in artifacts.
4. Mark backlog story `unblocked_at_plan_time` when all inferred dependencies are `done`.
5. Mark backlog story `blocked` when any inferred dependency is not `done`.

## Selectability Rules

1. A backlog story is selectable when all dependencies are either:
- already `done`, or
- selected earlier in the same sprint plan walk.
2. If a dependency is in `ready-for-dev`, `in-progress`, or `review`, treat dependent backlog stories as blocked for this planning run.
3. Preserve story order by epic and story number.

## Epic Completion Bias

1. Prefer sets that complete more epics end-to-end under point target.
2. On ties, prefer higher point utilization under target.
3. On remaining ties, prefer more stories selected.
