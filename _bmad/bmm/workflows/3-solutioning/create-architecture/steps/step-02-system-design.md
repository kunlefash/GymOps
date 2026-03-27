# Step 02: System Design

## Instructions
1. Design the high-level system components
2. Define communication patterns between components
3. Document key architectural decisions

<ask>
Let's design the system:

1. Based on the PRD, what are the major system components?
2. How should components communicate? (REST API, GraphQL, WebSockets?)
3. Do we need real-time features? (live updates, notifications)
4. Caching strategy needed? (Redis, in-memory, CDN)
5. Any background job requirements? (email sending, report generation)
</ask>

<template-output file="_bmad-output/planning-artifacts/architecture-{name}.md" section="system-design">
## System Component Diagram
```
[Client Browser]
    |
    v
[Next.js App (Vercel)] ── SSR/SSG ──> [Pages/Components]
    |
    v (API Routes)
[Node.js API Layer]
    |
    v
[PostgreSQL (Prisma)]
```

### Component Responsibilities
### Communication Patterns
### Key Decisions (ADRs)
</template-output>
