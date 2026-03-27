# Step 07: Full Test Suite Validation

## Instructions
Run the complete test suite to catch any regressions.

<action>
1. Run: `npm run test` (full suite)
2. Run: `npm run lint` (code quality)
3. Run: `npm run type-check` (TypeScript)
4. If E2E tests exist: `npm run test:e2e`
</action>

<check>
- [ ] All unit tests pass
- [ ] All integration tests pass
- [ ] Linting passes (zero errors)
- [ ] TypeScript compilation succeeds (zero errors)
- [ ] E2E tests pass (if applicable)
</check>

If ANY check fails, go back to step-05 and fix before proceeding.
