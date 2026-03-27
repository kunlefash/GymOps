# Story-Creator Dispatch Prompt Template

> Template used by the zone-sprint orchestrator to build prompts for generalPurpose subagents that create BMAD story files. Variables in `{curly_braces}` are replaced at dispatch time.

---

## Prompt Structure

Assemble the following sections when invoking the Task tool for each Wave 1 story:

### Section 1: Mission

```
You are creating a BMAD story file for the Zone Agentic SDLC pipeline.

MISSION: Create a comprehensive story file by following the execution protocol in `.claude/skills/zone-sprint/references/story-creator.md` exactly. Use the "specific story key provided by orchestrator" branch in Step 1 — do NOT auto-discover from backlog.

The orchestrator has provided this story key explicitly. Execute all protocol steps in order. Use `story_writer.py` to assemble the story file and update sprint-status. Validate against the BMAD checklist before reporting completion.
```

### Section 2: Story Key and Paths

```
[ORCHESTRATOR INPUT]
Story key: {story_key}
Project root: {project-root}
Story directory: {story_dir}
Sprint status: {sprint_status}

Protocol path: .claude/skills/zone-sprint/references/story-creator.md
[END ORCHESTRATOR INPUT]
```

### Section 3: Output Expectations

```
On success, you must produce:
- Story file at {story_dir}/{story_key}.md
- sprint-status.yaml updated (story = ready-for-dev, epic = in-progress if first in epic)
- Validation against BMAD checklist passed

Report back: story ID, key, file path, status (ready-for-dev), summary of context loaded.
```

---

## Variable Resolution

| Variable | Source |
| -------- | ------ |
| `{story_key}` | From Wave 1 selected stories (e.g. `2-2-msc-and-zone-fee-configuration`) |
| `{project-root}` | Repo root (e.g. `/apps/zonepay.global`) |
| `{story_dir}` | `{project-root}/_bmad-output/implementation-artifacts/stories` |
| `{sprint_status}` | `{project-root}/_bmad-output/implementation-artifacts/sprint-status.yaml` |
