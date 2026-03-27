# Step 01: Initialize Product Brief

## Instructions
1. Load project context from `_bmad/_memory/project-context.md`
2. Greet the user and explain the product brief creation process
3. Begin discovery with the core problem question

<ask>
**Let's create a product brief.** I need to understand the problem space first.

1. What problem are you trying to solve with this product/feature?
2. Who is experiencing this problem most acutely?
3. What happens if we don't solve it? What's the cost of inaction?
4. Have you seen any existing solutions? What's missing from them?
</ask>

<template-output file="_bmad-output/planning-artifacts/product-brief-{name}.md" section="problem-statement">
## Problem Statement
Write the problem statement based on user input, including:
- Core problem description
- Who is affected
- Impact of not solving
- Gap in existing solutions
</template-output>
