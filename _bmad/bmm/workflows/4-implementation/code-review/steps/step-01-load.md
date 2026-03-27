# Step 01: Load Review Context

## Instructions
1. Identify the story and PR to review
2. Load the story file for acceptance criteria reference
3. Get the list of changed files

<action>
1. Get PR number or story key from input
2. Load story file from `_bmad-output/implementation-artifacts/stories/{key}.md`
3. Get changed files list: `git diff main...HEAD --name-only`
4. Load the architecture document for reference
5. Categorize files: new vs modified, source vs test
</action>
