# Step 05: Database Design

## Instructions
1. Design the data model based on PRD requirements
2. Define Prisma schema
3. Plan migration strategy

<ask>
Database design:

1. Based on the PRD, what are the core entities? (Users, Gyms, Members, etc.)
2. What are the key relationships? (1:1, 1:N, N:M)
3. Any soft-delete requirements?
4. Audit trail needed? (who changed what, when)
5. Multi-tenancy model? (single gym vs. multi-gym platform)
</ask>

<template-output file="_bmad-output/planning-artifacts/architecture-{name}.md" section="database">
## 4. Database Design
### 4.1 Technology: PostgreSQL + Prisma ORM
### 4.2 Entity Relationship Diagram
### 4.3 Key Models (Prisma Schema)
### 4.4 Migration Strategy
### 4.5 Indexing Strategy
### 4.6 Data Seeding
</template-output>
