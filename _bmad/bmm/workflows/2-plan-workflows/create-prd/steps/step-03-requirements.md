# Step 03: Functional Requirements

## Instructions
1. Elicit functional requirements feature by feature
2. Each feature needs: priority, description, user stories, acceptance criteria

<ask>
Let's define what the product does, feature by feature:

1. List all the features you envision (we'll prioritize after)
2. For the top feature:
   - What exactly should it do?
   - Who uses it and when?
   - What's the happy path flow?
   - What are the edge cases?
   - How do you know it's working correctly?

We'll repeat this for each feature.
</ask>

<template-output file="_bmad-output/planning-artifacts/prd-{name}.md" section="functional-requirements">
## 5. Functional Requirements

### 5.1 Feature: {FEATURE_NAME}
- **Priority**: P0/P1/P2
- **Description**: {description}
- **User Stories**:
  - As a {persona}, I want to {action} so that {benefit}
- **Acceptance Criteria**:
  - [ ] {testable criteria}
</template-output>
