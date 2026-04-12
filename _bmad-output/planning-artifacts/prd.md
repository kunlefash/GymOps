---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-12-complete]
inputDocuments:
  - docs/FitBase_Product_Brief.md
  - _bmad-output/planning-artifacts/product-brief-GymOps-2026-03-28.md
  - _bmad/_memory/project-context.md
workflowType: 'prd'
projectType: greenfield
classification:
  projectType: saas_b2b2c_pwa
  domain: fitness_wellness_operations
  complexity: medium-high
  projectContext: greenfield
visionInsights:
  differentiationMoment: First automatic WhatsApp receipt after logging a payment — zero manual effort, professional output, member gets proof instantly
  deeperProblem: Trust — members don't trust the gym has their records right, owners don't trust staff are recording correctly, staff don't trust their tools; FitBase becomes the shared source of truth
  whyNow: Nigeria fitness industry growing fast, high smartphone penetration, WhatsApp Business API widely accessible, no dominant local competitor
  coreVisionStatement: A Nigerian gym owner runs their entire operation — members, payments, attendance, communications — from a single app that works offline, costs less than foreign alternatives, and communicates via WhatsApp
---

# Product Requirements Document - FitBase

**Author:** Adekunle
**Date:** 2026-04-06

---

## Executive Summary

FitBase is a B2B2C SaaS Progressive Web App for Nigerian fitness and wellness operators — gyms, yoga studios, martial arts schools, spas, and personal trainers. It replaces WhatsApp group chats, exercise books, and Excel spreadsheets with a single offline-capable platform that manages members, records payments, tracks attendance, and delivers automated WhatsApp communications.

The product serves two user groups within a single PWA: **business operators and staff** managing day-to-day operations, and **members/clients** with self-service access to their own membership data. Both experiences ship in MVP.

The addressable market is 15,000–20,000 Nigerian fitness and wellness operators, the majority fully manual. No dominant local competitor exists. Global alternatives (Mindbody, Glofox) start at ~₦200,000/month and are internet-dependent — non-viable for this segment.

### What Makes This Special

FitBase's differentiation is **context-native design**: built from first principles for the Nigerian fitness market, not adapted from a foreign product.

**Four non-negotiable product principles:**
1. **Offline-first** — core operations function without internet; writes queue locally and sync server-authoritatively on reconnect
2. **WhatsApp-primary** — all member communications deliver via WhatsApp, the channel Nigerian members actually use
3. **Naira-denominated, locally priced** — subscription pricing in NGN at a fraction of global alternatives
4. **Trust as the product** — every transaction is timestamped, logged, and attributed to a staff member, creating a verifiable shared record

**Differentiation moment:** A gym owner logs a cash payment in 3 taps, a professional WhatsApp receipt reaches the member automatically, and the membership renews — replacing 5–10 minutes of manual WhatsApp back-and-forth and an Excel update.

**Core insight:** The real problem is not "no software" — it is the absence of a shared source of truth between operators, staff, and members.

**Why now:** Nigeria's fitness industry is growing fast; smartphone penetration makes PWA viable; WhatsApp Business API is widely accessible; the addressable market is uncontested.

## Project Classification

- **Project Type:** B2B2C SaaS — multi-tenant, role-based, subscription model, delivered as PWA
- **Domain:** Fitness & Wellness Operations (Nigeria-first)
- **Complexity:** Medium-High — offline-first sync, dual-role PWA, WhatsApp API, multi-vertical config, QR check-in
- **Project Context:** Greenfield — building from zero; existing codebase is a landing page placeholder
- **Multi-vertical:** Single data model with `businessType` configuration driving terminology — no vertical silos

---

## Success Criteria

### User Success

**Business Operator (Gym Owner/Manager)**
- Records first payment and WhatsApp receipt fires within first session (≤15 mins from sign-up)
- Zero manual WhatsApp messages needed to confirm a member payment
- Looks up any member's status, payment history, and attendance in under 10 seconds
- Full onboarding completed in a single session without support

**Staff**
- Records a payment in ≤3 taps
- Completes a manual check-in in ≤2 taps
- Zero unresolved "is my membership active?" queries during a shift

**Member/Client**
- Checks in by scanning gym QR without staff involvement
- Views membership status and payment history without contacting anyone
- Receives WhatsApp receipt within 60 seconds of payment recording
- Opts out of business-promotional messages per gym while retaining transactional messages

### Business Success

| Metric | Baseline | Stretch | Timeframe |
|---|---|---|---|
| Paying gym operators | 50 | 65 | Month 6 |
| MRR | ₦2,100,000 | ₦2,700,000 | Month 6 |
| Operator churn | <15% | <10% | Rolling 3-month |
| Free trial sign-ups | 200 | 260 | Month 6 (33/month from M2) |
| Trial → paid conversion | 25% | 40% | Rolling |
| Time-to-first-value | ≤15 mins | ≤10 mins | Sign-up → first payment recorded |

**Pricing:**
- Starter (≤30 members): ₦25,000/month | ₦250,000/year
- Growth (31–80 members): ₦45,000/month | ₦450,000/year
- Pro (80+ members): ₦70,000/month | ₦700,000/year
- Free trial: 14 days, no card required
- Tier upgrades: manual/honour-based for MVP
- All tiers: same features — differentiation by member count only for MVP

**Core pricing narrative:** *"FitBase costs less than one member's monthly fee. Prevent a single lapse and it pays for itself."*

**GTM dependency:** 200 trial sign-ups in 6 months requires active pre-launch pipeline — gym owner WhatsApp groups, Instagram fitness community, direct outreach. Pipeline must be warm before launch day.

### Technical Success

- **Data integrity:** Payment and membership writes never lost — server-authoritative sync queue, append-only, no silent failures
- **Zero undetected sync divergence:** Local state never silently diverges from server state without user notification
- **Offline reliability:** Core operations function fully without internet
- **Sync transparency:** Sync failures surface explicitly in UI
- **PWA performance:** ≤3 seconds to functional state on mid-range Android on 3G
- **WhatsApp delivery:** Transactional messages deliver within 60 seconds of trigger
- **Uptime:** ≥99.5% for API and sync endpoints

### Notification Model

- **Transactional (always-on, cannot opt out):** Payment receipts, membership expiry warnings, welcome messages — FitBase system-triggered
- **Business promotional (member can opt out per gym):** Class announcements, special offers, custom messages — business-triggered

### Measurable Outcomes

- 50 paying gyms by month 6 generating ₦2.1M MRR
- ≥80% of onboarded gyms record first payment within 24 hours of sign-up
- ≥60% of active gym members have PWA installed within 60 days of gym onboarding
- ≤15% operator churn at 3-month rolling window
- Zero payment records lost due to sync failures
- Zero instances of undetected sync divergence

---

## User Journeys

### Journey 1: Tunde — Gym Owner, First-Run Onboarding (Success Path)

**Who he is:** Tunde, 34, owns IronCut Fitness on Lagos Mainland. 80 members, 2 staff. Runs everything on WhatsApp and Excel. Lost ₦105,000 last month to three members whose memberships expired silently.

**Opening scene:** Tunde sees a FitBase post in a Lagos gym owners WhatsApp group. Someone says *"I stopped chasing members for payment confirmation."* He clicks the link at 9pm after closing time.

**Rising action:**
- Phone number → WhatsApp OTP → in. 8 seconds.
- Onboarding wizard: selects Gym → terminology sets. "I have staff" → staff setup queued. Business name: IronCut Fitness. 90 seconds.
- Creates three plans: Walk-in ₦5,000 (daily), Weekly ₦15,000, Monthly ₦35,000.
- Adds first member: Emeka, phone number. Assigns Monthly plan. Start date auto-fills today, expiry auto-calculates 29 April 2026. No manual date entry.
- Records Emeka's payment: ₦35,000, cash. 3 taps.
- **Climax:** Emeka gets a WhatsApp instantly: *"Hi Emeka! Your membership at IronCut Fitness has been activated. Plan: Monthly (₦35,000). Valid until: 29 April 2026. — Powered by FitBase."*
- Generates check-in QR. One tap. Total time: 11 minutes.

**Resolution:** Tunde adds 4 more members before bed. Cancels his Excel reminder for tomorrow morning.

**Requirements revealed:** Onboarding wizard (P0), businessType config, plan creation (daily/weekly/monthly), auto expiry calc, payment recording ≤3 taps, auto WhatsApp receipt, QR generation, solo vs staff branching.

---

### Journey 2: Amaka — Front Desk Staff, Daily Operations

**Who she is:** Amaka, 26, front desk at a Lekki yoga studio. 30–40 check-ins on busy days. Writes names in a register, manually WhatsApps receipts. Gets blamed when records don't match.

**Opening scene:** Studio owner invites her via WhatsApp link. OTP. Sets up in 90 seconds.

**Rising action:**
- Staff dashboard: three actions — **Record Payment**, **Check In Member**, **Find Member**.
- Client Fatima walks in. Search "Fat" → found. Active, 18 days remaining. QR scan → checked in. WhatsApp confirms.
- Client Bola: no app. Manual check-in. 4 seconds.
- Client Kemi: expired. Pays ₦35,000 cash → Record Payment → receipt fires → membership renewed → checked in.
- Walk-in: searches by phone "0812..." → one result. No ambiguity.
- **Climax:** 7:30am. 22 check-ins. Zero register entries. Zero manual WhatsApps.

**Resolution:** A client calls asking about expiry. Amaka finds them in 3 seconds by phone number. First time she hasn't said *"let me check with the owner."*

**Requirements revealed:** Staff dashboard, member search by name or phone, membership status display, QR scan + manual check-in, payment + auto-renewal, stay-logged-in toggle.

---

### Journey 3: Chidi — Gym Member, Self-Service Check-In

**Who he is:** Chidi, 28, tech worker, pays ₦35,000/month. Wrongly told his membership expired twice due to poor record-keeping.

**Opening scene:** WhatsApp from his gym: *"Your membership is active until 15 April 2026. Download FitBase: [link]"*

**Rising action:**
- PWA installs in one tap. Phone → OTP → in.
- Home screen: name, status (green: Active), plan (Monthly), expiry (15 April 2026). First time he's seen his gym data on his phone.
- QR poster at entrance. 2 taps → scanner → scans.
- **Climax:** Check-in confirmed. WhatsApp: *"Checked in at PumpHouse Gym — 6:47am. 14 days remaining."* 8 seconds door-to-gym-floor.
- Expiry reminder 5 days before. Pays cash. App updates. Receipt fires.

**Resolution:** Never wrongly turned away again. Tells a friend: *"Tell your gym to get on this."*

**Requirements revealed:** PWA install, membership status home screen, QR scanner ≤2 taps, expiry reminders, notification preferences.

---

### Journey 4: Edge Cases — Lapsed Member and New Member

**Lapsed Member — Kunle:** Expired 3 days ago. Scans gym QR. App: *"Your membership expired on 26 March 2026. Please speak to the front desk to renew."* Pays. Renewed. Proceeds.

**New Member — Ngozi:** Joins today. Owner adds her, records payment. WhatsApp receipt + app install link fires. No app yet — owner manually checks her in. She installs on the way to the gym floor.

**Requirements revealed:** Expired state in QR flow, manual check-in as first-class flow, welcome WhatsApp with app install link.

---

### Journey 5: Super Admin — High-Touch Trial Monitoring

**Who:** Adekunle (FitBase founder), monitoring first 50 trials personally.

**Flow:** Monday morning. Dashboard: 3 new sign-ups. CrossFit box: stalled (0 activity). Yoga studio: activated (12 members, 3 payments, QR done). Martial arts: partial (2 members, no payment).

One-tap WhatsApp nudge to stalled gyms. CrossFit owner replies, activates that afternoon. Pattern discovered: gyms that don't add a member within 48 hours churn at 70%.

**Requirements revealed:** Super admin dashboard, activation funnel tracking, WhatsApp nudge, tenant notes.

---

### Journey 6: Biodun — Solo Personal Trainer

**Who:** Biodun, 22 clients, trains at clients' homes. No staff, no physical location.

**Flow:** Onboarding: "Just me" → staff setup skipped. "No physical location" → QR skipped. 4 steps to member management. Adds clients, records payments, sends WhatsApp receipts.

**Requirements revealed:** Solo operator detection (skip staff + QR), session-based manual check-in, personal trainer as first-class path.

---

### Journey Requirements Summary

| Journey | Core Capabilities |
|---|---|
| Gym Owner Onboarding | Wizard (P0), businessType config, plans (daily/weekly/monthly), auto expiry, payment recording, WhatsApp receipt, QR generation |
| Staff Daily Ops | Staff dashboard, search by name/phone, QR + manual check-in, payment + renewal, stay-logged-in |
| Member Self-Service | PWA install, membership status, QR scanner ≤2 taps, expiry reminders, notification preferences |
| Edge Cases | Expired state in QR, WhatsApp onboarding, retroactive check-in, walk-in payment+check-in |
| Super Admin | Trial list, activation funnel, WhatsApp nudge, tenant notes |
| Solo Operator | Onboarding branching, session-based manual check-in |

---

## Domain-Specific Requirements

### Data Privacy (Nigeria NDPR)

- Basic NDPR compliance for MVP: privacy notice on sign-up + internal data retention policy
- Member phone numbers, payment records, and attendance data are personal data under NDPR
- Consent captured at member registration via explicit consent notice
- Data retention: archive (not delete) churned members and closed tenants for audit trail
- Right to deletion: not required for MVP; architecture must not make it impossible later

### WhatsApp Business API Compliance

- **Hard launch dependency:** Meta Business verification + BSP onboarding (recommended: Termii)
- **Timeline:** 3–4 weeks from initiation — must start before development completes
- All automated messages use pre-approved WhatsApp templates — no free-form message customisation in MVP
- Six templates for MVP approval: OTP/login, payment receipt, welcome message, expiry reminder, staff invite, check-in confirmation
- Dedicated FitBase sender phone number required

### Financial Record Integrity

- Every payment record: amount, method, date, staff who recorded it, member it applies to
- No payment deletion — only voidable with a reason (audit trail preserved)
- Offline payment writes are append-only — no retroactive modification without audit entry
- All financial writes timestamped, logged, and attributed to staff

---

## SaaS B2B2C Technical Requirements

### Tenant Model

- Single PostgreSQL database with row-level tenant isolation via `business_id`
- All queries scoped by `business_id` — enforced at ORM/middleware layer, not per-query
- Strict isolation: gym A never sees gym B's data under any circumstance
- Super admin uses separate permission layer with explicit cross-tenant query capability
- Tenant data: business profile, members, staff, plans, payments, attendance, check-in QR config
- Tenant lifecycle: trial → active → suspended (non-payment) → archived (closed)

### RBAC Matrix

| Role | Scope | Key Permissions |
|---|---|---|
| **Super Admin** | Platform-wide | View all tenants, activation funnel, WhatsApp nudge, tenant notes, platform metrics |
| **Owner** | Single tenant | All business operations — settings, staff, members, payments, exports, QR, dashboard |
| **Staff** | Single tenant (limited) | Add/edit members, record payments, manual check-in, view limited dashboard |
| **Member** | Own data across gyms | View membership status, payment history, check-in history, self check-in, notification preferences |

- MVP: 4 roles, hard-coded permissions (no custom roles)
- Growth: configurable staff permissions per action

### Integration Requirements

| Integration | Type | Priority | Purpose |
|---|---|---|---|
| WhatsApp Business API (Termii BSP) | External API | P0 — launch blocker | All member comms: receipts, OTP, reminders, welcome |
| Service Worker + IndexedDB | Browser API | P0 — launch blocker | Offline-first data sync |
| Browser Camera (html5-qrcode) | Browser API | P0 | QR scanning for member check-in |
| Paystack | External API | Post-MVP | Payment gateway integration |

### Implementation Considerations

- **Authentication:** Phone + WhatsApp OTP (SMS fallback via Termii). No passwords in MVP. Stay-logged-in toggle for shared devices.
- **PWA:** Installable via Add to Home Screen on Android Chrome (primary). iOS Safari secondary.
- **Responsive design:** Mobile-first for all roles. Staff on phones, owner may use tablet/laptop.
- **API architecture:** RESTful with JWT auth tokens. Tenant scoping enforced at middleware.
- **Offline queue:** Append-only write queue in IndexedDB. Server-authoritative sync on reconnect. Explicit sync status in UI.

---

## Project Scoping & Phased Development

### MVP Strategy

**Approach:** Problem-solving MVP — the smallest product that replaces Excel + WhatsApp and delivers the auto WhatsApp receipt moment within 15 minutes.

**Resource:** Solo developer (Adekunle) + AI-assisted development (Claude Code with BMAD TDD workflow). No parallelisation — features ship sequentially by priority.

### MVP Build Order

| Priority | Feature | Rationale |
|---|---|---|
| P0 | Auth (phone + WhatsApp OTP via Termii) | Unlocks everything |
| P0 | Business setup + onboarding wizard | First-run value in ≤15 mins |
| P0 | Member management (add, edit, search by name/phone) | Core data |
| P0 | Membership plans (daily/weekly/monthly, auto-expiry) | Core business logic |
| P0 | Manual payment recording (≤3 taps) + WhatsApp receipt | Differentiation moment |
| P0 | QR check-in (member scans gym QR) + manual fallback | Core daily operation |
| P1 | Staff management + RBAC | Multi-user gyms |
| P1 | Member portal (status, history, QR scanner) | Member experience |
| P1 | Basic dashboard (active members, payments, check-ins) | Owner visibility |
| P1 | WhatsApp notifications (welcome, expiry reminder) | Retention + onboarding |
| P1 | Notification preferences (per-gym promotional opt-out) | Member control |
| P2 | Retroactive check-in | Edge case coverage |
| P2 | Walk-in combined payment+check-in flow | Convenience |
| P2 | Data export (CSV) | Trust + churn reduction |
| P2 | Share button (WhatsApp invite) | GTM lever |
| P2 | Super admin dashboard | Ops monitoring |
| P2 | Offline-first sync (service worker + IndexedDB) | Reliability |
| P2 | 14-day free trial + tier management | Commercials |

**Note on offline-first:** Marked P2 because building online-first then layering offline is safer for a solo dev. Ship online, validate, then add offline resilience.

### Post-MVP Roadmap

**Phase 2 — Growth:**
- Paystack payment gateway integration
- Rotating QR / staff scans member (Model 1 check-in)
- Automated expiry reminders with custom scheduling
- Multi-location support
- Advanced reporting and analytics
- Bulk member import (CSV)
- Custom WhatsApp message templates
- Referral tracking and rewards programme
- In-app subscription billing management
- PIN-based authentication for shared devices

**Phase 3 — Expansion:**
- Native mobile apps (iOS + Android)
- Paystack DVA per-business virtual accounts
- AI-powered attendance and retention insights
- Class/session scheduling
- Marketplace integrations (accounting, marketing tools)
- Pan-African expansion (Ghana, Kenya, South Africa)

### Risk Mitigation

**Technical Risks:**

| Risk | Severity | Mitigation |
|---|---|---|
| Offline-first sync complexity | High | Build online-first, add offline in P2; append-only queue; test sync scenarios explicitly |
| WhatsApp API setup delays | Medium | Start Meta verification immediately; Termii sandbox for dev; SMS fallback |
| PWA performance on low-end Android | Medium | ≤3s budget on 3G; test on Tecno/Infinix; lazy load non-critical routes |
| Solo dev burnout | Medium | Strict TDD; BMAD story-by-story execution; ship P0 first |

**Market Risks:**

| Risk | Severity | Mitigation |
|---|---|---|
| Gym owners don't trust "another app" | High | Free trial; value in ≤15 mins; WhatsApp receipt as tangible proof |
| Staff resistance | Medium | 3-action dashboard; WhatsApp invite onboarding; zero training |
| Low trial volume | Medium | Pre-launch pipeline: WhatsApp groups, Instagram, direct outreach |
| Members don't install PWA | Low | Value delivered via WhatsApp even without app |

**Resource Risks:**

| Risk | Severity | Mitigation |
|---|---|---|
| Solo dev — no parallelisation | High | Strict P0 → P1 → P2 order; AI-assisted TDD |
| Scope creep | Medium | PRD is the contract — defer to Growth |
| Meta verification delays | Medium | Start today; launch with SMS-only if delayed |

---

## Functional Requirements

### Authentication & Access

- FR1: Business operator can sign up with phone number and verify via WhatsApp OTP
- FR2: Staff member can accept an invitation and set up access via WhatsApp link + OTP
- FR3: Member can sign up and verify via WhatsApp OTP after receiving an invitation link
- FR4: Any authenticated user can stay logged in on a device to avoid repeated OTP entry
- FR5: Super admin can authenticate via email and password
- FR6: System enforces role-based access control across four roles: super admin, owner, staff, member

### Business Setup & Onboarding

- FR7: Business operator can register a new business by selecting business type and entering business name
- FR8: Business operator can indicate whether they operate solo or with staff during onboarding
- FR9: System skips staff setup and QR generation steps for solo operators
- FR10: Onboarding wizard guides operator through first member add, first payment, and QR generation in a single session
- FR11: System provides default membership plan templates based on business type

### Member Management

- FR12: Business operator or staff can add a new member with name and phone number
- FR13: Business operator or staff can edit member details
- FR14: Business operator or staff can archive a member
- FR15: Business operator or staff can search members by partial name or phone number
- FR16: System displays member status (active, expired, expiring soon) on member profile

### Membership Plans

- FR17: Business operator can create membership plans with name, price, and duration type (daily, weekly, monthly)
- FR18: Business operator can assign a plan to a member
- FR19: System auto-calculates membership expiry date from plan duration and start date
- FR20: Start date defaults to today with option to override for backdating
- FR21: Daily (walk-in) memberships auto-expire at end of day

### Payment Recording

- FR22: Business operator or staff can record a payment for a member specifying amount, payment method (cash/bank transfer), and optional note
- FR23: System records the staff member who processed each payment
- FR24: Payment recording automatically renews membership and updates expiry date
- FR25: Walk-in payment recording combines payment and check-in in a single action
- FR26: System sends automated WhatsApp receipt to member upon payment recording
- FR27: Payments cannot be deleted — only voided with a reason for audit trail

### Check-In

- FR28: Member can check in by scanning the gym's static QR code while logged into the app
- FR29: System validates member's active membership status on QR scan and rejects expired memberships with a clear message
- FR30: Business operator or staff can manually check in a member by searching and confirming
- FR31: Business operator or staff can retroactively log a missed check-in for a member
- FR32: System records check-in timestamp, method used (QR/manual), and staff ID for manual check-ins
- FR33: Business operator can generate a unique static QR code for their business location

### WhatsApp Communications

- FR34: System sends payment receipt via WhatsApp using pre-approved template upon payment recording
- FR35: System sends welcome message via WhatsApp with app install link when a new member is added
- FR36: System sends membership expiry reminder via WhatsApp at configurable days before expiry (default: 5 days)
- FR37: System sends check-in confirmation via WhatsApp upon successful check-in
- FR38: System sends staff invitation via WhatsApp with onboarding link when owner adds staff
- FR39: System sends OTP via WhatsApp for authentication (SMS fallback)

### Notification Preferences

- FR40: Member can opt out of business-promotional messages per gym
- FR41: Transactional messages (receipts, expiry warnings, welcome) are always delivered and cannot be opted out of
- FR42: System distinguishes between transactional (system-triggered) and promotional (business-triggered) messages

### Member Portal

- FR43: Member can view their membership status, plan, and expiry date
- FR44: Member can view their payment history
- FR45: Member can view their check-in history
- FR46: Member can access a QR scanner to scan a gym's check-in QR code within 2 taps of opening the app

### Staff Management

- FR47: Business operator can add staff members by entering phone number and assigning a role
- FR48: Business operator can remove staff access
- FR49: Staff permissions are limited to: add/edit members, record payments, manual check-in, view limited dashboard

### Business Dashboard

- FR50: Business operator can view count of active members
- FR51: Business operator can view payments recorded today
- FR52: Business operator can view recent check-ins
- FR53: Business operator can view upcoming membership expiry alerts
- FR54: Staff can view a limited version of the dashboard (check-ins and payments only)

### Data Export

- FR55: Business operator can export members list as CSV
- FR56: Business operator can export payment records as CSV
- FR57: Business operator can export attendance records as CSV

### Business Settings

- FR58: Business operator can configure business type and terminology
- FR59: Business operator can manage check-in QR code (regenerate if compromised)

### GTM & Sharing

- FR60: Business operator can share a pre-written WhatsApp invite message to refer other gym operators to FitBase

### Super Admin

- FR61: Super admin can view a list of all tenant businesses with trial/activation status
- FR62: Super admin can view activation funnel per tenant (signed up → member added → payment recorded → QR generated)
- FR63: Super admin can send a one-tap WhatsApp nudge to stalled trial businesses
- FR64: Super admin can add notes per tenant for follow-up tracking
- FR65: Super admin can view platform-wide metrics (total tenants, active trials, conversion rates)

### Offline Capability

- FR66: System queues payment, check-in, and member writes locally when offline
- FR67: System syncs queued writes to server when connectivity is restored
- FR68: System displays current sync status to the user (synced / pending / failed)
- FR69: System notifies the user explicitly if a sync operation fails

---

## Non-Functional Requirements

### Performance

- **PWA initial load:** ≤3 seconds to functional state on mid-range Android (Tecno/Infinix) over 3G
- **Subsequent loads:** ≤1 second from cached service worker
- **Payment recording:** ≤500ms from confirm tap to success confirmation
- **Member search:** Results within 300ms of typing (local search on cached data)
- **QR scan to check-in:** ≤2 seconds end-to-end
- **Concurrent users per tenant:** 5 simultaneous staff users without degradation

### Security

- **Data in transit:** HTTPS/TLS 1.2+ for all API communication
- **Data at rest:** Database encryption at rest via hosting provider
- **Auth tokens:** JWT with 15-min access / 7-day refresh; httpOnly cookies or secure storage
- **OTP:** Single-use, 10-minute expiry, rate-limited to 5 attempts per phone per hour
- **Tenant isolation:** All API queries scoped by `business_id` at middleware — no cross-tenant data
- **Payment audit trail:** Immutable records (append-only); void creates new audit entry
- **NDPR compliance:** Privacy notice at registration; data retention policy; personal data protected

### Scalability

- **Year 1:** Architecture supports 500 tenants × 500 members each (250,000 member records)
- **Database:** Single PostgreSQL instance for Year 1; schema supports future partitioning
- **API:** Stateless; horizontal scaling via Vercel serverless if needed
- **WhatsApp:** Termii handles rate limiting and queuing

### Integration

- **WhatsApp (Termii):** 99.9% availability (Termii SLA); degrade to SMS on failure; 60-second delivery target; 6 pre-approved templates; Meta re-approval for changes (3–7 day lead)
- **Offline sync:** 100 pending offline writes before warning; server-authoritative append-only queue; FIFO sync within 30 seconds of reconnect; failed syncs surface to user with retry

### Reliability

- **API uptime:** ≥99.5% monthly
- **Zero data loss:** Every write succeeds and confirms, or fails and notifies — no silent loss
- **Zero undetected divergence:** Local state never silently differs from server state
- **Backup:** Daily automated backups with 30-day retention
- **Recovery:** Database restorable within 1 hour of incident
