# Step 05: Generate Review Report

## Instructions
Compile all findings into a structured review report.

<action>
1. Compile findings from steps 02-04
2. Categorize by severity
3. Create actionable items
4. Update the story file with review section
</action>

<template-output file="story-file" section="senior-developer-review">
## Senior Developer Review (AI)

### Review Summary
- **Reviewer**: Code Review Agent
- **Date**: {date}
- **Verdict**: APPROVED / CHANGES REQUESTED / BLOCKED
- **Files Reviewed**: {count}

### Findings
#### Critical ({count})
{findings}

#### High ({count})
{findings}

#### Medium ({count})
{findings}

#### Low ({count})
{findings}

### Review Follow-ups (AI)
- [ ] [AI-Review][CRITICAL] {description} [{file}:{line}]
- [ ] [AI-Review][HIGH] {description} [{file}:{line}]

### Positive Notes
{What was done well}
</template-output>

<action>
1. Update story file with review section
2. If APPROVED: Add "approved" label to PR
3. If CHANGES REQUESTED: Add review comments to PR, update story status
4. Post review summary as PR comment
</action>

**Review complete!** Findings posted to PR.
