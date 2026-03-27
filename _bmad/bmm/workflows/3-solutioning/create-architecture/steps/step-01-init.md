# Step 01: Initialize Architecture

## Instructions
1. Load the PRD from `_bmad-output/planning-artifacts/`
2. Load architecture template from `_bmad/bmm/data/templates/architecture-template.md`
3. Identify key architectural concerns from the PRD

<ask>
Let's design the architecture. First:

1. Which PRD are we designing for? (I'll check planning-artifacts/)
2. Any strong technical preferences or constraints beyond the default stack?
   - Default: Next.js 15 + Node.js + PostgreSQL + Prisma + Vercel
3. Any third-party integrations required? (payment, email, SMS, etc.)
4. Expected scale at launch? In 6 months?
</ask>

<template-output file="_bmad-output/planning-artifacts/architecture-{name}.md" section="overview">
## 1. System Overview
### 1.1 Architecture Style
### 1.2 High-Level Diagram
### 1.3 Key Design Decisions
| Decision | Rationale | Alternatives Considered |
</template-output>
