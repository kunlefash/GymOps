---
name: bmad-dev-story
description: "Develop Story (TDD)"
---

# Develop Story (TDD)

Execute the full 10-step TDD development workflow for a story.

## Usage
Provide the story key as argument: `/bmad-dev-story 1-1-user-auth`

## Activation
1. Read `_bmad/bmm/agents/dev.md` for Dev persona (Amelia)
2. Read `_bmad/bmm/config.yaml`
3. Read `_bmad/_memory/project-context.md`
4. Load story file from `_bmad-output/implementation-artifacts/stories/{story_key}.md`
5. Execute ALL 10 steps in `_bmad/bmm/workflows/4-implementation/dev-story/steps/` sequentially:
   - step-01-load → step-02-validate → step-03-analyze → step-04-setup
   - step-05-implement (TDD: RED→GREEN→REFACTOR→EXPAND→VALIDATE per task)
   - step-06-coverage → step-07-suite → step-08-update → step-09-dod → step-10-finalize
6. On completion: create branch, commit, push, open PR
7. TDD is MANDATORY — never skip the RED phase
