# Step 01: Initialize PRD

## Instructions
1. Check if a product brief exists in `_bmad-output/planning-artifacts/`
2. If yes, load it as context. If no, inform user to create one first (or proceed without).
3. Load the PRD template from `_bmad/bmm/data/templates/prd-template.md`
4. Create the output file

<ask>
Let's create a comprehensive PRD.

1. Do you have an existing product brief? If so, which one? (I'll check `_bmad-output/planning-artifacts/`)
2. What is the working title for this PRD?
3. What is the executive summary — in 2-3 sentences, what are we building and why?
</ask>

<template-output file="_bmad-output/planning-artifacts/prd-{name}.md" section="header-and-summary">
---
title: "{PRD_TITLE}"
version: "1.0"
status: "draft"
author: "PM Agent (John)"
created: "{DATE}"
---
# Product Requirements Document: {TITLE}
## 1. Executive Summary
{SUMMARY}
</template-output>
