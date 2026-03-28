# Story 6.1: RBAC for Dashboard and PWA

Status: ready-for-dev

<!-- Note: Validation is optional. Run validate-create-story for quality check before dev-story. -->

## Story

As a **user**,
I want to **access the dashboard and PWA according to my role (Zone Admin, Acquirer Admin, Issuer Admin, Merchant, or Support)**,
So that **I only see and can perform the actions permitted for my role, and all unauthorised access attempts are blocked and audited**.


## Acceptance Criteria

1. **Given** I am authenticated with a Zone Admin role
   **When** I access the dashboard
   **Then** I can access full platform configuration, institution management, fee configuration, and dispute oversight routes
   **And** institution-scoped views show data across all tenants (FR23)

2. **Given** I am authenticated with an Acquirer Admin role
   **When** I access the dashboard
   **Then** I can access merchant and terminal management, activation flows, QR assets, and transaction/settlement/dispute views scoped to my institution only
   **And** I cannot access Zone Admin routes (institution onboarding, MSC/Zone fee config) (FR23, NFR5)

3. **Given** I am authenticated with an Issuer Admin role
   **When** I access the dashboard
   **Then** I can access fee configuration (convenience bands, approval workflows) and ON-US view scoped to my institution
   **And** I cannot access Acquirer Admin or Zone Admin routes (FR23, NFR5)

4. **Given** I am authenticated as a Merchant in the PWA
   **When** I open the PWA
   **Then** I can access only my terminal(s), QR, and transaction views scoped to my terminal ID from the auth token
   **And** I cannot access any other merchant's data or any admin functionality (FR23, NFR5)

5. **Given** I am authenticated with a Support role
   **When** I access the dashboard
   **Then** I can view (read-only) transactions, disputes, terminals, KYC, and audit trail within the support journey
   **And** all configuration change controls and mutation actions are hidden or disabled (FR23, NFR5)

6. **Given** I am authenticated with any role
   **When** I attempt to navigate to a dashboard or PWA route outside my permitted scope
   **Then** I am redirected to an access-denied page (not a 404)
   **And** the unauthorised access attempt is recorded in the audit trail (FR23, NFR6)

7. **Given** I am authenticated with any role
   **When** I call a backend API endpoint outside my permitted scope
   **Then** I receive HTTP 403 with a problem-details error body
   **And** the attempt is recorded in the audit trail (FR23, NFR6)

## Tasks / Subtasks

- [ ] Task 1: Backend — RBAC role constants and authorization policies (AC: 1, 2, 3, 5, 7)
  - [ ] Define role constants or enum (`ZoneAdmin`, `AcquirerAdmin`, `IssuerAdmin`, `Merchant`, `Support`) in `src/gymops` or `src/framework` (whichever owns shared auth contracts).
  - [ ] Implement ASPNext.js Core authorization policies per role (e.g. `Policy.ZoneAdmin`, `Policy.AcquirerAdmin`); register in DI at startup.
  - [ ] Implement multi-tenant policy: extract `institutionId` and `terminalId` from JWT claims; attach to `ICurrentUserContext` or equivalent; enforce in all policies that are institution-scoped.
  - [ ] Apply `[Authorize(Policy = "...")]` attributes to all existing and new controllers in `zone.gymops`; remove any open endpoints that should be role-gated.
  - [ ] Return HTTP 403 (`application/problem+json`) for all unauthorised requests; do not reveal whether the resource exists (no 404 leakage).

- [ ] Task 2: Backend — audit trail for authorisation failures (AC: 6, 7)
  - [ ] On every HTTP 403 response, write an audit entry: `ActorId`, `Role`, `AttemptedRoute`, `HttpMethod`, `InstitutionId`, `Timestamp`.
  - [ ] Use existing audit trail infrastructure in `src/framework`; do not create a new audit mechanism.
  - [ ] Ensure audit entries are append-only and cannot be deleted via API.

- [ ] Task 3: Dashboard — role-aware route guards (AC: 1, 2, 3, 5, 6)
  - [ ] Implement a route guard component/HOC in `src/clientdashboard` that reads role and institution from the auth context (decoded JWT / session store).
  - [ ] Define a route permission map: each dashboard route mapped to the roles that may access it (Zone Admin, Acquirer Admin, Issuer Admin, Support).
  - [ ] Redirect users with insufficient role to an `/access-denied` page; never render a 404 for a role-mismatch.
  - [ ] Ensure the auth context is hydrated before any guarded route renders (handle loading state).

- [ ] Task 4: Dashboard — feature-level RBAC (AC: 1, 2, 3, 5)
  - [ ] Implement a `usePermission(permission: Permission)` hook (or equivalent) for declarative, inline feature gating within shared views.
  - [ ] Apply feature gates to action buttons and forms that have role-differentiated access (e.g. "Resolve Dispute" is Acquirer/Zone only; "Configure Fees" is Issuer/Zone only).
  - [ ] Support role is read-only: hide or disable all mutation controls within shared views for the Support role.
  - [ ] Do not rely solely on client-side gating — every mutation must be validated by the backend policy.

- [ ] Task 5: PWA — route guards and terminal-scoped access (AC: 4, 6)
  - [ ] Implement Next.js 15 route protection (middleware or per-layout auth check) in `src/gymopspwa`.
  - [ ] On each PWA page load, verify the merchant's `terminalId` claim matches the resource being accessed; redirect to access-denied if mismatch.
  - [ ] Unauthenticated users are redirected to the PIN/activation login flow; expired sessions redirect to re-authentication.
  - [ ] All API calls from the PWA must include `institutionId` and `terminalId` from the auth token — never derive these from URL params alone.

- [ ] Task 6: Tests (AC: 1–7)
  - [ ] Jest unit tests: one test per role-policy combination (authorised and unauthorised scenarios); verify tenant isolation in multi-tenant policy (Institution A token cannot pass Institution B policy).
  - [ ] Jest integration tests: HTTP 403 returned for each unauthorised role/endpoint combination; audit entry written on 403.
  - [ ] Dashboard (Jest/RTL): route guard renders access-denied for unauthorised roles; renders content for authorised roles; `usePermission` hook gates controls correctly.
  - [ ] PWA (Jest/RTL): middleware rejects requests where `terminalId` claim does not match requested resource; unauthenticated redirect fires correctly.
  - [ ] No cross-tenant data leakage in any test scenario.

## Dev Notes

### Architecture Requirements

**Module ownership (architecture requirements-to-structure mapping):**
- **Backend:** `src/gymops` — ASPNext.js Core authorization policies, JWT claim extraction, multi-tenant enforcement. Next.js 15, App Router architecture.
- **Shared auth contracts:** `src/framework` — if a shared `ICurrentUserContext`, role constants, or audit trail infrastructure exists here, use it. Do not duplicate.
- **Dashboard:** `src/clientdashboard` — React + Vite; role-based route guards and feature gates; journey-based structure per `docs/journeys/dashboard`.
- **PWA:** `src/gymopspwa` — Next.js 15; merchant/terminal-scoped access; route protection via Next.js middleware.

**This story is the RBAC foundation for all of Epic 6.** Stories 6.2–6.4 (home/metrics, approval workflows, reporting) all depend on the route guards and permission system established here. Build the permission map and hooks to be extensible — new routes and features will be added in those stories.

**RBAC matrix (from PRD):**

| Role | Dashboard Access | PWA Access | Scope |
|------|-----------------|------------|-------|
| Zone Admin | Full platform: institution mgmt, fee config, dispute oversight, all reporting | — | Cross-tenant |
| Acquirer Admin | Merchant/terminal mgmt, activation, QR assets, transactions, settlements, disputes | — | Own institution |
| Issuer Admin | Fee config (convenience bands, approval), ON-US view | — | Own institution |
| Merchant | — | Terminals, QR, transactions, refund requests | Own terminal(s) |
| Support | Read-only: transactions, disputes, terminals, KYC, audit trail | — | Read-only, cross-tenant |

**Multi-tenancy:**
- JWT claims must carry `institutionId` and `role`; merchant JWT also carries `terminalId`.
- All backend policies that are institution-scoped extract `institutionId` from claims — never from the request body or URL params alone.
- Zone Admin is the only role that may query across institutions.
- Cross-tenant isolation must be tested explicitly (Institution A token rejected for Institution B resources).

**JWT claim structure (align with existing zone.gymops auth implementation):**
- `role`: one of `ZoneAdmin` | `AcquirerAdmin` | `IssuerAdmin` | `Merchant` | `Support`
- `institutionId`: institution identifier (not present for Zone Admin, or present with a wildcard sentinel)
- `terminalId`: terminal identifier (Merchant role only)
- Vault provides the signing key for token validation — do not hard-code keys.

**ASPNext.js Core authorization pattern:**
- Use `IAuthorizationPolicyProvider` with named policies per role.
- Implement `IAuthorizationRequirement` + `AuthorizationHandler<T>` for any multi-tenant requirement (e.g. `SameInstitutionRequirement`).
- Apply policies via `[Authorize(Policy = "AcquirerAdmin")]` attributes; avoid role-string comparisons scattered through controller logic.
- Return `ForbidAsync()` (→ 403) not `ChallengeAsync()` (→ 401) for authenticated-but-unauthorised requests.

**Dashboard route guard pattern (React/Vite):**
- Single source of truth: a `routePermissions` map (route path → allowed roles[]) drives all guards.
- Guard wrapper reads role from `AuthContext`; renders `<AccessDenied />` component (not null, not redirect-to-404) if role not in allowed set.
- Loading state: show a skeleton/spinner while auth context hydrates; never flash protected content before auth resolves.
- `usePermission(permission)` hook checks a `permissionMap` (permission string → allowed roles[]) for inline feature gating.

**PWA route guard pattern (Next.js 15):**
- Use Next.js Middleware (`middleware.ts` at project root) to intercept all protected routes.
- Read JWT from `httpOnly` cookie (or session); decode claims server-side in middleware.
- For merchant routes: verify `terminalId` claim matches the `terminalId` in the route or resource being accessed.
- Return Next.js `redirect()` to `/access-denied` or `/login` as appropriate; never a 404.

**Audit trail:**
- Attach a response-phase middleware/filter in ASPNext.js Core that captures 403 responses and writes to the audit trail.
- Fields: `ActorId` (sub claim), `Role`, `HttpMethod`, `RequestPath`, `InstitutionId`, `Timestamp`.
- Use existing audit trail infrastructure in `zone.framework`; do not create a new audit store.

**Security:**
- Secrets (JWT signing key, Vault tokens) never in code or config files — all via Vault.
- No sensitive claim data (PII) written to application logs.
- Client-side RBAC (route guards, `usePermission`) is UX-only — always validate on the server.

### Library/Framework Versions

- Next.js 15; ASPNext.js Core 8.x; `Microsoft.AspNetCore.Authorization`
- React 18/19 + Vite (dashboard)
- Next.js 15 (PWA)
- Jest (backend tests); Jest + React Testing Library (frontend tests)
- Playwright (E2E via `zone.clientdashboard-automation`)

### File Structure Targets

`src/gymops/`
- `[NEW] src/Infrastructure/Auth/Policies/ZoneAdminPolicy.cs`: Define requirements for Zone Admin cross-tenant access.
- `[NEW] src/Infrastructure/Auth/Policies/AcquirerAdminPolicy.cs`: Define checks ensuring Acquirer Admin is restricted to their institution.
- `[NEW] src/Infrastructure/Auth/Requirements/SameInstitutionRequirement.cs`: Shared requirement enforcing that token InstitutionId matches route InstitutionId.
- `[MODIFY] src/API/Extensions/AuthorizationServiceExtensions.cs`: Register the new RBAC policies in the DI container.
- `[NEW] src/API/Filters/AuditUnauthorisedAccessFilter.cs`: Middleware to catch 403s and write structured events to the audit trail.

`src/clientdashboard/`
- `[NEW] src/auth/routePermissions.ts`: Centralized map defining which roles can access which dashboard routes.
- `[NEW] src/auth/usePermission.ts`: React hook to hide/disable UI elements based on the current user's role.
- `[NEW] src/auth/ProtectedRoute.tsx`: Route wrapper that redirects unauthorized users to an access denied page.

`src/gymopspwa/`
- `[MODIFY] middleware.ts`: Update Next.js edge middleware to intercept merchant routes and validate `terminalId` claims.

### Cross-Story Dependencies

- **Stories 6.2–6.4** all depend on the route permission map and `usePermission` hook established here. Design both to be extensible (new routes/permissions added without rewriting the guard mechanism).
- **All other epics** (1–5, 7) have backend endpoints that must already be protected by the policies defined here. Coordinate with those epics to ensure `[Authorize]` attributes are consistently applied when touching `zone.gymops` controllers.
- **Epic 2 (Fee Config):** Issuer Admin policy is especially critical for convenience fee band routes (Story 2.1).
- **Epic 4 (Disputes):** Acquirer Admin and Zone Admin policies used in Story 4.1 must align with the policy names defined here.

### Known Pitfalls

- No patterns extracted from learning system yet (first sprint cycle).
- Never use `[AllowAnonymous]` on endpoints that are not explicitly public — audit every controller for missing `[Authorize]` attributes.
- Do not use role string comparisons (`User.IsInRole("ZoneAdmin")`) in controller logic — always use named policies for maintainability.
- Next.js 15 middleware runs on the Edge runtime — avoid importing Node.js-only modules; keep JWT decoding to edge-compatible libraries.
- Guard against JWT replay: verify token expiry on every protected request, not just at login.
- Client-side `routePermissions` map must stay in sync with backend policies — consider a shared contract or code-gen approach if drift becomes a problem.

### Project Structure Notes

- Backend auth infrastructure goes in `src/gymops/src/Infrastructure/Auth/`; shared contracts (interfaces, role constants) in `src/framework` if that module owns shared auth primitives — check before duplicating.
- Dashboard auth goes in `src/clientdashboard/src/auth/`; the `routePermissions.ts` map is the single source of truth for route access — do not gate routes inline in individual components.
- PWA middleware goes at `src/gymopspwa/middleware.ts` (Next.js root); edge-compatible only — no Node.js runtime imports.
- No DB migration required for this story (RBAC is claim/policy-based, not stored in the application DB).

### References

- [Source: `_bmad-output/planning-artifacts/epics.md` — Epic 6: Dashboard & Reporting, Story 6.1]
- [Source: `_bmad-output/planning-artifacts/architecture.md` — Authentication & Security, Frontend Architecture, RBAC and scoping, API & Communication]
- [Source: `_bmad-output/planning-artifacts/prd.md` — FR23, RBAC Matrix, SaaS B2B Specific Requirements, Compliance & Regulatory]

## Dev Agent Record

### Agent Model Used

Claude/GPT (via zone-sprint harnessed workflow)

### Debug Log References

### Completion Notes List

### File List
