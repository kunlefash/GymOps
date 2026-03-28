# Estimation Dispatch Prompt Template

> Template used by the zone-sprint orchestrator to build prompts for generalPurpose subagents that estimate backlog stories using the zone-estimator skill. Variables in `{curly_braces}` are replaced at dispatch time.

---

## Prompt Structure

Assemble the following sections when invoking the Task tool for estimation:

### Section 1: Mission

```
You are estimating backlog stories for the Zone Agentic SDLC sprint planner.

MISSION: For each backlog story listed below, run the zone-estimator skill by following `.claude/skills/zone-estimator/SKILL.md` exactly. Use the full estimation workflow (Steps 1-6): gather task details, score each dimension per the rubric, calculate raw score, normalize to effort score (1-10), derive confidence, and produce the output with dimension_breakdown.

Return a single JSON object mapping each story_key to its estimation result. The planner will convert effort_score/estimated_person_days to Fibonacci story points (1, 2, 3, 5, 8, 13).
```

### Section 2: Stories to Estimate

```
[ORCHESTRATOR INPUT]
Project root: {project-root}
Sprint status: {sprint_status}
Epics: {epics_path}
Story directory (for ready-for-dev stories): {story_dir}

Backlog story keys to estimate:
{story_keys}

For each story:
- If the story has a file in {story_dir}/{story_key}.md, read that file for title, body, acceptance criteria, and tasks.
- Otherwise, extract title and body from epics.md (Epic N, Story M heading and following content until next story).
[END ORCHESTRATOR INPUT]
```

### Section 3: Output Format

```
You MUST return a valid JSON object (and only that object, no markdown fences) with this structure:

{
  "1-1-merchant-upload-bulk-and-single": {
    "effort_score": 6,
    "estimated_person_days": 8,
    "dimension_breakdown": {
      "surface_area": 2,
      "logic_complexity": 2,
      "integration_complexity": 1,
      "data_complexity": 0,
      "operational_complexity": 1
    },
    "primary_drivers": ["multiple services affected", "moderate business logic complexity"],
    "confidence": 0.82
  },
  "2-1-convenience-fee-bands-and-on-chain-approval": { ... },
  ...
}

Required per story: effort_score (1-10), estimated_person_days. Optional but recommended: dimension_breakdown, primary_drivers, confidence.

If a story is UNESTIMABLE, use: { "story_key": { "status": "UNESTIMABLE", "reason": "..." } } — the planner will assign a default (e.g. 5 points).
```

---

## Variable Resolution

| Variable | Source |
| -------- | ------ |
| `{project-root}` | Repo root (e.g. `/apps/gymops.global`) |
| `{sprint_status}` | `{project-root}/_bmad-output/implementation-artifacts/sprint-status.yaml` |
| `{epics_path}` | `{project-root}/_bmad-output/planning-artifacts/epics.md` |
| `{story_dir}` | `{project-root}/_bmad-output/implementation-artifacts/stories` |
| `{story_keys}` | Newline-separated list of backlog story keys (e.g. from development_status where status=backlog) |
