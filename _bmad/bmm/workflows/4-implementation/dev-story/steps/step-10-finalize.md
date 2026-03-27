# Step 10: Push & Create PR

## Instructions
Push code and open a pull request for review.

<action>
1. Stage all changes: `git add -A`
2. Create final commit:
   ```
   git commit -m "feat({story_key}): complete story implementation
   
   - All acceptance criteria met
   - Test coverage: {X}%
   - Tasks completed: {N}/{N}
   
   Co-Authored-By: AI Dev Agent (Amelia) <ai-dev@gymops.dev>"
   ```
3. Push branch: `git push -u origin feat/{story_key}`
4. Create PR via GitHub CLI:
   ```
   gh pr create \
     --title "feat({story_key}): {story_title}" \
     --body "{PR body with story summary, changes, test results}" \
     --label "ai-generated,needs-review"
   ```
5. Update story status to "in-review"
6. Log PR URL in story file
</action>

**Story development complete!**
PR created and ready for review. Code review agent will be triggered automatically.
