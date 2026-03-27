---
story_key: "{STORY_KEY}"
epic: "{EPIC_KEY}"
title: "{TITLE}"
status: "ready-for-dev"
priority: "{PRIORITY}"
points: {POINTS}
assignee: "ai-dev-agent"
created: "{DATE}"
branch: "feat/{STORY_KEY}"
steps_completed: []
---

# {TITLE}

## Story
As a {PERSONA}, I want to {ACTION} so that {BENEFIT}.

## Acceptance Criteria
- [ ] AC-1: {CRITERIA_1}
- [ ] AC-2: {CRITERIA_2}
- [ ] AC-3: {CRITERIA_3}

## Technical Notes
{TECHNICAL_CONTEXT}

## Tasks
- [ ] Task 1: {TASK_DESCRIPTION} `[T1]`
  - [ ] Subtask 1a: Write failing tests `[T1.1]`
  - [ ] Subtask 1b: Implement to pass tests `[T1.2]`
  - [ ] Subtask 1c: Refactor `[T1.3]`

## File List
| File | Action | Description |
|------|--------|-------------|
| {FILE_PATH} | create/modify | {DESCRIPTION} |

## Dependencies
- {DEPENDENCY_OR_NONE}

## Definition of Done
- [ ] All acceptance criteria met
- [ ] All tests passing (unit + integration)
- [ ] Test coverage ≥ 80%
- [ ] Code reviewed by AI reviewer
- [ ] PR approved and merged
- [ ] No console errors or warnings

---

## Dev Agent Record
### Debug Log
_[Auto-populated during development]_

### Completion Notes
_[Auto-populated on completion]_

## Senior Developer Review (AI)
_[Auto-populated during code review]_

### Review Follow-ups (AI)
_[Action items from code review]_

## Change Log
- {DATE}: Initial creation from {EPIC_KEY}
