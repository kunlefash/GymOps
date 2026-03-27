# Step 02: Sprint Status

## Instructions
Generate a current sprint status report.

<action>
1. Load active sprint file from `_bmad-output/implementation-artifacts/sprints/`
2. Check each story's current status
3. Calculate metrics: completed points, remaining, burndown
4. Identify blockers
</action>

<template-output>
# Sprint {N} Status

## Progress: {completed}/{total} points ({percent}%)
## Days Remaining: {days}

| Story | Title | Status | Branch | PR |
|-------|-------|--------|--------|-----|

## Blockers
{any blocked stories and reasons}

## Burndown
{Simple text burndown showing daily progress}
</template-output>
