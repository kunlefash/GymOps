# Estimation Rules

Use zone-estimator skill for effort estimation, then map to time-based Fibonacci story points. Fallback to keyword heuristic when precomputed estimates are not available.

## Point Scale

Fibonacci only:
- 1, 2, 3, 5, 8, 13

Time-based semantics (Jira Agile alignment):
- 1: Trivial (< 2 hours)
- 2: Small (half day)
- 3: Medium (~ 1 day)
- 5: Large (2-3 days)
- 8: Very large (about a week, consider splitting)
- 13: Epic-sized (> 1 week, definitely split)

## Primary: Zone-Estimator + Subagent (Approach C)

1. **Phase 1a — Estimation subagent:** Orchestrator dispatches a generalPurpose subagent with the prompt from `templates/estimation-dispatch-prompt.md`. The subagent follows `.claude/skills/zone-estimator/SKILL.md` for each backlog story and returns a JSON object mapping `story_key` to `{ effort_score, estimated_person_days, dimension_breakdown, ... }`.

2. **Persist:** Orchestrator writes subagent output to `story-estimates.yaml` (or path from config).

3. **Plan:** Run `zone_sprint.py plan --estimates-file story-estimates.yaml`. The planner maps effort to Fibonacci and runs scope selection.

### Effort-to-Story-Point Mapping

| estimated_person_days | Fibonacci |
|-----------------------|-----------|
| 0 - 0.25 | 1 |
| 0.25 - 1 | 2 |
| 1 - 2 | 3 |
| 2 - 4 | 5 |
| 4 - 7 | 8 |
| 7+ | 13 |

When `estimated_person_days` is missing, use `effort_score` (1-10) with zone-estimator's default day mapping.

### UNESTIMABLE Handling

If zone-estimator returns `status: UNESTIMABLE` for a story, the planner assigns default 5 points and includes `zone-estimator=UNESTIMABLE` in rationale.

## Fallback: Keyword Heuristic

When `--estimates-file` is not provided and `planning.estimates_file` is not set, the planner uses the keyword heuristic.

### Inputs

1. Story title and body from `epics.md`
2. Acceptance criteria richness (Given/When/Then, criteria count)
3. Four dimensions inferred from text: Complexity, Uncertainty, Effort, Risk

### Scoring Heuristic

1. Start with base score `1`.
2. Add `+1` when acceptance criteria count is 2 or more.
3. Add `+1` when story body is long-form (>= 120 words).
4. Add complexity weight from keywords: `+1` if one, `+2` if two or more.
5. Add uncertainty weight: `+1` if two or more uncertainty keywords.
6. Add risk weight: `+1` if two or more risk keywords.

Complexity: blockchain, besu, settlement, nibss, webhook, kafka, rabbitmq, integration, async, security, rbac, audit, compliance.

Uncertainty: where applicable, as specified, optional, policy, configured, periodic, retry, fallback, support.

Risk: payment, settlement, refund, dispute, blockchain, nibss, security, compliance, audit.

### Score to Fibonacci (Fallback)

- score <= 1 -> 1
- score == 2 -> 2
- score == 3 -> 3
- score in [4, 5] -> 5
- score in [6, 7] -> 8
- score >= 8 -> 13

## Consistency

1. Clamp to config limits (`min_point_per_story`, `max_point_per_story`).
2. Include rationale fields in output for traceability.
3. Never output non-Fibonacci values.
4. If estimate is 8 or 13, include split recommendation in rationale.
