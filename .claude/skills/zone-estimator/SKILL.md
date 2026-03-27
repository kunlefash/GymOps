---
name: zone-estimator
description: |
  Estimate engineering implementation effort (1-10 scale) using a deterministic 
  rubric anchored to person-days. Use when estimating features, backlog grooming, 
  sprint planning, feasibility evaluation, or comparing task complexity.
compatibility: No external dependencies; pure rubric-based workflow
metadata:
  author: zone-network
  version: "1.0"
---

# Zone Estimator

Estimate engineering implementation effort on a 1-10 scale using a deterministic rubric anchored to person-days. Produces consistent effort scores across time, agents, and teams.

## Prerequisites

**Required Before Starting:**
- Task title and description (or infer from context)
- Acceptance criteria (or infer conservatively; missing = higher uncertainty)
- For full schema, see [references/input-schema.md](references/input-schema.md)

**Return UNESTIMABLE when:**
- Requirements are missing or ambiguous beyond reasonable assumptions
- Task is purely research with no implementation defined
- Task has no defined acceptance criteria

## Estimation Workflow

You *MUST* create a formal Todo/Task list exactly from this checklist:
```
Estimation Progress:
- [ ] Step 1: Gather task details
- [ ] Step 2: Score each dimension
- [ ] Step 3: Calculate raw score
- [ ] Step 4: Normalize to effort score (1-10)
- [ ] Step 5: Derive confidence
- [ ] Step 6: Produce output with breakdown
```

### Step 1: Gather Task Details

Extract or infer from the task:
- `repos_affected`, `services_affected`, `components_affected`
- `data_model_changes` (none | minor | moderate | major)
- `external_integrations`
- `unknowns` (list of uncertainties)
- `non_functional_requirements` (performance, security, compliance, availability)
- `testing_requirements` (none | basic | moderate | extensive)
- `deployment_requirements` (none | simple | moderate | complex)

Missing fields: infer conservatively (assume higher complexity when uncertain).

### Step 2: Score Each Dimension

Use the rubric in [references/dimension-rubric.md](references/dimension-rubric.md). Score each dimension:

| Dimension | Max | Criteria |
|-----------|-----|----------|
| surface_area | 3 | ≤2 files (0) → multiple files (1) → multiple services (2) → cross-repo (3) |
| logic_complexity | 3 | trivial (0) → straightforward (1) → complex/edge cases (2) → algorithmic/distributed (3) |
| integration_complexity | 2 | none (0) → known system (1) → new/unreliable/external (2) |
| data_complexity | 2 | none (0) → schema/migration (1) → large migration/backfill (2) |
| operational_complexity | 2 | simple (0) → testing coordination (1) → complex rollout/flags (2) |

### Step 3: Calculate Raw Score

```
raw_score = surface_area + logic_complexity + integration_complexity + data_complexity + operational_complexity
```

Max raw_score = 12.

### Step 4: Normalize to Effort Score (1-10)

| Raw Score | Effort Score | Approx Effort |
|-----------|--------------|---------------|
| 0-1 | 1 | ≤ 1 hour |
| 2 | 2 | 0.5 day |
| 3 | 3 | 1 day |
| 4 | 4 | 2-3 days |
| 5 | 5 | 4-5 days |
| 6 | 6 | 1-2 weeks |
| 7 | 7 | 2-3 weeks |
| 8 | 8 | 3-4 weeks |
| 9-10 | 9 | 1-2 months |
| 11-12 | 10 | multi-month / major effort |

### Step 5: Derive Confidence

```
confidence = 1.0 - (unknown_count × 0.1)
minimum = 0.5, maximum = 0.95
```

### Step 6: Produce Output

Return the full JSON structure (see Output Format below). Include dimension_breakdown, primary_drivers, assumptions, risk_factors, and recommended_task_breakdown.

## Output Format

**Success:**
```json
{
  "effort_score": 6,
  "confidence": 0.82,
  "estimated_person_days": 8,
  "dimension_breakdown": {
    "surface_area": 2,
    "logic_complexity": 2,
    "integration_complexity": 1,
    "data_complexity": 0,
    "operational_complexity": 1
  },
  "primary_drivers": ["multiple services affected", "moderate business logic complexity"],
  "assumptions": ["existing APIs behave as documented"],
  "risk_factors": ["dependency reliability"],
  "recommended_task_breakdown": [
    { "task": "implement core logic", "effort_days": 3 },
    { "task": "integration implementation", "effort_days": 2 },
    { "task": "testing", "effort_days": 2 },
    { "task": "deployment and validation", "effort_days": 1 }
  ]
}
```

**UNESTIMABLE:**
```json
{
  "status": "UNESTIMABLE",
  "reason": "insufficient acceptance criteria",
  "missing_information": ["integration details", "data model impact"]
}
```

## Examples

### Estimate Settlement Reconciliation Endpoint
```
User: "Estimate the settlement reconciliation endpoint"

Steps:
1. Gather: repos_affected=["settlement-service"], services_affected=["settlement-service"],
   data_model_changes="minor", external_integrations=["core banking"],
   testing_requirements="moderate", deployment_requirements="moderate"

2. Score: surface_area=1, logic_complexity=2, integration_complexity=1,
   data_complexity=0, operational_complexity=1 → raw_score=5

3. Normalize: raw 5 → effort_score 5 (or 6 if conservative)

4. Confidence: 2 unknowns → 0.8

5. Output: effort_score 6, confidence 0.84, estimated_person_days 8,
   dimension_breakdown, primary_drivers, assumptions, risk_factors, task_breakdown
```

### UNESTIMABLE Case
```
User: "Estimate this story" (no description or acceptance criteria provided)

Steps:
1. Cannot infer scope, integrations, or data impact
2. Return: { "status": "UNESTIMABLE", "reason": "insufficient acceptance criteria",
   "missing_information": ["description", "acceptance criteria", "scope"] }
```

## Verification

After estimation:
- [ ] All required output fields present (effort_score, confidence, dimension_breakdown, etc.)
- [ ] dimension_breakdown values sum to raw_score
- [ ] Confidence within [0.5, 0.95]
- [ ] recommended_task_breakdown present and sums to estimated_person_days
- [ ] primary_drivers explain the highest-scoring dimensions

## Edge Cases

| Scenario | Handling |
|----------|----------|
| Missing fields | Infer conservatively; assume higher complexity when uncertain |
| UNESTIMABLE | Return status with reason and missing_information list |
| Historical data provided | Apply calibration; see [references/calibration-mode.md](references/calibration-mode.md) |
| Identical inputs | Output MUST remain consistent within ±1 score (determinism) |

## Behavioral Rules

**MUST:**
- Use rubric strictly, not intuition alone
- Prefer conservative estimates when uncertain
- Never compress effort due to optimism bias
- Always explain estimation drivers (primary_drivers)
- Always produce task breakdown

**MUST NOT:**
- Guess without listing assumptions
- Produce score without dimension_breakdown
- Produce score without confidence

## Quick Reference

| Dimension | Max | Summary |
|-----------|-----|---------|
| surface_area | 3 | Files/modules/services/repos scope |
| logic_complexity | 3 | Trivial → algorithmic/distributed |
| integration_complexity | 2 | None → known → external/unreliable |
| data_complexity | 2 | None → migration → large migration |
| operational_complexity | 2 | Simple → testing → complex rollout |

| Raw Score | Effort | Days |
|-----------|--------|------|
| 0-1 | 1 | ≤1 hr |
| 2 | 2 | 0.5 |
| 3 | 3 | 1 |
| 4-5 | 4-5 | 2-5 |
| 6-8 | 6-8 | 1-4 weeks |
| 9-12 | 9-10 | 1+ months |

## Additional Resources

- [references/input-schema.md](references/input-schema.md) - Full input JSON schema
- [references/calibration-mode.md](references/calibration-mode.md) - Historical calibration workflow
- [references/dimension-rubric.md](references/dimension-rubric.md) - Detailed dimension scoring
