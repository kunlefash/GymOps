# Step 01: Decompose PRD into Epics & Stories

## Instructions
1. Load the PRD and Architecture documents
2. Group functional requirements into epics
3. Break each epic into implementable user stories
4. Each story gets tasks, acceptance criteria, and point estimates

<ask>
Let's break this down into implementable work:

1. Which PRD and architecture doc should I reference?
2. How do you want to prioritize epics? (user value, technical risk, dependencies)
3. Target sprint length? (1 week, 2 weeks recommended)
4. Any stories you want to tackle first? (quick wins, foundational)
</ask>

<action>
For each functional requirement group in the PRD:

1. Create an Epic file using `_bmad/bmm/data/templates/epic-template.md`
2. Within each epic, create Story files using `_bmad/bmm/data/templates/story-template.md`
3. Each story must have:
   - Clear user story format (As a X, I want Y, so that Z)
   - Specific acceptance criteria (testable)
   - Task breakdown with subtasks
   - File list (predicted files to create/modify)
   - Story point estimate (1, 2, 3, 5, 8, 13)
   - Dependencies on other stories
4. Save epics to: `_bmad-output/planning-artifacts/`
5. Save stories to: `_bmad-output/implementation-artifacts/stories/`
</action>

<template-output file="_bmad-output/planning-artifacts/epics-overview.md">
# Epics Overview

## Epic Roadmap
| # | Epic | Stories | Total Points | Priority | Dependencies |
|---|------|---------|-------------|----------|--------------|

## Recommended Sprint Plan
### Sprint 1: Foundation
- {stories}

### Sprint 2: Core Features
- {stories}

### Sprint 3: Polish & Launch
- {stories}

## Story Index
| Key | Epic | Title | Points | Status |
|-----|------|-------|--------|--------|
</template-output>

<check>
Epic/Story validation:
- [ ] Every PRD functional requirement maps to at least one story
- [ ] Every story has testable acceptance criteria
- [ ] Every story has a task breakdown
- [ ] Story points are assigned
- [ ] Dependencies form a valid DAG (no circular deps)
- [ ] Stories are small enough to complete in 1-3 days
- [ ] No orphan stories (every story belongs to an epic)
</check>

**Epics & Stories created!**
Next: `/bmad-sprint-plan` to plan your first sprint, or `/bmad-dev-story {key}` to start developing.
