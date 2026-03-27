# Step 04: Backend Architecture

## Instructions
1. API design (REST endpoints or Next.js API routes)
2. Service layer and business logic organization
3. Middleware (auth, validation, error handling)

<ask>
Backend design questions:

1. Pure Next.js API routes or separate Express/Fastify server?
   - Recommendation: Start with Next.js API routes (simpler, Vercel-native)
2. Authentication approach? (NextAuth.js, Clerk, custom JWT)
3. File upload needs? (images, documents)
4. Email/notification requirements?
</ask>

<template-output file="_bmad-output/planning-artifacts/architecture-{name}.md" section="backend">
## 3. Backend Architecture
### 3.1 Technology: Next.js API Routes + TypeScript
### 3.2 API Design
### 3.3 Directory Structure
```
src/app/api/
├── auth/               # Authentication endpoints
├── [resource]/         # CRUD endpoints per resource
├── middleware.ts       # Global middleware
└── lib/
    ├── services/       # Business logic
    ├── validators/     # Zod schemas
    └── errors/         # Error handling
```
### 3.4 Authentication & Authorization
### 3.5 Error Handling Strategy
### 3.6 Validation (Zod schemas)
</template-output>
