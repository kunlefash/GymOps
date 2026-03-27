# Step 03: Code Quality Review

## Instructions
Review code for quality, standards, and best practices.

<check>
## TypeScript
- [ ] Strict mode compliance (no `any` types without justification)
- [ ] Proper error handling (no swallowed errors)
- [ ] Types defined in `types/` directory
- [ ] No type assertions without comments explaining why

## React/Next.js
- [ ] Components are focused and reusable
- [ ] Proper use of Server vs Client components
- [ ] No unnecessary `use client` directives
- [ ] Hooks follow rules of hooks
- [ ] Proper error boundaries

## General
- [ ] No hardcoded values (use constants/config)
- [ ] No console.log in production code
- [ ] No commented-out code blocks
- [ ] Functions are small and single-purpose
- [ ] Variable/function names are descriptive
- [ ] No duplicate code (DRY principle)
- [ ] Error messages are user-friendly
</check>

Log each finding as: `[AI-Review][SEVERITY] description [file:line]`
