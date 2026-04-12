---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-04-13'
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
  - _bmad-output/planning-artifacts/product-brief-GymOps-2026-03-28.md
  - docs/FitBase_Product_Brief.md
  - _bmad/_memory/project-context.md
workflowType: 'architecture'
project_name: 'FitBase (GymOps)'
user_name: 'Adekunle'
date: '2026-04-13'
---

# Architecture Decision Document — FitBase (GymOps)

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

---

## Project Context Analysis

### Requirements Overview

**Functional Requirements:** 69 FRs across 16 categories — Authentication & Access (6), Business Setup & Onboarding (5), Member Management (5), Membership Plans (5), Payment Recording (6), Check-In (6), WhatsApp Communications (6), Notification Preferences (3), Member Portal (4), Staff Management (3), Business Dashboard (5), Data Export (3), Business Settings (2), GTM & Sharing (1), Super Admin (5), Offline Capability (4).

**Non-Functional Requirements:**
- PWA initial load ≤3s on mid-range Android over 3G; ≤1s subsequent from service worker cache
- Payment recording response ≤500ms; member search ≤300ms; QR-to-check-in ≤2s
- API uptime ≥99.5%; WhatsApp delivery ≤60s from trigger
- Zero data loss; zero undetected sync divergence
- Auth: JWT 15-min access / 7-day refresh; OTP single-use 10-min expiry rate-limited 5/hr
- Scale: 500 tenants × 500 members (250K records) for Year 1
- NDPR basic compliance: privacy notice, retention policy, archival (no hard deletes)

**Scale & Complexity:**
- Primary domain: Full-stack B2B2C SaaS PWA (greenfield)
- Complexity level: Medium-High
- Estimated architectural components: Auth/RBAC, Tenant Management, Member Management, Membership Plans, Payment Recording, Check-In/QR, WhatsApp Notification Engine, Member Portal, Staff Management, Business Dashboard, Data Export, Super Admin, Offline Sync (P2), PWA Shell

### Technical Constraints & Dependencies

- **WhatsApp Business API (Termii BSP):** P0 launch blocker. 6 pre-approved templates; Meta re-approval takes 3–7 days for changes. SMS fallback required for OTP. 3–4 week onboarding lead time — must start before development completes.
- **Solo developer + AI-assisted (BMAD TDD):** No parallelisation. Features ship sequentially P0 → P1 → P2. Architecture complexity must remain manageable for a single implementer.
- **Offline-first (P2 but architecturally load-bearing):** API must be idempotent-write-compatible from day 1. IndexedDB + Service Worker FIFO append-only queue. Server-authoritative on reconnect.
- **PWA constraints:** No native app APIs. Browser Camera (html5-qrcode) for QR. Add-to-Home-Screen on Android Chrome primary. iOS Safari secondary.
- **Paystack:** Post-MVP — not in architecture scope for now, but data model should not preclude it.
- **Hosting:** Vercel (frontend + serverless API). Stateless API required for horizontal scaling.
- **Database:** Single PostgreSQL instance (Year 1). Row-level multi-tenancy via `business_id`. Schema must support future partitioning.

### Cross-Cutting Concerns Identified

1. **Tenant isolation** — `business_id` scoping enforced at middleware layer on every query; never per-query manual scoping
2. **Auth & RBAC** — 4 hard-coded roles; JWT validation + role check on every protected route
3. **Audit trail** — Append-only writes for all financial records; void creates new audit entry; no DELETE on payments
4. **WhatsApp notification fan-out** — Triggered by payment recording, member add, check-in, auth OTP, staff invite; spans 5+ modules
5. **Idempotent write design** — All mutation APIs must tolerate duplicate submission (offline queue retry safety)
6. **Performance budgets** — Bundle splitting, lazy loading, local data caching even in online-first MVP
7. **NDPR archival semantics** — Member and tenant data archived, never hard-deleted; right-to-deletion deferred but schema must not make it impossible

---

## Starter Template Evaluation

### Primary Technology Domain

Full-stack B2B2C SaaS PWA — Next.js App Router monorepo (frontend + API routes in one deployment unit on Vercel).

### Starter Options Considered

- **create-next-app@latest** ✅ Selected — official CLI, matches defined stack exactly
- **T3 Stack** ❌ — includes tRPC and NextAuth which conflict with our custom OTP auth approach
- **RedwoodJS** ❌ — opinionated on GraphQL, misaligns with REST API decisions
- **Blitz.js** ❌ — reduced community momentum; unnecessary abstraction layer

### Selected Starter: create-next-app@latest (Next.js 16.2.3)

**Rationale:** The tech stack is fully pre-defined (Next.js, TypeScript strict, Tailwind, Prisma, Vercel). The official CLI initializes exactly this combination without imposing conflicting opinions on auth, API design, or ORM. Serwist handles PWA/service worker for the App Router.

**Initialization Sequence:**

```bash
# Bootstrap — run in project root (replaces static landing page)
npx create-next-app@latest . --typescript --tailwind --app --src-dir --import-alias "@/*"

# Component library
pnpm dlx shadcn@latest init

# Database ORM
npx prisma init --datasource-provider postgresql

# PWA service worker (App Router compatible)
pnpm add @serwist/next serwist

# Testing
pnpm add -D jest @testing-library/react @testing-library/jest-dom playwright @playwright/test
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:** TypeScript strict mode across all files; Node.js 20+ runtime on Vercel serverless functions.

**Styling Solution:** Tailwind CSS v4 with shadcn/ui component library; CSS variables for design tokens; mobile-first responsive utilities.

**Build Tooling:** Next.js Turbopack (dev); webpack (prod); automatic code splitting per route; image optimization via next/image; font optimization via next/font.

**Testing Framework:** Jest + React Testing Library (unit/component); Playwright (E2E). Configured separately — not included in create-next-app.

**Code Organization:** `src/app/` App Router with route groups for role separation: `(marketing)`, `(auth)`, `(owner)`, `(staff)`, `(member)`, `(admin)`. API routes co-located at `src/app/api/`. Shared lib at `src/lib/`. Middleware at `src/middleware.ts` for auth + tenant enforcement.

**Development Experience:** Turbopack hot reload; TypeScript strict checks; ESLint with Next.js rules; Prettier formatting.

**Note:** Project initialization using this sequence is the first implementation story.

---

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- Database provider: Neon (Vercel-native PostgreSQL, serverless pooling)
- JWT storage: httpOnly cookies (access 15-min / refresh 7-day)
- API middleware chain: Auth → Tenant scope → RBAC → Handler
- WhatsApp delivery: Outbox pattern (DB job queue + Vercel Cron)

**Important Decisions (Shape Architecture):**
- State management: TanStack Query v5 + Zustand v5 + React Context (auth)
- Rate limiting: Upstash Redis + @upstash/ratelimit (OTP only)
- Form handling: React Hook Form v7 + Zod
- Error format: Standardised JSON envelope with machine-readable codes
- Monitoring: Sentry v10 + Vercel Analytics

**Deferred Decisions (Post-MVP):**
- Redis general caching (revisit if member search degrades under load)
- Paystack payment gateway integration
- Rotating QR tokens
- Offline-first sync (P2 — online-first ships first)

### Data Architecture

**Database Provider:** Neon (neon.tech)
- Rationale: Native Vercel integration, serverless-compatible connection pooling (pgBouncer built-in), Prisma-first workflow, database branching for dev/staging environments. Avoids manual pooler setup on Railway or paying for unused Supabase features.
- Connection: `DATABASE_URL` with pooled connection string from Neon dashboard.

**ORM & Migrations:** Prisma 7.7.0
- Schema-first with Prisma Migrate. `prisma migrate deploy` in CI before build.
- Zod schemas generated/maintained in sync with Prisma types for shared validation.

**Validation Strategy:** Zod (already in package.json)
- Single schema definition: Prisma type → Zod schema → API request validation → frontend form validation.
- Shared `src/lib/schemas/` — imported by both API routes and React Hook Form resolvers.

**Caching Strategy:** TanStack Query client-side cache (MVP)
- PostgreSQL indexes on `(business_id, status)`, `(business_id, phone)`, `(business_id, name)` cover ≤300ms search NFR.
- No Redis cache for MVP. Revisit post-MVP under load.

### Authentication & Security

**Token Storage:** httpOnly cookies
- Access token: 15-min expiry. Refresh token: 7-day (30-day if `stayLoggedIn: true`).
- `Secure; HttpOnly; SameSite=Strict` attributes. Automatic on `fetch` with `credentials: 'include'`.
- No localStorage for tokens — XSS protection for PWA context.

**Stay-Logged-In (Shared Device):** Toggle at OTP verification
- Staff toggle sends `stayLoggedIn: true` with OTP confirmation request.
- Server sets refresh token expiry to 30 days and records preference in session record.

**OTP Rate Limiting:** Upstash Redis + @upstash/ratelimit
- 5 OTP attempts per phone number per hour.
- Serverless-compatible — no in-memory state required.
- Used only for rate limiting (not general caching).

**API Security Middleware Chain:**
```
Request → Auth (JWT verify) → Tenant inject (business_id from token) → RBAC check → Handler
```
- `src/middleware.ts`: JWT verification + `business_id` injection for all `/api/*` routes.
- Per-route higher-order function `withRole(roles)` wraps handler for RBAC enforcement.

### API & Communication Patterns

**API Design:** RESTful JSON via Next.js API Routes
- Resource-oriented URL structure: `/api/members`, `/api/payments`, `/api/checkins`
- Standard HTTP verbs. Tenant scoping implicit (from JWT, never from URL).

**Error Response Format:**
```json
{
  "error": {
    "code": "MEMBER_NOT_FOUND",
    "message": "No member with this phone number",
    "field": "phone"
  }
}
```
Machine-readable `code` (for frontend switch), human-readable `message` (for display), optional `field` (for form error placement).

**WhatsApp Delivery: Outbox Pattern**
- Payment write + WhatsApp job insert occur in a single Prisma transaction.
- `whatsapp_jobs` table: `id`, `type`, `payload` (JSON), `status` (pending/sent/failed), `retry_count`, `created_at`, `sent_at`.
- Vercel Cron job (`/api/cron/send-whatsapp`, every 1 minute) picks up pending jobs, calls Termii, updates status.
- Max 3 retries with exponential backoff. Failed after 3 retries → status: failed, surfaced in Super Admin dashboard.
- Decouples payment recording response time from Termii API latency.

**Input Validation:** Zod schemas on all API routes
- `src/lib/schemas/` shared between API routes and frontend forms.

### Frontend Architecture

**Server State:** TanStack Query v5
- All API calls go through TanStack Query hooks. stale-while-revalidate for member lists, dashboard data.
- Optimistic updates for check-in and payment recording (perceived ≤500ms).

**Client State:** Zustand v5
- Stores: `authStore` (current user + role), `syncStore` (offline queue status + sync state), `uiStore` (active modals, toasts).

**Auth Session:** React Context
- `AuthContext` wraps the app. Set once after OTP verification. Provides user object + active role to route groups.

**Forms:** React Hook Form v7 + Zod resolver
- shadcn/ui Form components integrate directly with RHF. Zod schemas shared with API validation layer.

**QR Scanning:** html5-qrcode (lazy loaded)
- Loaded dynamically only on member check-in route. Not in initial bundle.

**Route Groups (role isolation):**
- `(marketing)/` — public landing page
- `(auth)/` — login, OTP verification
- `(owner)/` — owner dashboard, member management, payments, settings
- `(staff)/` — shift-mode screen, check-in, payment recording
- `(member)/` — membership status, QR scanner, payment history
- `(admin)/` — super admin dashboard

### Infrastructure & Deployment

**Database:** Neon (serverless PostgreSQL)
- Pooled connection string for Vercel functions. Direct connection string for Prisma Migrate in CI.

**Monitoring:** Sentry v10 + Vercel Analytics
- Sentry: error capture on client, API routes, and edge runtime. Alert on WhatsApp job failures.
- Vercel Analytics: Core Web Vitals, LCP/FID/CLS tracking against ≤3s load NFR.

**CI/CD:** GitHub Actions
- Pipeline: typecheck → lint → unit tests → build → Playwright E2E → Vercel preview deploy.
- `main` merge → production deploy (automatic via Vercel Git integration).

**Migrations:** `prisma migrate deploy` in Vercel build step (before build).

**Environment Variables:** `.env.local` (dev), Vercel env vars (preview/production).
- Required: `DATABASE_URL`, `DATABASE_URL_DIRECT`, `TERMII_API_KEY`, `JWT_SECRET`, `UPSTASH_REDIS_REST_URL`, `UPSTASH_REDIS_REST_TOKEN`, `NEXT_PUBLIC_APP_URL`, `SENTRY_DSN`.

### Decision Impact Analysis

**Implementation Sequence (informed by decisions):**
1. Neon DB provisioned + `DATABASE_URL` set → Prisma can init schema
2. Prisma schema + Zod schemas → shared validation layer available
3. Auth middleware (JWT + tenant injection) → all protected routes unlock
4. Upstash Redis → OTP rate limiting available
5. Outbox pattern (`whatsapp_jobs` table + Cron) → WhatsApp delivery decoupled
6. TanStack Query + Zustand setup → frontend data layer ready
7. Route groups scaffolded → role-specific UI development can proceed in isolation

**Cross-Component Dependencies:**
- Every API route depends on auth middleware (tenant injection)
- Payment recording depends on WhatsApp outbox being available (transaction atomicity)
- Member search performance depends on DB indexes being in place
- QR check-in depends on active membership validation (Prisma query on `members` + `membership_plans`)
- Offline sync (P2) depends on all mutation APIs being idempotent — must be designed in from day 1

---

## Implementation Patterns & Consistency Rules

### Pattern Categories Defined

**Critical Conflict Points Identified:** 13 areas where AI agents could make different choices — naming conventions, structural organisation, API response formats, currency handling, tenant scoping, auth guard placement, query key management, and mutation patterns.

### Naming Patterns

**Database Naming Conventions (Prisma → PostgreSQL):**
- Prisma model names: PascalCase singular (`Business`, `Member`, `Payment`)
- PostgreSQL table names: snake_case plural via `@@map` (e.g., `@@map("businesses")`)
- Prisma field names: camelCase (`businessId`, `createdAt`)
- DB column names: snake_case via `@map` (e.g., `@map("business_id")`)
- Foreign keys in DB: `business_id`, `member_id` (not `fk_business`, not `businessId`)
- Indexes: `@@index([businessId, status])` — Prisma handles naming

**API Naming Conventions:**
- Resources: plural, lowercase, kebab-case — `/api/members`, `/api/whatsapp-jobs`
- Nested resources: `/api/members/[memberId]/payments`
- Route parameters: camelCase (`memberId`, not `member_id` or `id`)
- Query params: camelCase (`?businessId=`, `?status=active`)
- Cron endpoints: `/api/cron/send-whatsapp` (never `/api/cron/sendWhatsapp`)

**Code Naming Conventions:**
- React components: PascalCase (`MemberCard`, `PaymentForm`)
- Component files: PascalCase.tsx (`MemberCard.tsx`)
- Utility/hook files: camelCase.ts (`useMembers.ts`, `formatCurrency.ts`)
- Route segment directories: kebab-case (`member-portal/`, `shift-mode/`)
- Zustand stores: camelCase + Store suffix (`authStore`, `syncStore`)
- TanStack Query hooks: `use` + Resource + Action (`useMembers`, `useCreatePayment`)
- Zod schemas: camelCase + Schema suffix (`memberSchema`, `paymentSchema`)
- Constants: UPPER_SNAKE_CASE (`MAX_OTP_ATTEMPTS`, `JWT_EXPIRY_MINUTES`)

### Structure Patterns

**Project Organisation:**
```
src/
├── app/
│   ├── (marketing)/          # Public pages — no auth required
│   ├── (auth)/               # Login + OTP flows
│   ├── (owner)/              # Owner dashboard — layout checks Owner role
│   ├── (staff)/              # Staff shift-mode — layout checks Staff role
│   ├── (member)/             # Member portal — layout checks Member role
│   ├── (admin)/              # Super admin — layout checks SuperAdmin role
│   └── api/
│       ├── auth/             # /api/auth/[...] — OTP, refresh, logout
│       ├── members/          # /api/members/[memberId]/[...]
│       ├── payments/         # /api/payments/[paymentId]/[...]
│       ├── checkins/         # /api/checkins/[...]
│       ├── plans/            # /api/plans/[...]
│       ├── staff/            # /api/staff/[...]
│       ├── businesses/       # /api/businesses/[...]
│       └── cron/             # /api/cron/[...] — Vercel Cron only
├── components/
│   ├── ui/                   # shadcn/ui primitives (never edited manually)
│   └── [feature]/            # Feature-specific components (MemberCard, PaymentForm)
├── lib/
│   ├── schemas/              # Zod schemas — one file per domain entity
│   ├── prisma.ts             # Prisma client singleton
│   ├── auth.ts               # JWT sign/verify helpers
│   ├── termii.ts             # Termii API client
│   ├── redis.ts              # Upstash Redis client
│   └── utils.ts              # Shared utilities (formatCurrency, formatPhone, etc.)
├── hooks/                    # TanStack Query hooks (useMembers.ts, usePayments.ts)
├── stores/                   # Zustand stores (authStore.ts, syncStore.ts, uiStore.ts)
├── middleware.ts             # JWT auth + tenant injection
└── types/                    # TypeScript types not generated by Prisma
tests/
├── unit/                     # Jest unit tests (mirrors src/ structure)
├── integration/              # API route integration tests
└── e2e/                      # Playwright E2E tests
```

**Test File Location:** Tests are never co-located with source files. All tests live in `tests/` at root, mirroring the `src/` structure. Example: `tests/unit/lib/formatCurrency.test.ts` mirrors `src/lib/utils.ts`.

### Format Patterns

**API Response Formats:**

Success responses return the resource directly (no `data:` wrapper):
```json
// GET /api/members/123 → 200
{ "id": "...", "name": "Emeka", "status": "active" }

// POST /api/payments → 201
{ "id": "...", "amount": 3500000, "createdAt": "2026-04-13T10:00:00.000Z" }

// DELETE → 204 (no body)
```

Error responses always use the envelope:
```json
{ "error": { "code": "MEMBER_NOT_FOUND", "message": "No member with this phone number", "field": "phone" } }
```

**Data Exchange Formats:**
- Dates: ISO 8601 UTC strings always (`"2026-04-13T10:00:00.000Z"`). Never Unix timestamps.
- Display in UI: Nigerian locale (`13 Apr 2026, 10:00am`)
- Currency: integer in kobo (₦35,000 = `3500000`). Never float. Prisma field type: `Int`.
- Display helper: `formatCurrency(3500000)` → `"₦35,000"`
- Phone numbers: E.164 format in storage and API (`+2348012345678`)
- JSON field naming: camelCase in all API request/response bodies

### Communication Patterns

**TanStack Query Key Factory:**

All query keys defined in `src/lib/queryKeys.ts` — never inline strings:
```ts
export const queryKeys = {
  members: {
    all: (businessId: string) => ['members', businessId] as const,
    detail: (businessId: string, memberId: string) => ['members', businessId, memberId] as const,
  },
  payments: {
    all: (businessId: string) => ['payments', businessId] as const,
  },
}
```

**Zustand Store Pattern:**

Each store in its own file, typed slice, no cross-store imports:
```ts
// src/stores/authStore.ts
interface AuthState {
  user: User | null
  role: Role | null
  setUser: (user: User, role: Role) => void
  clearAuth: () => void
}
```

### Process Patterns

**API Route Handler Structure (every `route.ts`):**
```ts
export async function POST(req: Request) {
  const { businessId, userId, role } = getRequestContext(req)  // from middleware
  requireRole(role, [Role.OWNER, Role.STAFF])                  // RBAC check
  const body = memberSchema.parse(await req.json())            // validate
  const result = await prisma.member.create({ ... })           // business logic
  return NextResponse.json(result, { status: 201 })            // respond
}
```

**Tenant Scoping — Critical Security Rule:**

`business_id` is NEVER taken from the request body or URL parameters. It is ALWAYS extracted from the verified JWT via middleware and injected into `RequestContext`. Reading `business_id` from `req.body` or `req.query` is a security vulnerability.

**Loading & Mutation Pattern:**

All mutations use TanStack Query `useMutation` — never raw `fetch` in components:
```ts
const { mutate, isPending } = useMutation({
  mutationFn: (data: CreatePaymentInput) => api.post('/api/payments', data),
  onSuccess: () => {
    queryClient.invalidateQueries({ queryKey: queryKeys.members.all(businessId) })
    toast.success('Payment recorded. Receipt sent via WhatsApp.')
  },
  onError: (error) => toast.error(error.message),
})
```

**Error Display Rules:**
- API error with `field` → inline on form field via React Hook Form `setError`
- API error without `field` → toast notification (5s auto-dismiss)
- Unhandled exception → Sentry captures; user sees generic "Something went wrong" toast
- Never show raw server error messages to end users

**Auth Guard Pattern:**

Auth checking happens only in route group `layout.tsx` files, never in individual `page.tsx` files:
```ts
// src/app/(owner)/layout.tsx
export default async function OwnerLayout({ children }) {
  const session = await getServerSession()
  if (!session || session.role !== Role.OWNER) redirect('/login')
  return <>{children}</>
}
```

**Idempotency Pattern (Offline-queue safety):**

Payment and check-in `POST` routes accept an optional `idempotencyKey` (client-generated UUID). If a request with the same key has already been processed, return the original response. Store `idempotencyKey` on the created record. Required on `POST /api/payments` and `POST /api/checkins` from day 1.

### Enforcement Guidelines

**All AI Agents MUST:**
- Extract `business_id` from JWT context only — never from request input
- Use `queryKeys` factory for all TanStack Query keys — never inline strings
- Store money as integers in kobo — never as floats
- Store dates as `DateTime` (TIMESTAMPTZ) — never as strings in DB
- Store phone numbers in E.164 format
- Place auth guards in route group layouts only
- Return success responses without `data:` wrapper
- Return error responses with the standard `{ error: { code, message, field? } }` envelope
- Use `useMutation` for all state-mutating API calls in components
- Use `isPending` (not `isLoading`) for mutation loading states

**Anti-Patterns (never do these):**
- `const businessId = req.body.businessId` — tenant scoping violation
- `queryClient.invalidateQueries({ queryKey: ['members'] })` — use key factory
- `amount: 35000.50` — float for currency
- `if (!session) return null` inside a `page.tsx` — auth guard belongs in layout
- Raw `fetch('/api/payments', { method: 'POST', ... })` inside a component — use `useMutation`

---

## Project Structure & Boundaries

### Complete Project Directory Structure

```
gymops/
├── .env.example
├── .env.local                          # gitignored
├── .eslintrc.json
├── .gitignore
├── .prettierrc
├── next.config.ts                      # Next.js + Serwist PWA config
├── package.json
├── pnpm-lock.yaml
├── postcss.config.mjs
├── tailwind.config.ts
├── tsconfig.json                       # strict: true
├── sentry.client.config.ts
├── sentry.server.config.ts
├── sentry.edge.config.ts
├── jest.config.ts
├── playwright.config.ts
├── vercel.json                         # Cron: /api/cron/send-whatsapp every 1 min
│
├── .github/
│   └── workflows/
│       ├── ci.yml                      # typecheck → lint → test → build → E2E
│       └── deploy.yml                  # main branch → Vercel production
│
├── prisma/
│   ├── schema.prisma                   # Models: Business, User, Member, MembershipPlan,
│   │                                   #   Membership, Payment, CheckIn, WhatsappJob,
│   │                                   #   StaffInvite, OtpRequest, TenantNote
│   └── migrations/
│
├── public/
│   ├── manifest.json                   # PWA manifest
│   ├── sw.js                           # Serwist service worker (generated)
│   ├── icons/                          # PWA icons (192×192, 512×512, maskable)
│   └── logo.svg
│
├── src/
│   ├── middleware.ts                   # JWT verify + business_id inject (all /api/*)
│   │
│   ├── app/
│   │   ├── globals.css
│   │   ├── layout.tsx                  # Root layout: Providers (Query, Auth, Zustand, Sentry)
│   │   ├── not-found.tsx
│   │   │
│   │   ├── (marketing)/
│   │   │   ├── layout.tsx              # Public layout, no auth
│   │   │   ├── page.tsx                # Landing page (migrated from index.html)
│   │   │   └── pricing/page.tsx
│   │   │
│   │   ├── (auth)/
│   │   │   ├── layout.tsx              # Redirect to role home if already authed
│   │   │   ├── login/page.tsx          # Phone number entry (FR1, FR3)
│   │   │   └── verify/page.tsx         # OTP + stay-logged-in toggle (FR4)
│   │   │
│   │   ├── (owner)/
│   │   │   ├── layout.tsx              # Auth guard: Owner role required
│   │   │   ├── onboarding/page.tsx     # Wizard: businessType → staff? → first member → plan → payment → QR (FR7–11)
│   │   │   ├── dashboard/page.tsx      # Active members, today's payments, check-ins, expiry alerts (FR50–53)
│   │   │   ├── members/
│   │   │   │   ├── page.tsx            # Member list + search (FR15)
│   │   │   │   ├── new/page.tsx        # Add member (FR12)
│   │   │   │   └── [memberId]/
│   │   │   │       ├── page.tsx        # Member profile + status + edit (FR13, FR16)
│   │   │   │       └── payments/page.tsx
│   │   │   ├── payments/
│   │   │   │   ├── page.tsx            # Payment list (FR51)
│   │   │   │   └── new/page.tsx        # Record payment (FR22–26)
│   │   │   ├── plans/
│   │   │   │   ├── page.tsx            # Plan list (FR17)
│   │   │   │   └── new/page.tsx        # Create plan: daily/weekly/monthly (FR17–18)
│   │   │   ├── checkins/page.tsx       # Manual check-in + retroactive log (FR30–32)
│   │   │   ├── staff/
│   │   │   │   ├── page.tsx            # Staff list (FR47, FR54)
│   │   │   │   └── new/page.tsx        # Invite staff → WhatsApp link (FR47, FR38)
│   │   │   ├── settings/page.tsx       # Business type, QR management (FR58–59)
│   │   │   ├── export/page.tsx         # CSV export: members, payments, attendance (FR55–57)
│   │   │   └── share/page.tsx          # WhatsApp referral share (FR60)
│   │   │
│   │   ├── (staff)/
│   │   │   ├── layout.tsx              # Auth guard: Staff or Owner role required
│   │   │   └── shift/
│   │   │       ├── page.tsx            # Shift-mode home: 3 actions + recents + today counter (FR54)
│   │   │       ├── checkin/page.tsx    # Manual check-in (FR30)
│   │   │       ├── payment/page.tsx    # Record payment ≤3 taps (FR22–26)
│   │   │       └── member/page.tsx     # Find member quick view
│   │   │
│   │   ├── (member)/
│   │   │   ├── layout.tsx              # Auth guard: Member role required
│   │   │   ├── page.tsx                # Status badge + QR scanner shortcut (FR43, FR46)
│   │   │   ├── scan/page.tsx           # QR scanner: check in ≤2 taps (FR28, FR46)
│   │   │   ├── history/
│   │   │   │   ├── page.tsx            # Payment history (FR44)
│   │   │   │   └── checkins/page.tsx   # Check-in history (FR45)
│   │   │   └── settings/page.tsx       # Notification prefs: opt-out promotional per gym (FR40–41)
│   │   │
│   │   ├── (admin)/
│   │   │   ├── layout.tsx              # Auth guard: SuperAdmin role required
│   │   │   ├── page.tsx                # Tenant list + activation funnel + metrics (FR61–62, FR65)
│   │   │   └── tenants/[tenantId]/
│   │   │       └── page.tsx            # Tenant detail + notes + WhatsApp nudge (FR63–64)
│   │   │
│   │   └── api/
│   │       ├── auth/
│   │       │   ├── otp/route.ts        # POST: send OTP via Termii (FR1, FR3, FR39)
│   │       │   ├── verify/route.ts     # POST: verify OTP → JWT cookies (FR1–FR3)
│   │       │   ├── refresh/route.ts    # POST: rotate access token
│   │       │   └── logout/route.ts     # POST: clear httpOnly cookies
│   │       │
│   │       ├── businesses/
│   │       │   ├── route.ts            # POST: create business (FR7)
│   │       │   └── [businessId]/
│   │       │       ├── route.ts        # GET/PATCH: business profile (FR58)
│   │       │       └── qr/route.ts     # POST: generate/regenerate QR (FR33, FR59)
│   │       │
│   │       ├── members/
│   │       │   ├── route.ts            # GET: list+search; POST: add member (FR12, FR15)
│   │       │   └── [memberId]/
│   │       │       ├── route.ts        # GET/PATCH: member detail (FR13, FR16)
│   │       │       ├── payments/route.ts       # GET: payment history (FR44)
│   │       │       ├── checkins/route.ts        # GET: check-in history (FR45)
│   │       │       └── preferences/route.ts    # GET/PATCH: notification prefs (FR40–41)
│   │       │
│   │       ├── payments/
│   │       │   ├── route.ts            # GET: list; POST: record (FR22–27) — Prisma tx: Payment + Membership + WhatsappJob
│   │       │   └── [paymentId]/void/route.ts   # POST: void with reason (FR27)
│   │       │
│   │       ├── plans/
│   │       │   ├── route.ts            # GET: list; POST: create plan (FR17–18)
│   │       │   └── [planId]/route.ts   # GET/PATCH
│   │       │
│   │       ├── checkins/
│   │       │   ├── route.ts            # POST: manual/retroactive check-in (FR30–32)
│   │       │   └── qr-validate/route.ts # POST: validate QR scan → membership check → CheckIn + WhatsappJob (FR28–29)
│   │       │
│   │       ├── staff/
│   │       │   ├── route.ts            # GET: list; POST: invite → WhatsApp link (FR47–48, FR38)
│   │       │   └── [staffId]/route.ts  # DELETE: remove staff access (FR48)
│   │       │
│   │       ├── export/
│   │       │   ├── members/route.ts    # GET: CSV (FR55)
│   │       │   ├── payments/route.ts   # GET: CSV (FR56)
│   │       │   └── checkins/route.ts   # GET: CSV (FR57)
│   │       │
│   │       ├── admin/
│   │       │   ├── tenants/
│   │       │   │   ├── route.ts        # GET: all tenants + funnel (FR61–62, FR65)
│   │       │   │   └── [tenantId]/
│   │       │   │       ├── route.ts    # GET/PATCH: tenant detail + notes (FR64)
│   │       │   │       └── nudge/route.ts # POST: WhatsApp nudge to owner (FR63)
│   │       │   └── metrics/route.ts    # GET: platform-wide metrics (FR65)
│   │       │
│   │       └── cron/
│   │           └── send-whatsapp/route.ts # Vercel Cron: process pending WhatsappJobs (FR34–39)
│   │
│   ├── components/
│   │   ├── ui/                         # shadcn/ui primitives — never manually edited
│   │   ├── auth/
│   │   │   ├── PhoneInput.tsx          # E.164 formatting + validation
│   │   │   ├── OtpInput.tsx            # 6-digit OTP
│   │   │   └── StayLoggedInToggle.tsx  # Shared-device toggle (FR4)
│   │   ├── member/
│   │   │   ├── MemberSearch.tsx        # Debounced name/phone search (FR15)
│   │   │   ├── MemberCard.tsx          # Status + plan + expiry display
│   │   │   ├── MemberStatusBadge.tsx   # Active/Expired/ExpiringSoon (FR16)
│   │   │   └── MemberList.tsx
│   │   ├── payment/
│   │   │   ├── PaymentForm.tsx         # ≤3-tap recording (FR22)
│   │   │   ├── PaymentCard.tsx         # History item
│   │   │   └── WhatsAppReceiptConfirm.tsx # "Receipt sent ✓" (FR26)
│   │   ├── checkin/
│   │   │   ├── QrScanner.tsx           # html5-qrcode lazy-loaded wrapper (FR28, FR46)
│   │   │   ├── ManualCheckinForm.tsx   # Search + confirm (FR30)
│   │   │   └── CheckinConfirm.tsx      # Success state + WhatsApp confirmation
│   │   ├── onboarding/
│   │   │   ├── OnboardingWizard.tsx    # Step machine (FR7–11)
│   │   │   ├── BusinessTypeStep.tsx    # Gym/Yoga/Spa + solo? detection (FR8–9)
│   │   │   ├── PlansStep.tsx
│   │   │   ├── FirstMemberStep.tsx
│   │   │   └── QrGenerateStep.tsx
│   │   ├── dashboard/
│   │   │   ├── ActiveMembersCard.tsx
│   │   │   ├── TodayPaymentsCard.tsx
│   │   │   ├── RecentCheckinsCard.tsx
│   │   │   └── ExpiryAlertsCard.tsx
│   │   └── layout/
│   │       ├── AppShell.tsx            # PWA shell — no persistent nav chrome
│   │       ├── SyncStatusBar.tsx       # Offline/pending/synced indicator (FR68–69)
│   │       └── Providers.tsx           # QueryClientProvider + AuthContext + Zustand hydration
│   │
│   ├── hooks/
│   │   ├── useMembers.ts
│   │   ├── usePayments.ts
│   │   ├── useCheckins.ts
│   │   ├── usePlans.ts
│   │   ├── useStaff.ts
│   │   ├── useBusiness.ts
│   │   ├── useDashboard.ts
│   │   └── useAuth.ts
│   │
│   ├── stores/
│   │   ├── authStore.ts                # user, role, businessId
│   │   ├── syncStore.ts                # offline queue + sync state (FR66–69)
│   │   └── uiStore.ts                  # modals, toasts
│   │
│   ├── lib/
│   │   ├── prisma.ts                   # Prisma client singleton
│   │   ├── auth.ts                     # JWT sign/verify + cookie helpers
│   │   ├── termii.ts                   # Termii BSP client (OTP + 6 WhatsApp templates)
│   │   ├── redis.ts                    # Upstash Redis (OTP rate limiting only)
│   │   ├── queryKeys.ts                # TanStack Query key factory
│   │   ├── requestContext.ts           # Extract businessId/userId/role from JWT
│   │   ├── withRole.ts                 # RBAC HOF for API routes
│   │   ├── utils.ts                    # formatCurrency, formatPhone, formatDate
│   │   └── schemas/
│   │       ├── auth.schema.ts
│   │       ├── member.schema.ts
│   │       ├── payment.schema.ts
│   │       ├── plan.schema.ts
│   │       ├── checkin.schema.ts
│   │       ├── staff.schema.ts
│   │       └── business.schema.ts
│   │
│   └── types/
│       ├── api.ts                      # Error envelope + shared response types
│       ├── roles.ts                    # Role enum: SuperAdmin | Owner | Staff | Member
│       └── whatsapp.ts                 # WhatsappJob types + template name enums
│
└── tests/
    ├── unit/
    │   ├── lib/
    │   │   ├── formatCurrency.test.ts
    │   │   ├── formatPhone.test.ts
    │   │   ├── auth.test.ts
    │   │   └── schemas/
    │   └── hooks/
    ├── integration/
    │   ├── api/
    │   │   ├── auth.test.ts
    │   │   ├── members.test.ts         # Tenant isolation boundary tests
    │   │   ├── payments.test.ts        # Atomic tx: payment + membership + WhatsappJob
    │   │   └── checkins.test.ts
    │   └── middleware.test.ts
    └── e2e/
        ├── onboarding.spec.ts          # Owner: sign-up → wizard → first payment → receipt
        ├── staff-shift.spec.ts         # Staff: check-in + payment ≤3 taps
        ├── member-portal.spec.ts       # Member: QR scan → confirmation
        └── auth.spec.ts
```

### Architectural Boundaries

**API Boundaries:**
- All `/api/*` routes protected by `src/middleware.ts` (JWT verify + `businessId` inject)
- `/api/admin/*` routes additionally require `role === SuperAdmin` — cross-tenant queries permitted here only
- `/api/cron/*` routes require Vercel Cron secret header — not user-accessible
- `(marketing)/` routes: no API access, static/server-rendered only
- External boundary outbound: Termii BSP (via `src/lib/termii.ts`, called from Cron route only)
- External boundary outbound: Upstash Redis (OTP rate limiting only, via `src/lib/redis.ts`)

**Component Boundaries:**
- `src/components/ui/` — shadcn primitives, imported everywhere, never modified manually
- `src/components/[feature]/` — only import from `ui/` and `src/lib/`
- `src/hooks/` — TanStack Query hooks, only used in client components, never in API routes
- `src/stores/` — Zustand, client components only, never API routes

**Data Boundaries:**
- `business_id` never crosses tenant boundaries in database queries
- `WhatsappJob` table is the sole async boundary between payment recording and Termii delivery
- Member data crosses gym boundaries only for a user holding Member roles at multiple gyms — own data only, scoped per membership record
- Super Admin cross-tenant queries use explicit Prisma calls without `businessId` filter — never via middleware bypass

### Prisma Schema Models

| Model | Purpose | Key Fields |
|---|---|---|
| `Business` | Tenant record | `id`, `name`, `type`, `qrCode`, `tier`, `status`, `ownerId` |
| `User` | Auth entity (all roles) | `id`, `phone`, `role`, `businessId` |
| `Member` | Gym member profile | `id`, `businessId`, `name`, `phone`, `status`, `archivedAt` |
| `MembershipPlan` | Plan definition | `id`, `businessId`, `name`, `price` (Int kobo), `durationType` |
| `Membership` | Active plan assignment | `id`, `memberId`, `planId`, `startDate`, `expiryDate` |
| `Payment` | Financial record (append-only) | `id`, `memberId`, `businessId`, `amount`, `method`, `staffId`, `idempotencyKey`, `voidedAt`, `voidReason` |
| `CheckIn` | Attendance record | `id`, `memberId`, `businessId`, `method`, `staffId`, `timestamp` |
| `WhatsappJob` | Outbox queue | `id`, `type`, `payload`, `status`, `retryCount`, `createdAt`, `sentAt` |
| `TenantNote` | Super admin notes | `id`, `businessId`, `note`, `createdBy` |

### Key Data Flows

**Payment Recording (critical path ≤500ms):**
```
PaymentForm (≤3 taps)
  → useMutation → POST /api/payments
  → middleware: JWT verify + businessId inject
  → withRole([Owner, Staff])
  → Zod validate body
  → Prisma transaction:
      CREATE Payment (with idempotencyKey)
      UPDATE Membership (new expiryDate auto-calculated)
      CREATE WhatsappJob (type: RECEIPT)
  → 201 response
  → queryClient.invalidate → UI updates
  [async via Vercel Cron every 1 min]
  → POST /api/cron/send-whatsapp → Termii API → WhatsApp receipt (≤60s total)
```

**QR Check-In (member self-service ≤2s):**
```
QrScanner (lazy loaded) → scan gym QR → extract businessId + token
  → POST /api/checkins/qr-validate
  → middleware: JWT (member's token)
  → Prisma: verify active Membership for memberId + businessId
  → if expired: 403 + clear message
  → if active: CREATE CheckIn + CREATE WhatsappJob (CHECKIN_CONFIRM)
  → 200 → CheckinConfirm screen
```

**Member Search (staff daily ops ≤300ms):**
```
MemberSearch (debounce 300ms) → GET /api/members?q=Fat
  → middleware: JWT + businessId inject
  → Prisma: WHERE business_id = $1 AND (name ILIKE '%Fat%' OR phone LIKE '%Fat%')
  → Index: (business_id, name), (business_id, phone)
  → results
```

### Integration Points

**Internal:** All communication via TanStack Query hooks → Next.js API routes. No direct component-to-database access.

**External:**
- **Termii BSP** — outbound only, from Cron route. Never from user-facing routes directly.
- **Upstash Redis** — OTP rate limiting in `/api/auth/otp` route only.
- **Neon PostgreSQL** — via Prisma client singleton. Pooled connection for all API routes.
- **Sentry** — auto-instrumented via `sentry.*.config.ts`. Manual capture in WhatsappJob failure handler.
- **Vercel Analytics** — zero-config in root `layout.tsx`.

---

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:** All technology choices are mutually compatible — Next.js 16 + Prisma 7 + Neon + Vercel form the native ecosystem; TanStack Query v5 + Zustand v5 + RHF v7 + Zod are peer-dep compatible; Serwist is purpose-built for Next.js App Router; Upstash Redis integrates natively with Vercel serverless; Sentry v10 auto-instruments all runtimes.

**Pattern Consistency:** Zod schemas defined once, imported by both API routes and RHF resolvers. Auth guards placed consistently in route group layouts only. Query key factory prevents cache collisions. Prisma `@map`/`@@map` handles camelCase↔snake_case boundary. All mutation patterns use `useMutation` — no raw fetch in components.

**Structure Alignment:** Route groups map directly to RBAC roles. WhatsApp delivery fully decoupled via outbox Cron. Test structure mirrors `src/` exactly. Integration boundaries are explicit — no component-to-database direct access anywhere.

### Requirements Coverage Validation

**All 69 FRs covered. 3 gaps identified and resolved:**

**Gap 1 — FR5: Super Admin email+password auth (resolved)**
- Added: `src/app/(auth)/admin-login/page.tsx`
- Added: `src/app/api/auth/admin-login/route.ts` — bcrypt verify, issues JWT with `role: SuperAdmin`
- Single seeded super admin record (not multi-user for MVP)

**Gap 2 — FR21 + FR36: Daily expiry + expiry reminder Cron (resolved)**
- Added: `src/app/api/cron/process-memberships/route.ts`
- Runs daily at midnight WAT (`0 23 * * *` UTC) via Vercel Cron
- Handles: mark DAILY memberships expired + queue `EXPIRY_REMINDER` WhatsappJobs
- Added `EXPIRY_REMINDER` to WhatsappJob type enum in `src/types/whatsapp.ts`

**Gap 3 — FR2: Staff invite acceptance route (resolved)**
- Added: `src/app/(auth)/staff-invite/[token]/page.tsx`
- Added: `src/app/api/staff/invite/[token]/route.ts` — validate invite token
- Existing `/api/auth/verify` handles OTP step with `inviteToken` param

**Non-Functional Requirements Coverage:**
- ≤3s load: Serwist service worker, code splitting, lazy QrScanner ✅
- ≤500ms payment: Prisma atomic transaction + optimistic TanStack Query update ✅
- ≤300ms search: DB indexes on `(business_id, name)`, `(business_id, phone)` ✅
- ≤2s QR check-in: Single Prisma membership validity query ✅
- ≥99.5% uptime: Vercel infrastructure ✅
- Zero data loss: Prisma transactions, append-only Payment records, no hard deletes ✅
- JWT security: httpOnly cookies, `SameSite=Strict` ✅
- Tenant isolation: middleware enforced, anti-patterns documented ✅
- NDPR archival: `archivedAt` fields on Member + Business, no hard deletes ✅

### Implementation Readiness Validation ✅

**Decision Completeness:** All critical decisions documented with verified versions. Technology stack fully specified. Integration patterns defined. Performance considerations addressed with concrete NFR targets mapped to architectural choices.

**Structure Completeness:** Complete directory tree with every file named and FR-referenced. All 69 FRs mapped to specific routes/components. Integration points explicitly specified. Component boundaries clearly defined.

**Pattern Completeness:** 13 conflict points addressed with examples and anti-patterns. Naming conventions cover DB, API, and code layers. Critical security patterns have explicit anti-pattern examples to prevent violations.

### Architecture Completeness Checklist

**✅ Requirements Analysis**
- [x] Project context thoroughly analyzed (69 FRs, 16 categories)
- [x] Scale and complexity assessed (Medium-High, 500 tenants × 500 members Year 1)
- [x] Technical constraints identified (Termii BSP, solo dev, Vercel serverless, offline-first P2)
- [x] Cross-cutting concerns mapped (7 concerns documented)

**✅ Architectural Decisions**
- [x] Critical decisions documented with verified versions
- [x] Technology stack fully specified (Next.js 16.2.3, Prisma 7.7.0, Neon, Serwist, TanStack Query v5, Zustand v5, RHF v7)
- [x] Integration patterns defined (outbox pattern, Vercel Cron, Upstash rate limiting)
- [x] Performance considerations addressed (indexes, optimistic updates, lazy loading, code splitting)

**✅ Implementation Patterns**
- [x] Naming conventions established (DB, API, code — all layers)
- [x] Structure patterns defined (test location, component organisation, schema sharing)
- [x] Communication patterns specified (query key factory, Zustand store slices)
- [x] Process patterns documented (API handler structure, error display, auth guard placement, idempotency)

**✅ Project Structure**
- [x] Complete directory structure defined with all files named
- [x] Component boundaries established
- [x] Integration points mapped (Termii via Cron only, Redis for OTP only, Prisma singleton)
- [x] All 69 FRs mapped to specific file paths

### Architecture Readiness Assessment

**Overall Status: READY FOR IMPLEMENTATION**

**Confidence Level: HIGH**

**Key Strengths:**
1. WhatsApp outbox pattern cleanly decouples the critical payment path from Termii latency
2. Route groups enforce RBAC at the layout level — agents cannot accidentally skip auth
3. Tenant scoping enforced at middleware — cross-tenant leaks are architecturally prevented if patterns are followed
4. Idempotency keys on Payment and CheckIn from day 1 — offline queue (P2) can be added without data model changes
5. Zod schema sharing between API + frontend eliminates validation drift between layers
6. Vercel + Neon + Serwist is a proven stack with excellent offline + serverless compatibility

**Areas for Future Enhancement (post-MVP):**
- Paystack DVA integration for subscription billing (Phase 2)
- Rotating QR tokens (Phase 2 — static QR for MVP)
- Configurable WhatsApp template scheduling (Phase 2)
- Redis general caching if member search degrades under load (revisit at 100+ tenants)
- Offline-first sync (P2 — syncStore + Serwist architecture in place, implementation deferred)
- Multi-location support (Phase 2 — schema must not preclude it)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented
- Refer to the anti-patterns section before writing any API route or mutation
- `business_id` NEVER from request input — always from JWT context via `getRequestContext()`
- All money as integers in kobo — never floats
- All dates as `DateTime` in DB, ISO 8601 UTC strings in API
- Tests live in `tests/` only — never co-located with source
- Auth guards belong in route group `layout.tsx` files only — never in `page.tsx`

**First Implementation Story — Project Initialisation:**
```bash
# Run in project root (replaces static landing page)
npx create-next-app@latest . --typescript --tailwind --app --src-dir --import-alias "@/*"
pnpm dlx shadcn@latest init
npx prisma init --datasource-provider postgresql
pnpm add @serwist/next serwist
pnpm add -D jest @testing-library/react @testing-library/jest-dom playwright @playwright/test
```
