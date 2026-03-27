# Step 01: Validate PRD

## Instructions
1. Load the PRD file specified by user
2. Run comprehensive validation across completeness, quality, and consistency

<ask>
Which PRD would you like to validate? I'll check `_bmad-output/planning-artifacts/` for available PRDs.
</ask>

<action>
Load PRD from: _bmad-output/planning-artifacts/{prd-file}
</action>

<check>
## Completeness Checks
- [ ] Executive summary present and clear
- [ ] All user personas defined with needs
- [ ] Functional requirements have acceptance criteria
- [ ] Non-functional requirements are measurable
- [ ] Scope clearly defined (in/out)
- [ ] Success metrics have numeric targets
- [ ] Risks identified with mitigations
- [ ] Timeline has milestones
- [ ] Dependencies listed

## Quality Checks
- [ ] Requirements are testable (no vague language)
- [ ] No ambiguous terms ("should", "might", "possibly", "etc.")
- [ ] No conflicting requirements
- [ ] User stories follow "As a X, I want Y, so that Z" format
- [ ] Acceptance criteria are specific and measurable
- [ ] Technical constraints are realistic for the tech stack

## Consistency Checks
- [ ] Personas align with functional requirements
- [ ] Metrics align with stated goals
- [ ] Timeline is realistic given scope
- [ ] Dependencies don't create circular blocks
- [ ] Priority levels are consistent (not everything is P0)
</check>

<template-output file="_bmad-output/planning-artifacts/prd-validation-{name}.md">
# PRD Validation Report

## Overall Score: {X}/100

## Findings
### Critical Issues (Must Fix)
### Warnings (Should Fix)
### Suggestions (Nice to Have)

## Section Scores
| Section | Score | Notes |
|---------|-------|-------|

## Recommendations
{Prioritized list of improvements}
</template-output>
