# Step 01: Implementation Readiness Check

## Instructions
Validate alignment between PRD, Architecture, and Stories before development begins.

<action>
Load and cross-reference:
1. PRD from `_bmad-output/planning-artifacts/prd-*.md`
2. Architecture from `_bmad-output/planning-artifacts/architecture-*.md`
3. Stories from `_bmad-output/implementation-artifacts/stories/`
</action>

<check>
## PRD → Architecture Alignment
- [ ] Every functional requirement has architectural support
- [ ] Non-functional requirements reflected in architecture decisions
- [ ] Tech stack can deliver all required features
- [ ] Security requirements addressed in architecture

## PRD → Stories Alignment
- [ ] Every functional requirement covered by at least one story
- [ ] Acceptance criteria traceable to PRD requirements
- [ ] No gold-plating (stories don't exceed PRD scope)

## Architecture → Stories Alignment
- [ ] Stories reference correct architectural patterns
- [ ] File lists in stories match architecture directory structure
- [ ] Database stories align with Prisma schema design
- [ ] API stories align with API design

## Development Readiness
- [ ] All stories have task breakdowns
- [ ] Dependencies between stories are clear
- [ ] No blocking unknowns or open questions
- [ ] Dev environment setup documented
- [ ] CI/CD pipeline configured
</check>

<template-output file="_bmad-output/planning-artifacts/readiness-report.md">
# Implementation Readiness Report

## Overall Status: READY / NOT READY

## Alignment Score: {X}/100

## Issues Found
### Blockers (Must resolve before dev)
### Warnings (Should resolve soon)
### Notes

## Recommended Action
{Next steps based on findings}
</template-output>
