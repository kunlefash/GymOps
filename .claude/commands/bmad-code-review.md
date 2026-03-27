# Code Review

Run adversarial AI code review on a story's implementation.

## Usage
Provide story key or PR number: `/bmad-code-review 1-1-user-auth`

## Activation
1. Read `_bmad/bmm/agents/dev.md` for code review context
2. Read `_bmad/bmm/config.yaml`
3. Execute ALL 5 steps in `_bmad/bmm/workflows/4-implementation/code-review/steps/`:
   - step-01-load → step-02-architecture → step-03-quality → step-04-tests → step-05-report
4. Review is REPORT-FOCUSED — do NOT auto-fix issues
5. Post findings to PR as comments
6. Update story file with review section
