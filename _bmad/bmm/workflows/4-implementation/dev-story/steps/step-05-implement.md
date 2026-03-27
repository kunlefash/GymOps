# Step 05: Implement Tasks (TDD)

## Instructions
This is the core development step. For EACH task in the story, follow the TDD protocol:

### RED Phase
1. Write a failing test that defines the expected behavior
2. Run the test — confirm it FAILS
3. Log: `RED [TaskID]: {test description} — FAILING`

### GREEN Phase
1. Write the MINIMAL code to make the test pass
2. Run the test — confirm it PASSES
3. Log: `GREEN [TaskID]: {implementation summary} — PASSING`

### REFACTOR Phase
1. Clean up the code without changing behavior
2. Run tests — confirm they still PASS
3. Log: `REFACTOR [TaskID]: {what was cleaned up}`

### EXPAND Phase
1. Add edge case tests (null inputs, boundary values, error cases)
2. Implement handling for edge cases
3. Log: `EXPAND [TaskID]: {edge cases covered}`

### VALIDATE Phase
1. Run the FULL test suite (not just this task's tests)
2. Confirm zero regressions
3. Log: `VALIDATE [TaskID]: Full suite — {X} passed, {Y} failed`

<action>
Repeat RED→GREEN→REFACTOR→EXPAND→VALIDATE for every task in the story.
After each task, update the story file:
- Check off completed task
- Write debug log entry
</action>

## Rules
- NEVER skip RED — tests are written FIRST
- NEVER modify existing passing tests without approval
- If a test breaks that shouldn't, investigate before proceeding
- Commit after each task: `git commit -m "feat({story_key}): implement {task_description}"`
