---
title: "{PROJECT} - Architecture Document"
version: "1.0"
status: "draft"
author: "Architect Agent (Winston)"
created: "{DATE}"
prd_reference: "{PRD_FILE}"
---

# Architecture Document: {PROJECT}

## 1. System Overview
### 1.1 Architecture Style
{ARCHITECTURE_STYLE}

### 1.2 High-Level Diagram
```
{ASCII_DIAGRAM}
```

### 1.3 Key Design Decisions
| Decision | Rationale | Alternatives Considered |
|----------|-----------|------------------------|
| {DECISION} | {RATIONALE} | {ALTERNATIVES} |

## 2. Frontend Architecture
### 2.1 Technology: Next.js 15 + TypeScript
### 2.2 Directory Structure
```
src/
├── app/                 # Next.js App Router pages
├── components/          # Reusable UI components
│   ├── ui/             # Base components (Button, Input, etc.)
│   └── features/       # Feature-specific components
├── lib/                # Utilities, helpers
├── hooks/              # Custom React hooks
├── services/           # API client services
├── stores/             # State management
├── types/              # TypeScript type definitions
└── styles/             # Global styles, Tailwind config
```

### 2.3 State Management
{STATE_MANAGEMENT_APPROACH}

### 2.4 Routing Strategy
{ROUTING_DETAILS}

## 3. Backend Architecture
### 3.1 Technology: Node.js + TypeScript
### 3.2 API Design
{REST_OR_GRAPHQL}

### 3.3 Directory Structure
```
api/
├── routes/             # Route definitions
├── controllers/        # Request handlers
├── services/           # Business logic
├── models/             # Prisma models
├── middleware/          # Auth, validation, error handling
├── utils/              # Shared utilities
└── types/              # TypeScript types
```

### 3.4 Authentication & Authorization
{AUTH_APPROACH}

## 4. Database Design
### 4.1 Technology: PostgreSQL + Prisma ORM
### 4.2 Entity Relationship Diagram
```
{ERD_ASCII}
```

### 4.3 Key Models
{MODEL_DEFINITIONS}

### 4.4 Migration Strategy
{MIGRATION_APPROACH}

## 5. Infrastructure & Deployment
### 5.1 Vercel Configuration
{VERCEL_SETUP}

### 5.2 Environment Variables
| Variable | Purpose | Required |
|----------|---------|----------|
| DATABASE_URL | Postgres connection | Yes |
| {VAR} | {PURPOSE} | {Y/N} |

### 5.3 CI/CD Pipeline
{GITHUB_ACTIONS_OVERVIEW}

## 6. Security Architecture
{SECURITY_DETAILS}

## 7. Monitoring & Observability
{MONITORING_APPROACH}

## 8. Scalability Considerations
{SCALABILITY_NOTES}

## 9. API Contracts
### 9.1 Endpoint: {METHOD} {PATH}
{API_CONTRACT_DETAILS}

## Appendix
### A. ADR Log
{ARCHITECTURE_DECISION_RECORDS}
