# Calibration Mode

When historical task data is provided, adjust estimates to align with actual effort distribution.

## Input

```json
{
  "historical_tasks": [
    {
      "description": "Add settlement reconciliation endpoint",
      "effort_score": 5,
      "actual_person_days": 4
    },
    {
      "description": "Implement RBAC for dashboard",
      "effort_score": 7,
      "actual_person_days": 10
    }
  ]
}
```

## Calibration Rules

1. **Compute ratio**: For each historical task, `actual_person_days / estimated_person_days` (where estimated_person_days comes from the raw rubric mapping).
2. **Average ratio**: If historical tasks show consistent under/over-estimation (e.g. ratio 0.8 = we overestimate), apply that ratio to new estimates.
3. **Adjust estimated_person_days**: Multiply rubric-derived estimated_person_days by the calibration ratio before returning.
4. **Preserve effort_score**: Do not change effort_score (1-10); only adjust estimated_person_days for planning accuracy.
5. **Document**: Add to assumptions: "Calibrated using N historical tasks (avg ratio X)."

## Example

- Rubric says: effort_score 6 → ~8 person days
- Historical: similar tasks averaged 6.4 days (ratio 0.8)
- Calibrated: 8 × 0.8 = 6.4 → round to 6 or 7 person days
- Assumptions: "Calibrated using 3 historical tasks (avg ratio 0.8)."

## When to Apply

- Only when `historical_tasks` is provided and has at least 2 comparable tasks.
- Comparable = similar scope (same dimension profile or effort_score range).
- If historical data is sparse or incomparable, use rubric only and note in assumptions.
