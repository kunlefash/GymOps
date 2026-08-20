---
stepsCompleted: [1, 2, 3, 4]
inputDocuments:
  - _bmad-output/planning-artifacts/prd.md
  - _bmad-output/planning-artifacts/architecture.md
  - _bmad-output/planning-artifacts/ux-design-specification.md
workflowType: 'epics-and-stories'
project_name: 'FitBase (GymOps)'
user_name: 'Adekunle'
date: '2026-08-20'
---

# FitBase (GymOps) - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for FitBase (GymOps), decomposing the requirements from the PRD, UX Design, and Architecture into implementable stories.

## Requirements Inventory

### Functional Requirements

FR1: Business operator can sign up with phone number and verify via WhatsApp OTP
FR2: Staff member can accept an invitation and set up access via WhatsApp link + OTP
FR3: Member can sign up and verify via WhatsApp OTP after receiving an invitation link
FR4: Any authenticated user can stay logged in on a device to avoid repeated OTP entry
FR5: Super admin can authenticate via email and password
FR6: System enforces role-based access control across four roles: super admin, owner, staff, member
FR7: Business operator can register a new business by selecting business type and entering business name
FR8: Business operator can indicate whether they operate solo or with staff during onboarding
FR9: System skips staff setup and QR generation steps for solo operators
FR10: Onboarding wizard guides operator through first member add, first payment, and QR generation in a single session
FR11: System provides default membership plan templates based on business type
FR12: Business operator or staff can add a new member with name and phone number
FR13: Business operator or staff can edit member details
FR14: Business operator or staff can archive a member
FR15: Business operator or staff can search members by partial name or phone number
FR16: System displays member status (active, expired, expiring soon) on member profile
FR17: Business operator can create membership plans with name, price, and duration type (daily, weekly, monthly)
FR18: Business operator can assign a plan to a member
FR19: System auto-calculates membership expiry date from plan duration and start date
FR20: Start date defaults to today with option to override for backdating
FR21: Daily (walk-in) memberships auto-expire at end of day
FR22: Business operator or staff can record a payment for a member specifying amount, payment method (cash/bank transfer), and optional note
FR23: System records the staff member who processed each payment
FR24: Payment recording automatically renews membership and updates expiry date
FR25: Walk-in payment recording combines payment and check-in in a single action
FR26: System sends automated WhatsApp receipt to member upon payment recording
FR27: Payments cannot be deleted — only voided with a reason for audit trail
FR28: Member can check in by scanning the gym's static QR code while logged into the app
FR29: System validates member's active membership status on QR scan and rejects expired memberships with a clear message
FR30: Business operator or staff can manually check in a member by searching and confirming
FR31: Business operator or staff can retroactively log a missed check-in for a member
FR32: System records check-in timestamp, method used (QR/manual), and staff ID for manual check-ins
FR33: Business operator can generate a unique static QR code for their business location
FR34: System sends payment receipt via WhatsApp using pre-approved template upon payment recording
FR35: System sends welcome message via WhatsApp with app install link when a new member is added
FR36: System sends membership expiry reminder via WhatsApp at configurable days before expiry (default: 5 days)
FR37: System sends check-in confirmation via WhatsApp upon successful check-in
FR38: System sends staff invitation via WhatsApp with onboarding link when owner adds staff
FR39: System sends OTP via WhatsApp for authentication (SMS fallback)
FR40: Member can opt out of business-promotional messages per gym
FR41: Transactional messages (receipts, expiry warnings, welcome) are always delivered and cannot be opted out of
FR42: System distinguishes between transactional (system-triggered) and promotional (business-triggered) messages
FR43: Member can view their membership status, plan, and expiry date
FR44: Member can view their payment history
FR45: Member can view their check-in history
FR46: Member can access a QR scanner to scan a gym's check-in QR code within 2 taps of opening the app
FR47: Business operator can add staff members by entering phone number and assigning a role
FR48: Business operator can remove staff access
FR49: Staff permissions are limited to: add/edit members, record payments, manual check-in, view limited dashboard
FR50: Business operator can view count of active members
FR51: Business operator can view payments recorded today
FR52: Business operator can view recent check-ins
FR53: Business operator can view upcoming membership expiry alerts
FR54: Staff can view a limited version of the dashboard (check-ins and payments only)
FR55: Business operator can export members list as CSV
FR56: Business operator can export payment records as CSV
FR57: Business operator can export attendance records as CSV
FR58: Business operator can configure business type and terminology
FR59: Business operator can manage check-in QR code (regenerate if compromised)
FR60: Business operator can share a pre-written WhatsApp invite message to refer other gym operators to FitBase
FR61: Super admin can view a list of all tenant businesses with trial/activation status
FR62: Super admin can view activation funnel per tenant (signed up → member added → payment recorded → QR generated)
FR63: Super admin can send a one-tap WhatsApp nudge to stalled trial businesses
FR64: Super admin can add notes per tenant for follow-up tracking
FR65: Super admin can view platform-wide metrics (total tenants, active trials, conversion rates)
FR66: System queues payment, check-in, and member writes locally when offline
FR67: System syncs queued writes to server when connectivity is restored
FR68: System displays current sync status to the user (synced / pending / failed)
FR69: System notifies the user explicitly if a sync operation fails

### NonFunctional Requirements

NFR1: PWA initial load ≤3 seconds to functional state on mid-range Android (Tecno/Infinix) over 3G
NFR2: Subsequent loads ≤1 second from cached service worker
NFR3: Payment recording ≤500ms from confirm tap to success confirmation
NFR4: Member search results within 300ms of typing
NFR5: QR scan to check-in ≤2 seconds end-to-end
NFR6: Support 5 simultaneous staff users per tenant without degradation
NFR7: HTTPS/TLS 1.2+ for all API communication
NFR8: Database encryption at rest via hosting provider
NFR9: JWT with 15-min access / 7-day refresh; httpOnly cookies with Secure, HttpOnly, SameSite=Strict
NFR10: OTP single-use, 10-minute expiry, rate-limited to 5 attempts per phone per hour
NFR11: All API queries scoped by business_id at middleware layer — no cross-tenant data leakage
NFR12: Payment audit trail — immutable records (append-only); void creates new audit entry; no hard deletes
NFR13: NDPR compliance: privacy notice at registration; data retention policy; personal data archived not deleted
NFR14: Architecture supports 500 tenants × 500 members each (250,000 member records) for Year 1
NFR15: Single PostgreSQL instance for Year 1; schema supports future partitioning
NFR16: Stateless API; horizontal scaling via Vercel serverless
NFR17: WhatsApp via Termii: 99.9% availability; SMS fallback on failure; 60-second delivery target; 6 pre-approved templates
NFR18: Offline sync: 100 pending writes before warning; server-authoritative; FIFO sync within 30 seconds of reconnect; failed syncs surface to user with retry
NFR19: API uptime ≥99.5% monthly
NFR20: Zero data loss — every write confirms or fails with notification; no silent loss
NFR21: Zero undetected divergence — local state never silently differs from server state
NFR22: Daily automated backups with 30-day retention
NFR23: Database restorable within 1 hour of incident

### Additional Requirements

**From Architecture:**
- Project must be initialised using create-next-app@latest (first implementation story — Epic 1 Story 1)
- Neon (serverless PostgreSQL) must be provisioned as database provider before any DB work
- Prisma migrate deploy must run in CI build step before build
- WhatsApp delivery uses outbox pattern: whatsapp_jobs table + Vercel Cron every 1 minute
- Upstash Redis required for OTP rate limiting (5 attempts/hr) via @upstash/ratelimit
- Serwist (Next.js App Router compatible) for PWA service worker and caching
- Sentry v10 + Vercel Analytics for error capture and Core Web Vitals monitoring
- GitHub Actions CI: typecheck → lint → unit tests → build → Playwright E2E → Vercel preview deploy
- Super admin email+password auth route (FR5 gap): (auth)/admin-login + /api/auth/admin-login with bcrypt
- Daily expiry + expiry reminder Cron (FR21+FR36 gap): /api/cron/process-memberships running midnight WAT
- Staff invite acceptance route (FR2 gap): /api/staff/invite/[token] + (auth)/staff-invite/[token] page
- All money stored as integers in kobo (₦35,000 = 3500000) — never floats
- All dates as DateTime (TIMESTAMPTZ) in DB, ISO 8601 UTC strings in API
- business_id always from JWT context via middleware — never from request body or URL
- Tests live in tests/ only — never co-located with source files
- Auth guards in route group layout.tsx files only — never in page.tsx

**From UX Design:**
- Mobile-first responsive design: 320px–767px primary, 768px–1023px tablet, 1024px+ desktop (max-width 480px centred)
- WCAG 2.1 Level AA compliance required across all screens
- Touch targets minimum 44×44px (WCAG 2.5.5); primary CTAs 56px height; list items 64px minimum
- All colour combinations must meet WCAG AA contrast ratios (defined in UX spec)
- Status never conveyed by colour alone — always colour + text + icon
- OTP inputs use autocomplete="one-time-code" for Android WhatsApp auto-fill
- Success screen animation must respect prefers-reduced-motion media query
- Safe area insets required: pb-[env(safe-area-inset-bottom)] on bottom nav and drawers
- Use dvh not vh for full-screen layouts (iOS Safari toolbar overlap prevention)
- Font: Inter via next/font/google with display:swap
- Numeric currency inputs use inputmode="numeric" not type="number" (Naira formatting)
- Bank transfer flow: no auto-activation; owner confirms pending payments before receipt fires; bank account setup banner in owner dashboard (conditional, disappears once configured)
- QR check-in uses native device camera via URL-based deep link — not in-app scanner; gym QR contains URL that deep-links to PWA
- New visitor self-enroll flow on QR scan (unregistered visitor)
- Contextual login for known member on unknown device after QR scan
- Staff shift screen: no tab bar, 3 full-width action buttons + recents list (last 5 members) + today counter chip
- Owner navigation: 4-tab bottom nav (Dashboard / Members / Payments / Settings)
- Member navigation: 3-tab bottom nav (Status / Check In / History)
- SyncIndicator persistent chip on all staff/owner screens (synced / N pending / failed / offline states)
- PaymentSuccessScreen is full-screen, non-dismissable, with "Check In [Name]" primary CTA + "Done" ghost
- Empty states: icon + message + optional CTA; never "No data available"
- Member search: results after 2 characters (200ms debounce), by name or phone; no-results prompts "Add as new member?"

### FR Coverage Map

FR1: Epic 1 — Operator phone+OTP sign-up
FR2: Epic 5 — Staff invite acceptance via WhatsApp link + OTP
FR3: Epic 6 — Member sign-up via OTP after invitation link
FR4: Epic 1 — Stay-logged-in toggle for any authenticated user
FR5: Epic 10 — Super admin email + password authentication
FR6: Epic 1 — RBAC enforcement across all four roles via middleware
FR7: Epic 1 — Business registration (type + name) in onboarding wizard
FR8: Epic 1 — Solo vs. staff selection during onboarding
FR9: Epic 1 — System skips staff + QR steps for solo operators
FR10: Epic 1 — Onboarding wizard guides operator to first value in one session
FR11: Epic 2 — Default plan templates based on business type
FR12: Epic 2 — Add member (name + phone)
FR13: Epic 2 — Edit member details
FR14: Epic 2 — Archive member
FR15: Epic 2 — Search members by partial name or phone
FR16: Epic 2 — Member status display (active / expired / expiring soon)
FR17: Epic 2 — Create membership plans (daily / weekly / monthly)
FR18: Epic 2 — Assign plan to member
FR19: Epic 2 — Auto-calculate expiry from plan duration + start date
FR20: Epic 2 — Start date defaults to today; override for backdating
FR21: Epic 2 — Daily memberships auto-expire at end of day (cron)
FR22: Epic 3 — Record payment (amount, method, optional note)
FR23: Epic 3 — Record staff member who processed each payment
FR24: Epic 3 — Payment recording auto-renews membership + updates expiry
FR25: Epic 3 — Walk-in: combined payment + check-in in one action
FR26: Epic 3 — Auto WhatsApp receipt on payment recording
FR27: Epic 3 — Payments void-only with reason; no deletion
FR28: Epic 4 — Member checks in via gym static QR (URL deep-link, native camera)
FR29: Epic 4 — System validates active membership on QR scan; rejects expired
FR30: Epic 4 — Manual check-in by staff (search + confirm)
FR31: Epic 8 — Retroactive missed check-in logging
FR32: Epic 4 — Check-in record: timestamp, method, staff ID
FR33: Epic 4 — Generate unique static QR code per business location
FR34: Epic 3 — WhatsApp payment receipt via pre-approved template
FR35: Epic 6 — WhatsApp welcome message + app install link on new member add
FR36: Epic 7 — WhatsApp expiry reminder (default: 5 days before)
FR37: Epic 4 — WhatsApp check-in confirmation on successful check-in
FR38: Epic 5 — WhatsApp staff invitation with onboarding link
FR39: Epic 1 — WhatsApp OTP for authentication (SMS fallback)
FR40: Epic 6 — Member opts out of business-promotional messages per gym
FR41: Epic 6 — Transactional messages always delivered; cannot be opted out
FR42: Epic 6 — System distinguishes transactional vs. promotional messages
FR43: Epic 6 — Member views membership status, plan, and expiry date
FR44: Epic 6 — Member views payment history
FR45: Epic 6 — Member views check-in history
FR46: Epic 6 — Member accesses QR scanner within 2 taps of opening app
FR47: Epic 5 — Owner adds staff (phone + role)
FR48: Epic 5 — Owner removes staff access
FR49: Epic 5 — Staff permissions scoped to: members, payments, manual check-in, limited dashboard
FR50: Epic 7 — Owner views count of active members
FR51: Epic 7 — Owner views payments recorded today
FR52: Epic 7 — Owner views recent check-ins
FR53: Epic 7 — Owner views upcoming expiry alerts
FR54: Epic 5 — Staff limited dashboard view (check-ins + payments only)
FR55: Epic 9 — Export member list as CSV
FR56: Epic 9 — Export payment records as CSV
FR57: Epic 9 — Export attendance records as CSV
FR58: Epic 8 — Configure business type and terminology
FR59: Epic 8 — Manage / regenerate check-in QR code
FR60: Epic 8 — Share WhatsApp invite message to refer other gym owners
FR61: Epic 10 — Super admin views all tenants with trial/activation status
FR62: Epic 10 — Super admin views activation funnel per tenant
FR63: Epic 10 — Super admin sends one-tap WhatsApp nudge to stalled trials
FR64: Epic 10 — Super admin adds notes per tenant
FR65: Epic 10 — Super admin views platform-wide metrics
FR66: Epic 11 — System queues writes locally when offline
FR67: Epic 11 — System syncs queued writes on reconnect
FR68: Epic 11 — System displays sync status (synced / pending / failed)
FR69: Epic 11 — System notifies user explicitly on sync failure

## Epic List

### Epic 1: Authentication & Business Setup
Operators sign up with phone + WhatsApp OTP, step through the onboarding wizard, and land on a working owner home screen. RBAC guards all routes from day one. Includes full project bootstrapping and infrastructure setup.
**Priority:** P0
**FRs covered:** FR1, FR4, FR6, FR7, FR8, FR9, FR10, FR39
**Architecture:** Project bootstrapping (create-next-app + shadcn + Prisma + Serwist + testing tools), Neon PostgreSQL provisioning, Prisma schema v1 (all models), Sentry v10 + Vercel Analytics, GitHub Actions CI pipeline, JWT + httpOnly cookies, Upstash Redis OTP rate-limiting, auth middleware chain, route group layouts (owner/staff/member/admin)

### Epic 2: Member Management & Membership Plans
Operators add and manage members, create plans (daily/weekly/monthly) with auto-calculated expiry, assign plans, and search/view member status.
**Priority:** P0
**FRs covered:** FR11, FR12, FR13, FR14, FR15, FR16, FR17, FR18, FR19, FR20, FR21

### Epic 3: Payment Recording & WhatsApp Receipts
Staff record a payment in ≤3 taps, membership auto-renews, and a WhatsApp receipt fires to the member within 60 seconds — the core product differentiation moment.
**Priority:** P0
**FRs covered:** FR22, FR23, FR24, FR25, FR26, FR27, FR34
**Architecture:** WhatsApp outbox pattern (whatsapp_jobs table + Vercel Cron every 1 min), Termii BSP client + 6 pre-approved templates

### Epic 4: QR Check-In & Attendance Tracking
Operators generate a gym QR code; members check in by scanning it via native camera (URL deep-link); staff can manually check in. All attendance logged with timestamps and WhatsApp confirmation.
**Priority:** P0
**FRs covered:** FR28, FR29, FR30, FR32, FR33, FR37
**Architecture:** qr-validate API route, daily membership expiry cron (/api/cron/process-memberships, midnight WAT)

### Epic 5: Staff Management & Shift Operations
Owners invite staff via WhatsApp; staff access a dedicated shift screen built for high-speed daily ops (recents + 3 actions + today counter); owners manage staff access.
**Priority:** P1
**FRs covered:** FR2, FR38, FR47, FR48, FR49, FR54
**Architecture:** Staff invite acceptance route (/api/staff/invite/[token]), stay-logged-in for shared devices

### Epic 6: Member Portal & Notification Preferences
Members access their membership status, payment history, check-in history, and QR scanner. They receive a welcome WhatsApp on joining and control promotional notifications per gym.
**Priority:** P1
**FRs covered:** FR3, FR35, FR40, FR41, FR42, FR43, FR44, FR45, FR46

### Epic 7: Owner Dashboard & Automated Notifications
Owners see live business metrics (active members, today's payments, check-ins, expiry alerts). WhatsApp expiry reminders fire automatically via the daily cron.
**Priority:** P1
**FRs covered:** FR36, FR50, FR51, FR52, FR53

### Epic 8: Business Settings, Retroactive Ops & GTM
Operators configure business settings, manage QR codes, retroactively log missed check-ins, and share FitBase via WhatsApp with other gym owners.
**Priority:** P2
**FRs covered:** FR31, FR58, FR59, FR60

### Epic 9: Data Export & Compliance
Operators export member lists, payment records, and attendance data as CSV for external reporting and NDPR compliance.
**Priority:** P2
**FRs covered:** FR55, FR56, FR57

### Epic 10: Super Admin & Platform Operations
The platform super admin monitors all tenant trials, tracks activation funnels, nudges stalled businesses via WhatsApp, and views platform-wide metrics.
**Priority:** P2
**FRs covered:** FR5, FR61, FR62, FR63, FR64, FR65
**Architecture:** Super admin email+password auth route (/api/auth/admin-login, bcrypt)

### Epic 11: Offline-First Sync
All core operations function without internet. Writes queue in IndexedDB, sync on reconnect via service worker, and sync state is always visible. No silent failures.
**Priority:** P2
**FRs covered:** FR66, FR67, FR68, FR69
**Architecture:** IndexedDB FIFO write queue; idempotency keys already built in from Epics 3 & 4; Serwist service worker already initialized in Epic 1

---

## Epic 1: Authentication & Business Setup

Owner operators sign up with phone + WhatsApp OTP, step through the onboarding wizard, and land on a working owner home screen. RBAC guards all routes from day one. Includes full project bootstrapping and all auth infrastructure.

### Story 1.1: Project Bootstrap & Deployable Foundation

As a developer,
I want the Next.js application bootstrapped with all required dependencies, database connection, CI pipeline, and monitoring configured,
So that every subsequent story has a working, tested, and deployable foundation to build upon.

**Acceptance Criteria:**

**Given** the project root directory exists
**When** the bootstrap sequence runs (create-next-app, shadcn init, Prisma init, Serwist, Sentry, Jest + Playwright)
**Then** the app starts on localhost:3000 with no errors
**And** TypeScript strict mode is enabled with zero type errors
**And** Prisma connects to Neon using DATABASE_URL with pooled connection
**And** GitHub Actions CI passes: typecheck → lint → build
**And** Sentry is configured and captures a test error in development
**And** initial Prisma schema defines: `User`, `Business`, `OtpRequest` models with correct types and relations
**And** all required env vars are documented in `.env.example` with no secrets committed

---

### Story 1.2: Phone Number Entry & WhatsApp OTP

As a business operator or returning user,
I want to enter my phone number and receive a one-time passcode via WhatsApp,
So that I can sign in securely without creating a password.

**Acceptance Criteria:**

**Given** I am on the /login screen
**When** I enter a valid phone number and tap "Send OTP"
**Then** Termii sends a 6-digit OTP to my WhatsApp (SMS fallback if WhatsApp fails)
**And** the OTP is stored as a single-use `OtpRequest` record with a 10-minute expiry
**And** the UI transitions to the OTP entry screen without a full-page reload

**Given** I have requested OTP more than 5 times in one hour for the same number
**When** I tap "Send OTP" again
**Then** the request is rejected with a clear rate-limit message via Upstash Redis
**And** I am told when I can try again

**Given** I tap "Resend OTP"
**When** the new OTP is sent
**Then** the previous OTP is invalidated
**And** the resend button is disabled for 60 seconds after tapping

---

### Story 1.3: OTP Verification & JWT Session

As an authenticated user,
I want my OTP verified and a secure session established,
So that I am logged in and routed to the correct home screen for my role.

**Acceptance Criteria:**

**Given** I enter the correct 6-digit OTP within its 10-minute window
**When** I confirm
**Then** JWT access token (15-min) and refresh token (7-day) are set as httpOnly, Secure, SameSite=Strict cookies
**And** I am routed to my role's home screen: Owner → /dashboard, Staff → /shift, Member → /member
**And** the `OtpRequest` record is marked used and cannot be reused

**Given** I toggle "Stay logged in" before confirming OTP
**When** OTP is verified
**Then** refresh token expiry extends to 30 days

**Given** I enter an incorrect OTP
**When** I tap "Verify"
**Then** an inline error shows "Incorrect code — X attempts remaining"
**And** after 5 incorrect attempts the OTP is locked

**Given** I enter an expired OTP (>10 minutes)
**When** I tap "Verify"
**Then** I see "Code expired" with a "Resend" CTA

**Given** I am already authenticated and navigate to /login
**When** the page loads
**Then** I am redirected to my role's home screen

---

### Story 1.4: Business Registration Wizard

As a new business operator,
I want to register my business type, name, and operating model through a guided wizard,
So that FitBase is correctly configured for my operation with no irrelevant steps shown.

**Acceptance Criteria:**

**Given** I have verified OTP for the first time with no existing Business record
**When** the app detects no business
**Then** I am routed to the onboarding wizard at /onboarding

**Given** I am on the business type step
**When** I select my type (Gym / Yoga Studio / Martial Arts / Spa / Personal Trainer)
**Then** I advance to the business name step
**And** app terminology updates to match (e.g., "Client" for Personal Trainer)

**Given** I enter my business name and tap Continue
**When** the form submits
**Then** a `Business` record is created with name, type, and my userId as ownerId
**And** I advance to the solo/staff question

**Given** I select "Just me"
**When** I advance
**Then** staff setup and QR generation are excluded from the remaining wizard steps
**And** `Business.soloOperator` is set to true

**Given** I select "I have staff"
**When** I advance
**Then** a staff setup prompt is queued for the owner dashboard (non-blocking)

**Given** I navigate directly to /dashboard without completing the wizard
**When** the owner layout checks wizard completion
**Then** I am redirected to /onboarding

---

## Epic 2: Member Management & Membership Plans

Operators add and manage members, create plans with auto-calculated expiry, assign plans, and search/view member status.

### Story 2.1: Create & List Membership Plans

As a business operator,
I want to create membership plans with a name, price, and duration type,
So that I have reusable plans to assign to members with consistent pricing.

**Acceptance Criteria:**

**Given** I tap "Add Plan" and fill in name, price, and duration type (Daily / Weekly / Monthly)
**When** I confirm
**Then** a `MembershipPlan` record is created with price stored as an integer in kobo
**And** the plan appears in my plan list immediately

**Given** my business type was set during onboarding
**When** I open Plans for the first time
**Then** default plan templates are pre-populated based on my business type
**And** I can edit or delete the defaults before using them

**Given** I enter a price
**When** I type in the price field
**Then** the field uses `inputmode="numeric"` and ₦35,000 is stored as `3500000` kobo (never a float)

---

### Story 2.2: Add Members & Member List

As a business operator or staff,
I want to add new members and search the member list by name or phone,
So that every client has a record and can be found in under 3 seconds.

**Acceptance Criteria:**

**Given** I tap "Add Member" and enter a name and phone number
**When** I confirm
**Then** a `Member` record is created scoped to my `businessId` (from JWT, never request body)
**And** phone is stored in E.164 format (+2348012345678)
**And** the member appears in the list immediately

**Given** a phone number already exists in my gym
**When** I try to add a duplicate
**Then** I see "This number is already registered — [view member]" inline error and no duplicate is created

**Given** I type 2+ characters in the search field
**When** I pause (200ms debounce)
**Then** results update with members matching name or phone within 300ms (DB indexes on businessId+name and businessId+phone)

**Given** no members match my search
**When** results load
**Then** I see "No members found. Add [term] as a new member?" with "Add Member" CTA

---

### Story 2.3: Assign Plan to Member with Auto-Expiry

As a business operator,
I want to assign a membership plan to a member with an auto-calculated expiry date,
So that the membership period is tracked accurately without manual date entry.

**Acceptance Criteria:**

**Given** I select a plan for a member with today as start date (default)
**When** I confirm
**Then** a `Membership` record is created and expiry auto-calculated: Daily → end of today, Weekly → start + 7 days, Monthly → start + 30 days
**And** member status updates to "Active" immediately

**Given** I override the start date to a past date (backdating)
**When** I confirm
**Then** expiry recalculates correctly from the overridden start date

**Given** the member already has an active membership
**When** I assign a new plan
**Then** a confirmation dialog warns me before replacing it

---

### Story 2.4: Member Profile, Status Display & Management

As a business operator or staff,
I want to view a member's profile with live status, edit their details, archive them, and have daily memberships auto-expire at end of day,
So that member records are always accurate and staff always know who is active.

**Acceptance Criteria:**

**Given** I open a member's profile
**When** it loads
**Then** I see name, phone, plan, expiry date, and status badge (Active / Expiring Soon ≤7 days / Expired)
**And** status is shown via colour + text + icon (never colour alone)

**Given** I edit a member's name or phone and save
**When** the update completes
**Then** the `Member` record is updated with phone in E.164 format

**Given** I archive a member and confirm the dialog
**When** the action completes
**Then** `Member.archivedAt` is set (no hard delete — NDPR)
**And** historical payments and check-ins are preserved
**And** the member no longer appears in the active list

**Given** a member has a Daily membership
**When** the `/api/cron/process-memberships` job runs at midnight WAT
**Then** all Daily memberships whose expiry is today are marked Expired
**And** the cron endpoint requires the Vercel Cron secret header

---

## Epic 3: Payment Recording & WhatsApp Receipts

Staff record a payment in ≤3 taps, membership auto-renews, and a WhatsApp receipt fires to the member within 60 seconds — the core product differentiation moment.

### Story 3.1: Record Payment (≤3-Tap Flow)

As a business operator or staff,
I want to record a member's payment in ≤3 taps with membership auto-renewal,
So that the member's record is updated and I never need to manually follow up.

**Acceptance Criteria:**

**Given** I tap "Record Payment" from a member's profile (tap 1)
**When** the payment drawer slides up
**Then** the member is pre-selected, the plan amount is pre-filled in kobo, and Cash/Bank Transfer toggle is shown

**Given** I confirm the payment details and tap "Record Payment" (tap 3)
**When** the mutation completes
**Then** a `Payment` record is created with amount, method, staffId, memberId, businessId, and idempotencyKey
**And** the `Membership` expiry date is updated in the same Prisma transaction
**And** a `WhatsappJob` record of type RECEIPT is inserted in the same transaction
**And** the full-screen `PaymentSuccessScreen` is shown with member name, amount, new expiry, and "Receipt sent ✓"

**Given** I add an optional note before confirming
**When** the payment saves
**Then** the note is stored on the Payment record

**Given** I submit the same payment twice (network retry or double-tap)
**When** the second request arrives with the same idempotencyKey
**Then** the original response is returned and no duplicate Payment is created

---

### Story 3.2: Payment Void & Audit Trail

As a business operator,
I want to void an incorrect payment with a reason,
So that the audit trail is preserved and financial records remain trustworthy.

**Acceptance Criteria:**

**Given** I view a payment record and tap "Void Payment"
**When** I enter a reason and confirm the dialog
**Then** `Payment.voidedAt` and `Payment.voidReason` are set (no deletion)
**And** the membership expiry is recalculated to reflect the void
**And** the voided payment is visually marked in payment history with the reason shown

**Given** I attempt to void a payment without entering a reason
**When** I tap confirm
**Then** the form shows an inline validation error and submission is blocked

---

### Story 3.3: WhatsApp Outbox Worker & Receipt Delivery

As a member,
I want to receive a WhatsApp receipt within 60 seconds of a payment being recorded,
So that I have instant, automatic proof of my payment without waiting for manual messages.

**Acceptance Criteria:**

**Given** a `WhatsappJob` of type RECEIPT exists with status "pending"
**When** the Vercel Cron job (`/api/cron/send-whatsapp`) runs (every 1 minute)
**Then** the job calls Termii with the pre-approved receipt template
**And** on success, `WhatsappJob.status` is updated to "sent" and `sentAt` is set
**And** on Termii failure, `retryCount` increments; after 3 failures, status is set to "failed"

**Given** the Termii API is unavailable
**When** the cron processes a pending job
**Then** the job retries with exponential backoff (max 3 attempts)
**And** failed jobs after max retries surface as "failed" (visible to Super Admin in Epic 10)

**Given** a payment is recorded while offline (Epic 11)
**When** the payment syncs to the server
**Then** a WhatsappJob is created and processed on the next cron tick

---

## Epic 4: QR Check-In & Attendance Tracking

Operators generate a gym QR code; members check in by scanning it via native camera (URL deep-link); staff can manually check in. All attendance is logged with timestamps.

### Story 4.1: Generate Gym QR Code

As a business operator,
I want to generate a unique static QR code for my gym,
So that members can use it to check themselves in without staff involvement.

**Acceptance Criteria:**

**Given** I am in Business Settings or completing the onboarding wizard
**When** I tap "Generate QR"
**Then** a unique token is generated and stored on the `Business` record
**And** a QR code image is displayed encoding `{APP_URL}/checkin/{businessId}?token={qrToken}`
**And** I can download or share the QR image

**Given** I tap "Regenerate QR" (if QR is compromised)
**When** I confirm the dialog
**Then** a new token is generated, the old token is invalidated, and old QR codes no longer work

---

### Story 4.2: Member QR Scan Check-In

As a member,
I want to check in by pointing my phone's native camera at the gym QR poster,
So that I am checked in in under 2 seconds without needing to open the app first.

**Acceptance Criteria:**

**Given** the gym has a QR code displayed at the entrance
**When** I scan it with my phone's native camera
**Then** my device opens `{APP_URL}/checkin/{businessId}?token={qrToken}` in the browser
**And** if I am authenticated, my membership is validated and a `CheckIn` record is created
**And** a `WhatsappJob` of type CHECKIN_CONFIRM is inserted in the same transaction
**And** I see a full-screen success confirmation

**Given** my membership is expired
**When** the `/api/checkins/qr-validate` endpoint processes my scan
**Then** I receive a 403 with a clear message: "Your membership expired on [date]. Please speak to the front desk to renew."
**And** no CheckIn record is created

**Given** I am not authenticated when I scan the QR
**When** the deep-link opens
**Then** I am routed to /login with the check-in URL preserved as a return URL
**And** after OTP verification I am redirected back to complete the check-in

**Given** a QR token is invalid or belongs to a different business
**When** the endpoint validates it
**Then** I see "Invalid QR code. Please scan the correct gym QR."

---

### Story 4.3: Manual Staff Check-In

As a business operator or staff,
I want to manually check in a member by searching and confirming,
So that members without the app or in poor-signal environments can still be checked in.

**Acceptance Criteria:**

**Given** I search for a member from the check-in screen
**When** I select a member and tap "Check In"
**Then** a `CheckIn` record is created with method "manual", staffId, businessId, and timestamp
**And** a `WhatsappJob` of type CHECKIN_CONFIRM is queued

**Given** the member's membership is expired
**When** I attempt to check them in manually
**Then** a warning is shown: "Membership expired — check in anyway?" with Confirm / Cancel
**And** if confirmed, the check-in is recorded with an "expired_override" flag

---

## Epic 5: Staff Management & Shift Operations

Owners invite staff via WhatsApp; staff access a dedicated shift screen for high-speed daily ops; owners manage staff access.

### Story 5.1: Invite & Onboard Staff Members

As a business operator,
I want to invite a staff member by entering their phone number,
So that they receive a WhatsApp invitation link and can set up their access immediately.

**Acceptance Criteria:**

**Given** I enter a staff member's phone number and tap "Send Invite"
**When** the invitation is created
**Then** a `StaffInvite` record is created with a unique token and 48-hour expiry
**And** a `WhatsappJob` of type STAFF_INVITE is queued with the onboarding link
**And** the staff member appears in my staff list as "Invited (pending)"

**Given** the staff member opens the WhatsApp invite link
**When** they complete OTP verification at `/staff-invite/{token}`
**Then** their `User` record is created/linked with role Staff and my businessId
**And** the `StaffInvite` token is consumed and cannot be reused
**And** they are routed to the staff shift screen

**Given** an invite token has expired (>48 hours)
**When** the staff member opens the link
**Then** they see "This invitation has expired. Ask your manager to resend it."

---

### Story 5.2: Staff Shift Screen

As a staff member,
I want a dedicated shift screen with recents and 3 primary actions,
So that I can complete any daily operation in the fewest possible taps without navigating menus.

**Acceptance Criteria:**

**Given** I log in as Staff
**When** the app loads
**Then** I see the `ShiftScreen`: business name + sync indicator at top, today's check-in counter, 3 full-width action buttons (Record Payment / Check In Member / Find Member), and last 5 recent members
**And** no bottom tab bar is shown (shift screen is my only home)

**Given** I tap a member from the recents list
**When** their profile loads
**Then** I can see their status and take action immediately (Record Payment / Check In)

**Given** today is my first shift (no recent members)
**When** the shift screen loads
**Then** the recents section shows: "No recent activity. Search for a member to begin." with search focused

---

### Story 5.3: Staff Access Management

As a business operator,
I want to view my staff list and remove a staff member's access,
So that I control who can operate my gym's FitBase account at any time.

**Acceptance Criteria:**

**Given** I view my staff list
**When** it loads
**Then** I see each staff member with their name, phone, status (Active / Invited), and date added

**Given** I tap "Remove Access" for a staff member and confirm
**When** the action completes
**Then** their `User.businessId` is disassociated and role is cleared
**And** their active session is invalidated (refresh token revoked)
**And** they are removed from the staff list immediately

**Given** I have only one staff member (myself as owner)
**When** I attempt to remove access
**Then** the action is blocked: "You cannot remove yourself"

---

## Epic 6: Member Portal & Notification Preferences

Members access their membership status, payment history, check-in history, and QR scanner. They receive a welcome WhatsApp on joining and control notification preferences per gym.

### Story 6.1: Member Sign-Up & Portal Access

As a member,
I want to access my membership information via a PWA link sent to my WhatsApp,
So that I can see my gym records on my phone without asking anyone.

**Acceptance Criteria:**

**Given** an owner adds me as a new member
**When** my record is saved
**Then** a `WhatsappJob` of type WELCOME is queued with my name, plan details, and a PWA install link

**Given** I open the PWA link from WhatsApp
**When** I complete phone + OTP verification
**Then** a `User` record is created/linked with role Member and my businessId(s)
**And** I am routed to the member home screen showing my membership status

---

### Story 6.2: Membership Status, Payment History & Check-In History

As a member,
I want to view my current membership status, all payments I've made, and my check-in history,
So that I have full visibility of my gym records without needing to ask staff.

**Acceptance Criteria:**

**Given** I open the member app
**When** the home screen loads
**Then** I see the `MemberStatusHero`: full-bleed colour header (green/amber/red by status), gym name, my name, status badge, plan name, and expiry date
**And** status is Active (green), Expiring Soon (amber ≤7 days), or Expired (red)

**Given** I tap the Payments tab
**When** the history loads
**Then** I see all my payments in reverse chronological order with amount, date, method, and plan

**Given** I tap the History tab
**When** it loads
**Then** I see all my check-ins with date, time, and method (QR / manual)

---

### Story 6.3: Member QR Scanner (2-Tap Check-In)

As a member,
I want to access a QR scanner within 2 taps of opening the app,
So that I can check in at the gym entrance quickly without staff involvement.

**Acceptance Criteria:**

**Given** I am on the member home screen
**When** I tap "Check In" (tap 1) and the camera opens (tap 2)
**Then** I can scan the gym's QR code and am checked in automatically
**And** the full check-in flow completes in ≤2 seconds end-to-end

**Given** I deny camera permission
**When** the scanner tries to open
**Then** I see a prompt explaining why camera access is needed with a link to grant it in settings

---

### Story 6.4: Notification Preferences

As a member,
I want to opt out of promotional messages from a specific gym while keeping transactional messages,
So that I control my WhatsApp communications without losing important alerts.

**Acceptance Criteria:**

**Given** I open Settings in the member app
**When** I view notification preferences
**Then** I see a toggle per gym for "Promotional messages" (on by default)
**And** transactional messages (receipts, expiry warnings, welcome) are shown as always-on and cannot be toggled off

**Given** I toggle off Promotional messages for a gym
**When** the setting is saved
**Then** `MemberNotificationPreference.optOutPromotional` is set to true for that businessId
**And** the WhatsApp cron skips promotional jobs for me at this gym

---

## Epic 7: Owner Dashboard & Automated Notifications

Owners see live business metrics and WhatsApp expiry reminders fire automatically.

### Story 7.1: Owner Dashboard

As a business operator,
I want a dashboard showing my active members, today's payments, recent check-ins, and upcoming expiry alerts,
So that I can see the health of my gym in seconds.

**Acceptance Criteria:**

**Given** I open the owner dashboard
**When** it loads
**Then** I see 4 stat cards: Active Members count, Today's Payments total (₦), Today's Check-ins count, and Members Expiring Soon (≤7 days)
**And** a Recent Check-ins list with the last 10 entries
**And** an Expiry Alerts section listing members expiring in ≤7 days with their plan and expiry date

**Given** I have zero members
**When** the dashboard loads
**Then** each stat card shows "0" and an "Add your first member" prompt is shown

---

### Story 7.2: Automated Membership Expiry Reminders

As a member,
I want to receive a WhatsApp reminder before my membership expires,
So that I can renew before being turned away at the gym entrance.

**Acceptance Criteria:**

**Given** a member's membership expires in exactly 5 days
**When** the `/api/cron/process-memberships` runs at midnight WAT
**Then** a `WhatsappJob` of type EXPIRY_REMINDER is created for that member
**And** the job is processed on the next cron tick and a WhatsApp reminder is sent via Termii

**Given** a member has already received an expiry reminder for this membership cycle
**When** the cron runs again the next day
**Then** no duplicate reminder is sent (idempotency check on memberId + expiryDate)

**Given** a member has opted out of transactional messages
**When** the cron creates an expiry reminder
**Then** the job is still created and sent (expiry reminders are transactional — cannot be opted out per FR41)

---

## Epic 8: Business Settings, Retroactive Ops & GTM

Operators configure business settings, manage QR codes, retroactively log missed check-ins, and refer other gym owners.

### Story 8.1: Business Settings & QR Management

As a business operator,
I want to update my business type, terminology, and regenerate my QR code,
So that FitBase stays correctly configured as my business evolves.

**Acceptance Criteria:**

**Given** I open Business Settings
**When** I update my business type
**Then** terminology updates across the app immediately (e.g., "Member" → "Client")
**And** the `Business.type` field is updated

**Given** I tap "Regenerate QR" and confirm
**When** the action completes
**Then** a new QR token is generated, the old one is invalidated, and a new QR image is shown
**And** all previous QR scans with the old token return an "Invalid QR" error

---

### Story 8.2: Retroactive Check-In Logging

As a business operator or staff,
I want to retroactively log a missed check-in for a member,
So that attendance records reflect what actually happened even when the system wasn't used in the moment.

**Acceptance Criteria:**

**Given** I open a member's profile and tap "Log Missed Check-In"
**When** I select a past date and confirm
**Then** a `CheckIn` record is created with the chosen date, method "retroactive", and my staffId
**And** the record appears in the member's check-in history with a "retroactive" label

**Given** I select a date in the future
**When** I try to confirm
**Then** validation blocks submission: "Check-in date cannot be in the future"

---

### Story 8.3: Operator Referral Share

As a business operator,
I want to share a pre-written WhatsApp message about FitBase with other gym owners,
So that I can refer peers and help FitBase grow.

**Acceptance Criteria:**

**Given** I tap "Share FitBase" in my settings
**When** the share sheet opens
**Then** a pre-written WhatsApp message is composed with a referral link and my gym name as attribution
**And** the native share sheet opens so I can send it to any WhatsApp group or contact

---

## Epic 9: Data Export & Compliance

Operators export member, payment, and attendance data as CSV for external reporting and NDPR compliance.

### Story 9.1: CSV Data Export

As a business operator,
I want to export my member list, payment records, and attendance data as CSV files,
So that I can share records with accountants, maintain offline backups, and meet compliance requirements.

**Acceptance Criteria:**

**Given** I tap "Export Members" on the Export screen
**When** the download completes
**Then** a CSV is generated with all non-archived members: name, phone, plan, status, expiry, join date
**And** the file is named `fitbase-members-{businessName}-{date}.csv`

**Given** I tap "Export Payments"
**When** the download completes
**Then** a CSV contains all payment records: member name, amount (₦), method, date, staff, void status
**And** voided payments are included with their void reason

**Given** I tap "Export Attendance"
**When** the download completes
**Then** a CSV contains all check-in records: member name, date, time, method (QR/manual/retroactive)

**Given** I have no records of a given type
**When** I attempt to export
**Then** a CSV with just the header row is returned (not an error)

---

## Epic 10: Super Admin & Platform Operations

The platform super admin monitors all tenant businesses, tracks activation funnels, nudges stalled trials, and views platform metrics.

### Story 10.1: Super Admin Authentication

As the platform super admin,
I want to authenticate via email and password,
So that I can access the admin dashboard without using phone OTP.

**Acceptance Criteria:**

**Given** I navigate to /admin/login
**When** I enter the correct admin email and password
**Then** a JWT is issued with role SuperAdmin and I am routed to /admin
**And** the password is verified with bcrypt (no plaintext stored)

**Given** I enter incorrect credentials
**When** I submit
**Then** I see "Incorrect email or password" with no indication of which field is wrong

---

### Story 10.2: Tenant Dashboard & Activation Funnel

As the platform super admin,
I want to see all tenant businesses with their trial stage and activation funnel progress,
So that I can identify stalled trials and prioritise outreach.

**Acceptance Criteria:**

**Given** I open the admin dashboard
**When** it loads
**Then** I see all tenant businesses sorted by: stalled (oldest first), then partial, then activated
**And** each row shows: gym name, owner phone, sign-up date, and activation stage (1–5)

**Given** I view the activation funnel
**When** it renders
**Then** each stage shows the count and percentage of tenants at that stage:
  1. Signed up → 2. Business profile complete → 3. First member added → 4. First payment recorded → 5. QR generated

**Given** I view platform metrics
**When** the page loads
**Then** I see: total tenants, active trials, converted (paying), trial-to-paid conversion rate

---

### Story 10.3: WhatsApp Nudge & Tenant Notes

As the platform super admin,
I want to send a one-tap WhatsApp nudge to stalled trial businesses and add follow-up notes,
So that I can personally activate high-potential trials without leaving the dashboard.

**Acceptance Criteria:**

**Given** I tap "Send Nudge" for a stalled tenant
**When** I confirm
**Then** a `WhatsappJob` of type ADMIN_NUDGE is queued to the business owner's phone
**And** a log entry records that a nudge was sent with timestamp

**Given** I add a note on a tenant's detail page
**When** I save
**Then** a `TenantNote` record is created with my admin userId, content, and timestamp
**And** the note appears in the tenant's note history in reverse chronological order

---

## Epic 11: Offline-First Sync

All core operations function without internet. Writes queue in IndexedDB, sync on reconnect, and sync state is always visible.

### Story 11.1: Offline Write Queue (IndexedDB)

As a staff member or owner,
I want payment, check-in, and member writes to queue locally when I'm offline,
So that I never lose data during network interruptions and can keep working normally.

**Acceptance Criteria:**

**Given** I lose network connectivity
**When** I record a payment, check in a member, or add a member
**Then** the write is stored in IndexedDB with a FIFO queue structure
**And** the success screen shows "Receipt will send when back online" instead of "Receipt sent ✓"
**And** the `SyncIndicator` shows "1 pending" (amber)

**Given** I have 100 or more pending writes in the queue
**When** I attempt another offline write
**Then** I see a warning: "You have many unsynced records. Sync soon to avoid data loss."

**Given** my idempotencyKey is already set on Payment and CheckIn from Epics 3 & 4
**When** the offline queue retries a write on reconnect
**Then** duplicate submissions are safely rejected by the server via idempotency check

---

### Story 11.2: Sync-on-Reconnect & SyncIndicator UI

As a staff member or owner,
I want queued writes to sync automatically when I come back online and to always see my sync state,
So that I can trust that no data is lost and I know when everything is safe.

**Acceptance Criteria:**

**Given** I come back online after being offline
**When** connectivity is restored
**Then** the service worker triggers the sync queue to process in FIFO order
**And** each write is sent to the server and confirmed
**And** the `SyncIndicator` updates from "N pending" → "All synced" (green, fades after 3 seconds)

**Given** a sync write fails (server error)
**When** the failure occurs
**Then** the `SyncIndicator` shows "Sync failed" (red, tappable)
**And** tapping it shows which write failed with a "Retry" CTA
**And** the user is never left without knowing the state of their data

**Given** the `SyncIndicator` is in any state
**When** it renders
**Then** it uses `aria-live="polite"` and `role="status"` for screen reader accessibility
