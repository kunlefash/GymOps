# Step 01: Load Story

## Instructions
1. Receive story key from user or CI input
2. Find and load the story file from `_bmad-output/implementation-artifacts/stories/{story_key}.md`
3. Parse frontmatter for status, tasks, dependencies
4. Verify story status is "ready-for-dev"

<action>
1. Search for story file matching the provided key
2. Parse the story markdown: frontmatter, tasks, acceptance criteria, file list
3. Check status — must be "ready-for-dev" to proceed
4. Check dependencies — all dependent stories must be "done"
5. Update status to "in-progress"
</action>

If story not found or not ready, halt and report.
