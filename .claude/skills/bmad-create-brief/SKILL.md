---
name: bmad-create-brief
description: "Create Product Brief (Quick Start)"
---

# Create Product Brief (Quick Start)

Direct shortcut to the Product Brief creation workflow.

## Activation
1. Read `_bmad/bmm/agents/pm.md` for PM persona context
2. Read `_bmad/bmm/config.yaml` for project config
3. Read `_bmad/_memory/project-context.md` for current state
4. Execute workflow steps in `_bmad/bmm/workflows/1-analysis/create-brief/steps/` in numerical order (step-01 through step-04)
5. Follow workflow engine rules from `_bmad/core/tasks/workflow.xml`:
   - Execute steps in EXACT order
   - At each `<template-output>` tag, prompt: **[c]**ontinue, **[y]**olo, **[a]**dvanced, **[e]**dit
   - Save progress after each template-output
6. All outputs go to `_bmad-output/planning-artifacts/`
