# FitBase — Product Brief

**Management SaaS for Fitness & Wellness Businesses in Nigeria**

---

| | |
|---|---|
| **Document Type** | Product Brief |
| **Product Name** | FitBase |
| **Business Model** | B2B2C SaaS (Monthly Subscription) |
| **Target Market** | Nigerian Fitness & Wellness Industry |
| **Verticals Served** | Gyms, Fitness Studios, Yoga Studios, CrossFit Boxes, Wellness Centers, Spas, Martial Arts Studios, Personal Training Studios |
| **Platform** | Progressive Web App (PWA) — Single App |
| **Version** | MVP v1.0 |
| **Date** | March 2026 |

---

## 1. Executive Summary

FitBase is a purpose-built management SaaS platform designed exclusively for the Nigerian fitness and wellness market. It serves the full spectrum of fitness and wellness businesses — from traditional gyms and CrossFit boxes to yoga studios, wellness spas, martial arts dojos, and personal training studios — providing a unified platform that addresses the unique operational challenges of running these businesses in Nigeria.

The platform tackles Nigeria-specific constraints head-on: unreliable internet connectivity, cash-heavy payment environments, and WhatsApp-first communication preferences. Built on a modern, mobile-first Progressive Web App, FitBase is a single app where users select their role on sign-up — either as a business (owner/staff) or as a member/client. This unified architecture keeps distribution simple, reduces maintenance overhead, and creates a seamless experience for users who may be both a business operator and a member at different facilities.

Revenue is generated through monthly subscriptions paid by businesses via bank transfer or in-person cash collection, with manual renewal and WhatsApp-based reminders.

---

## 2. Problem Statement

Nigeria's fitness and wellness industry is growing rapidly, yet business owners across the sector — whether running a gym, yoga studio, or wellness spa — operate with fragmented, manual tools that create inefficiencies:

- **Manual record-keeping:** Membership data lives in spreadsheets, notebooks, or paper logs, leading to lost records, billing errors, and no visibility into business performance.
- **Payment friction:** Nigerian fitness businesses rely heavily on cash and bank transfers. Existing management software assumes card-first payment models, forcing owners into workflows that don't match local reality.
- **Connectivity challenges:** Internet access in Nigeria is inconsistent. Cloud-only software breaks during outages, disrupting check-ins, payments, and daily operations.
- **Communication gaps:** Business owners communicate with clients via WhatsApp, but no management platform integrates natively with WhatsApp as a notification channel.
- **Imported solutions don't fit:** Global platforms (Mindbody, Glofox, etc.) are priced for Western markets, don't support Naira payments, and lack Nigeria-specific workflows. They also tend to be gym-centric, underserving studios, spas, and wellness centers.
- **No cross-vertical platform:** A yoga studio owner and a gym owner face the same operational challenges — memberships, payments, check-ins, staff — but are forced to use different tools or none at all. No single platform serves the breadth of the Nigerian fitness and wellness market.

---

## 3. Target Market

### 3.1 Verticals Served

- **Traditional Gyms:** Independent and chain gyms offering weight training, cardio, and general fitness.
- **Fitness Studios:** Boutique studios for spinning, HIIT, Pilates, aerobics, and group fitness classes.
- **Yoga & Mindfulness Studios:** Studios offering yoga, meditation, and breathwork sessions.
- **CrossFit Boxes:** Affiliate and independent CrossFit training facilities.
- **Wellness & Spa Centers:** Wellness centers offering massage, physiotherapy, and holistic health services.
- **Martial Arts Studios:** Dojos and studios for kickboxing, MMA, taekwondo, and self-defense training.
- **Personal Training Studios:** Private and semi-private training spaces run by independent trainers or small teams.

### 3.2 Target Users

**Primary Users (B2B):**

- **Business Owners:** Independent fitness and wellness business owners in Nigerian cities who need affordable, reliable tools to manage memberships, payments, and operations.
- **Managers & Staff:** Front-desk personnel, studio managers, and instructors who handle daily check-ins, client inquiries, and payment collection.

**Secondary Users (B2C):**

- **Members & Clients:** Fitness enthusiasts and wellness clients who want to view their membership status, check-in history, make payments, and receive notifications from their fitness or wellness provider.

---

## 4. Product Vision

To become the default operating platform for fitness and wellness businesses in Nigeria by delivering the most locally relevant, reliable, and affordable management solution in the market. FitBase will be the platform that every Nigerian fitness and wellness business owner reaches for because it was built for how they actually run their business — regardless of whether that business is a gym, a yoga studio, or a wellness spa.

### 4.1 Design Principles

- **Nigeria-first:** Every feature decision is filtered through the lens of Nigerian market realities — connectivity, payment methods, communication habits, and device landscape.
- **One app, two experiences:** A single PWA where users select their role (business or member) on sign-up. The interface adapts accordingly — business users see operations tools, members see their membership dashboard. Users can hold both roles simultaneously.
- **Vertical-agnostic, locally specific:** The platform's core workflows (memberships, payments, check-ins, staff) are universal across fitness and wellness verticals, with configurable options that let each business type tailor the experience.
- **Offline-resilient:** Core operations work without internet. Data syncs seamlessly when connectivity returns.
- **WhatsApp-native:** WhatsApp is the primary notification channel, not email. The platform integrates with WhatsApp Cloud API for all client communications.
- **Progressive complexity:** Start simple, grow powerful. Small studios get an easy onboarding experience; larger operations unlock advanced features as they scale.

---

## 5. Product Architecture

### 5.1 Single-App PWA with Role Selection

FitBase is a single Progressive Web App. On sign-up, users select whether they are joining as a business (to manage a fitness or wellness facility) or as a member/client (to interact with a facility they belong to). The app adapts its interface based on this role:

| Business Experience | Member Experience |
|---|---|
| Operations dashboard for managing memberships, processing payments, handling check-ins, configuring business settings, managing staff, and viewing reports. Terminology adapts to the business vertical (e.g., "members" for gyms, "clients" for spas). | Personal dashboard for viewing membership status, check-in history, payment records, and receiving WhatsApp notifications. Works for gym members, yoga students, spa clients, and all other verticals. |

A single user account can hold both roles. For example, a personal trainer who owns a studio (business role) may also be a member at a separate gym (member role). Role switching is available from the app's navigation without logging out.

### 5.2 Key Technical Decisions

- **Single PWA:** One installable app, no app store dependency. Reduces data usage and works on low-end Android devices prevalent in the Nigerian market. Role-based UI adapts the experience without requiring separate codebases.
- **Offline-first via IndexedDB & Service Workers:** Critical operations (check-ins, payment recording) cached locally and synced when online.
- **Paystack integration:** Dedicated Virtual Accounts (DVA) for bank transfer subscription payments. Webhooks auto-confirm transfers.
- **WhatsApp Cloud API:** Primary notification channel for payment receipts, membership reminders, subscription renewal alerts, and check-in confirmations.
- **Rotating QR tokens:** Secure, time-limited QR codes for member/client check-in that prevent screenshot sharing and unauthorized access.
- **Configurable business profiles:** Onboarding flow lets owners select their business type (gym, studio, spa, etc.), which adapts terminology, default settings, and relevant feature surfaces throughout the app.

---

## 6. MVP Feature Set

The MVP delivers seven core features prioritized using the MoSCoW framework. These features are designed to be vertical-agnostic, serving gyms, studios, spas, and all other fitness and wellness businesses equally:

| Feature | Description | Priority |
|---|---|---|
| Billing & Payments | Paystack-powered payments supporting bank transfers and manual cash recording for member payments, with auto-receipt generation via WhatsApp. | **Must Have** |
| Membership Management | Create and manage membership/service plans, assign clients, track status (active, expired, frozen), and handle renewals and upgrades across any business type. | **Must Have** |
| Check-in & Attendance | QR-based check-in with rotating tokens, manual check-in fallback, attendance history, and real-time capacity tracking. | **Must Have** |
| Business Setup & Config | Onboarding wizard with role selection (business or member), business profile setup (with vertical selection), operating hours, service/membership plans, staff roles, and branding. | **Must Have** |
| Staff Management | Role-based access control (Owner, Manager, Front Desk/Reception), staff invitations, activity logs, and permission management. | **Must Have** |
| Notifications | WhatsApp-first notifications for payment confirmations, membership expiry reminders, check-in alerts, subscription renewal reminders, and promotional messages. | **Must Have** |
| Reporting & Analytics | Dashboard with key metrics: revenue, active members/clients, attendance trends, plan popularity, and payment method breakdowns. | **Must Have** |

---

## 7. Business Model

### 7.1 Revenue Model

FitBase charges businesses a monthly subscription fee to access the platform. Subscriptions are paid via bank transfer (using Paystack Dedicated Virtual Accounts) or in-person cash collection by a FitBase sales agent. There is no auto-renewal — businesses manually renew each month, prompted by WhatsApp reminders sent at 7 days, 3 days, and 1 day before expiry.

### 7.2 Subscription Payment Flow

The subscription payment process works as follows:

- **Reminder phase:** WhatsApp reminders are sent to the business owner at 7, 3, and 1 day(s) before the subscription is due, including the amount, due date, and payment instructions.
- **Payment phase (bank transfer):** FitBase generates a dedicated virtual account via Paystack for each business. The owner transfers the subscription amount, and Paystack's webhook automatically confirms receipt and activates the subscription.
- **Payment phase (in-person cash):** A FitBase sales agent collects payment from the business and logs it in the FitBase admin panel. A FitBase administrator manually verifies and confirms the transaction, which activates the subscription.
- **Activation:** Once payment is confirmed, the subscription status is set to active, the billing period dates are updated, and a WhatsApp receipt is sent to the business owner with confirmation and the next renewal date.
- **Grace period:** If a business does not renew by the expiry date, a 3–5 day grace period allows continued access with a persistent renewal banner. After the grace period, the account enters read-only mode — the business can view existing data but cannot process new check-ins or payments.

### 7.3 Pricing Principles

- **Low barrier to entry:** Affordable monthly pricing to drive adoption across Nigerian fitness and wellness businesses of all sizes and types.
- **Simple and predictable:** A flat monthly fee that business owners can budget for. No per-transaction charges, no hidden costs.
- **Manual renewal by design:** Respects the cash-heavy, bank-transfer-first payment culture in Nigeria. No surprise charges. Businesses pay when they're ready, prompted by WhatsApp reminders.
- **Vertical-neutral:** Same pricing structure regardless of whether the business is a gym, yoga studio, or wellness spa.

---

## 8. Competitive Landscape

FitBase differentiates from both global platforms and local alternatives across the full fitness and wellness spectrum:

| Dimension | Global Platforms | Local Alternatives | FitBase |
|---|---|---|---|
| Pricing | USD-based, expensive | Varies, often manual | **Naira-based, monthly sub** |
| Payments | Card-first | Cash/transfer only | **Bank transfer + cash** |
| Connectivity | Cloud-dependent | Basic/manual | **Offline-first PWA** |
| Notifications | Email/SMS | WhatsApp (manual) | **WhatsApp Cloud API** |
| Localization | Global focus | Partial | **Nigeria-first design** |
| Verticals | Gym-centric | Single vertical | **All fitness & wellness** |
| Architecture | Separate apps | Web-only | **Single PWA, role-based** |

---

## 9. Success Metrics

### 9.1 Adoption Metrics

- Number of businesses onboarded in first 6 months (across all verticals)
- Vertical distribution of onboarded businesses
- Monthly active business operators
- Monthly active members/clients
- Client-to-business ratio (engagement depth)

### 9.2 Engagement Metrics

- Daily check-ins processed per business
- WhatsApp notification delivery and open rates
- Feature adoption rates across the seven core modules
- Offline usage frequency and sync success rates

### 9.3 Revenue Metrics

- Monthly recurring revenue (MRR) from subscriptions
- Subscription renewal rate
- Payment method split (bank transfer vs. cash)
- Average time from reminder to payment
- Churn rate (business-level)
- Revenue breakdown by vertical

---

## 10. Risks and Mitigations

| Risk | Impact | Mitigation |
|---|---|---|
| Low internet reliability | Core features become unusable | Offline-first architecture with IndexedDB caching and background sync |
| Cash payment dominance | Manual subscription collection overhead | Sales agent network for in-person collection; incentivize bank transfer adoption over time |
| Device fragmentation | Poor UX on low-end devices | Single PWA optimized for low-spec Android; minimal data usage |
| WhatsApp API limits | Notification delivery failures | Rate limiting, message queuing, and SMS fallback for critical notifications |
| Subscription churn | Revenue instability | Grace period, persistent renewal prompts, value-driven engagement to reduce voluntary churn |
| Multi-vertical complexity | Feature bloat or diluted UX | Shared core workflows with configurable terminology and settings per vertical; phased vertical-specific features post-MVP |
| Single-app complexity | Role switching confusion | Clear onboarding flow with role selection; intuitive navigation with role indicator; user testing with both personas |

---

## 11. Roadmap Outlook

### Phase 1: MVP Launch

Deliver the seven core features (billing, membership, check-in, business setup, staff management, notifications, reporting) within the single-app architecture to early-adopter fitness and wellness businesses in Lagos. Validate product-market fit across multiple verticals and refine based on operator and member feedback.

### Phase 2: Growth & Expansion

- Class, session, and appointment scheduling (critical for studios and spas)
- Trainer and instructor management with booking
- Multi-branch and multi-location support
- Advanced analytics and financial reporting
- Client engagement features (workout logging, wellness tracking, challenges)
- Vertical-specific feature packs (e.g., treatment menus for spas, belt/rank tracking for martial arts)
- Tiered subscription plans (basic, pro, enterprise) as feature set expands

### Phase 3: Platform & Ecosystem

- Marketplace for fitness equipment, supplements, and wellness products
- API integrations with accounting and HR platforms
- Franchise and white-label capabilities
- Client discovery and booking marketplace (find fitness/wellness businesses near you)
- Expansion to other West African markets

---

*End of Product Brief*
