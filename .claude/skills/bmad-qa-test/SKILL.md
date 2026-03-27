---
name: bmad-qa-test
description: "QA Test Generation"
---

# QA Test Generation

Generate tests for a story's implementation.

## Usage
Provide story key: `/bmad-qa-test 1-1-user-auth`

## Activation
1. Read `_bmad/bmm/agents/qa.md` for QA persona (Quinn)
2. Read `_bmad/bmm/config.yaml`
3. Load story file and identify implemented features
4. Generate:
   - Unit tests (Jest + React Testing Library)
   - Integration tests (API routes)
   - E2E tests (Playwright) for critical user flows
5. Target ≥80% coverage
6. Tests must be deterministic (no flaky tests)
