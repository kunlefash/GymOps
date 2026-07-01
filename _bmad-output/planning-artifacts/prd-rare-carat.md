---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-06-innovation, step-07-project-type, step-08-scoping, step-09-functional, step-10-nonfunctional, step-11-polish, step-12-complete]
inputDocuments:
  - rare-carat-product-brief.md
workflowType: 'prd'
classification:
  projectType: web_app_feature_redesign
  domain: consumer_marketplace_ecommerce_diamond_jewelry
  complexity: medium-high
  projectContext: brownfield
  specialConcern: anti-steering_recommendation_integrity
  prdStructure: MVP (closing screen + priority question) + Phase 2 (homepage repositioning, email gate removal)
problemFraming:
  rootDrivers:
    - unresolved_asymmetric_stakes
    - trust_deficit_invisible_differences
  designTarget: permission_to_stop
  validationSignals:
    - gemologist_chat_logs
    - funnel_dropoff_location
    - multi_session_purchase_rate
    - compare_tool_usage_vs_conversion
    - filter_churn_on_near_identical_results
visionInsights:
  coreVision: Transform Rare Carat from a marketplace that lists diamonds into an advisor that finds yours — the guided flow is the front door, browse is the fallback
  differentiationMoment: When the shopper reads "Best balance of size and sparkle for your budget" on the detail page and does not need to ask "Is this a nice diamond?" because the product already answered it
  coreInsight: A recommendation is only trustworthy when it comes with a reason you can reject — visible reasoning is where confidence lives, hidden ranking is where steering hides
  whyNow: The quiz translation layer already exists, AI picks already surface, quality scores already exist — this is structural repositioning of what Rare Carat already built, not invention
  visionFraming: redesign_flow_as_front_door
newProductIdeas:
  - whats_actually_different_comparison_mode
  - sparkle_simulation_visual_differentiation
  - why_the_price_gap_explainer
  - recommendation_rationale_carried_to_detail_page
  - gemologist_endorsement_layer
  - explicit_youve_found_your_stone_closing_language
  - cohort_social_proof_baked_into_ranking
  - priority_weighted_scoring_engine
---

# Product Requirements Document - Rare Carat Diamond Advisor

**Author:** Adekunle
**Date:** 2026-06-30

---

## Executive Summary

Rare Carat holds the largest lab-grown diamond catalog online — over 900,000 stones — with AI price and quality scoring layered on top. The product correctly identified that a non-expert buyer needs guidance, built a quiz that translates gemological specs into plain-English outcomes, and failed to close: the quiz ends on the same 900,000-stone catalog it was supposed to replace. The shopper who took the guided path and the shopper who ignored it land on the same filter wall, with the same generic "Overall pick" label and no reason to stop comparing.

The Diamond Decision Advisor redesign corrects this. It transforms Rare Carat from a marketplace that lists diamonds into an advisor that finds yours — the guided flow becomes the front door, browse the fallback for experts who want it.

**Target user:** Men buying engagement rings account for 86% of purchases; ~67% report feeling overwhelmed by the technical decision. The purchase is emotionally high-stakes (median ~$5,000), close to one-shot, and often shaped by partner hints the buyer is trying to decode. This is not a catalog browser optimizing a spreadsheet — it is an anxious non-expert spending a large sum on a public, permanent decision he is afraid of getting wrong.

**Two root drivers of decision failure:**
1. **Unresolved asymmetric stakes.** Diamond purchases are irreversible. The shopper needs permission to stop looking, not just fewer options. The design target is a declaration — "you've found your stone" — not a narrowed list.
2. **Invisible meaningful differences.** Near-identical stones separated by $70 with no explanation manufacture a specific fear: *I will pay more and get less.* The product does not tell the shopper why the price differs, which specs matter visually, or why two 15/15 stones cost different amounts.

### What Makes This Special

Rare Carat already built the salesperson. The quiz quality translation step is the best product interaction on the site. The closing recommendation screen, the priority-weighted ranking, the rationale carry-through to the detail page — none of these require new data or new AI. They require the existing intelligence to be surfaced in the right place, in the right order, with a reason the shopper can read and reject.

A recommendation is only trustworthy when it comes with a reason you can reject. Hidden ranking is where steering hides; visible reasoning is where confidence lives. Every recommendation must display a plain-English rationale, and ranking must be driven by the shopper's stated priority — not Rare Carat's take rate or seller placement fees. This is not a UI concern; it is a trust-integrity requirement underpinning the entire value proposition.

**MVP scope:** Priority question (size / sparkle / value) + closing recommendation screen (one primary match, two differentiated alternates, plain-English reason per pick) + rationale string carried through to the detail page.

**Phase 2 scope:** Homepage repositioning (advisor as front door), budget step with anchored ranges replacing the empty $0 input, email capture moved post-recommendation, gemologist endorsement layer distinct from AI score, "What's actually different" comparison mode showing outcome-language deltas not spec tables.

### Project Classification

| Attribute | Value |
|-----------|-------|
| **Project Type** | Brownfield web app feature redesign |
| **Domain** | Consumer marketplace / e-commerce (diamond jewelry) |
| **Complexity** | Medium-high (trust architecture + recommendation integrity) |
| **Context** | Brownfield — redesigning Rare Carat's existing quiz + result flow |
| **Special Concern** | Recommendation integrity / anti-steering |
| **Primary User** | Non-expert first-time engagement ring buyer (male, 25–45) |
| **Preserved Path** | Expert / returning shopper browse flow — unchanged |

---

## Success Criteria

### User Success

The primary emotional success metric is post-purchase confidence: **80%+ of advisor-led purchasers answer "Yes" to "Did you feel confident in your choice?"** (binary post-purchase survey). The benchmark value of 80% reflects the structural reality that some buyer's remorse is unavoidable on a $5,000 one-shot purchase; below 70% indicates the advisor built funnel throughput without building genuine confidence. The signal that matters is the gap: advisor-led purchases must score meaningfully higher than browse-led purchases on the same question.

The four paralysis behaviours — comparing, second-guessing, delaying, dropping off — are tracked as a metric stack, each at its own funnel position:

| Behaviour | Metric | Target |
|-----------|--------|--------|
| **Keep comparing** | Stones viewed per session before detail page click | Advisor sessions: 3–5 stones. Browse sessions: baseline (expected 15–30). |
| **Second-guess** | Sessions to purchase (visits before conversion) | Advisor path median sessions lower than browse path median. |
| **Delay** | Days from first visit to purchase | Meaningful reduction in median purchase cycle length on advisor path vs. browse path. |
| **Drop off** | Advisor flow completion rate | ≥70% of users who start the advisor reach the recommendation screen. |

**The single headline user metric:** Sessions to purchase on the advisor path. It captures all four paralysis behaviours in one number — comparing, second-guessing, and delaying all manifest as returning to the site instead of buying.

### Business Success

| Metric | Target | Rationale |
|--------|--------|-----------|
| Advisor-led conversion rate | Meaningfully above filter-wall conversion rate | Primary business proof that the flow closes decisions |
| Gemologist chat volume — "which is better / is this good" queries | Measurable reduction vs. pre-launch baseline | Proxy for how many shoppers the advisor failed to answer |
| Return and exchange rate — advisor-led purchases | At or below site-wide average | A confidence win shows up as fewer regretted purchases, not just more checkouts |
| Overall site conversion and AOV | No degradation vs. pre-launch baseline | Coexistence requirement |

**3-month target:** Advisor flow instrumented, A/B test running, primary metrics collecting against pre-registered baseline. No premature reads — diamond purchase cycles run weeks to months.

**12-month target:** Advisor path shows statistically significant conversion lift and sessions-to-purchase reduction. Gemologist chat volume trending down. Return rate on advisor-led purchases at or below site average. Email capture rate post-recommendation measured and compared to pre-recommendation gate baseline.

### Technical Success

| Requirement | Target |
|-------------|--------|
| Recommendation screen render time | Under 2 seconds from quiz completion to closing screen display |
| Quiz completion rate | ≥70% of starters reach recommendation screen |
| Recommendation engine correctness | Ranked picks match stated shopper priority in 100% of cases (auditable by priority × stone spec matrix) |
| Filter-wall availability | Zero degradation — full browse path functional and independently measurable throughout |

### Measurable Outcomes

**Experiment design:** Ship as a randomised A/B test. Advisor flow = treatment; existing filter wall = control. Pre-register the primary metric (sessions to purchase) and a minimum detectable effect before reading results. Hold for at least one full purchase cycle before any read. Monitor all guardrail metrics for the full test duration.

**Anti-steering guardrail:** Track recommended-stone gross margin vs. catalog average on a weekly basis from launch. Upward drift is a defect, not a result to keep. Trigger a ranking audit if advisor-recommended stones average more than 5% above catalog margin baseline.

---

## Product Scope

### MVP — Minimum Viable Product

The smallest change that fixes the actual defect and is measurable in isolation:

1. **Priority question** — added to the existing quiz flow: "What matters most to you?" (Size / Sparkle / Value). Single-select. Feeds the recommendation ranking engine.
2. **Closing recommendation screen** — replaces the current filter-wall dump at quiz end. Displays: one primary match ("Your stone"), two clearly differentiated alternates ("A little bigger" / "A little sparklier"), a plain-English reason for each pick, and a visible "See all results" escape hatch.
3. **Rationale carry-through** — the recommendation reason string ("Best balance of size and sparkle for your $2,000 budget") persists to the detail page, replacing the silent "Overall pick" label.
4. **Priority-weighted ranking engine** — backend ranking logic that scores stones against stated priority (size → optimise carat first; sparkle → optimise cut first; value → optimise price score first) within the shopper's budget and quality floor.

MVP explicitly excludes: homepage repositioning, budget anchoring, email gate removal, gemologist layer, comparison mode redesign. These are preserved as Phase 2 to keep the experiment clean and measurable.

### Growth Features (Phase 2)

Features that make the advisor competitive and address the second root driver (invisible meaningful differences):

- **Homepage repositioning** — advisor as the default front door ("Find my diamond" CTA primary; "Search the catalog" secondary). Filter wall stays fully intact as the expert path.
- **Budget anchoring** — replace the empty $0 input with anchored ranges ("Most shoppers in your shape choose between $1,500–$3,000") to reduce first-question abandonment.
- **Email capture moved post-recommendation** — capture email after the shopper has received value ("Save your recommendation and get expert follow-up"), not as a toll before results.
- **"What's actually different" comparison mode** — replaces the spec-table comparison view with a plain-English delta list: "Stone A is slightly bigger. Stone B is slightly sparklier. Price difference: $90." Full spec table remains accessible via toggle.
- **"Why the price gap" explainer** — plain-English tooltip or inline text on detail page explaining the price difference between near-identical stones: "This one costs more because the cut grade is higher — it catches more light."
- **Gemologist endorsement layer** — visual distinction between AI-scored picks and gemologist-reviewed picks on the recommendation screen and card grid.

### Vision (Future)

- **Sparkle simulation** — visual differentiation in the card grid using rendered light-behaviour previews by cut quality, not just cert scan images.
- **Cohort social proof in ranking** — "Shoppers with your budget and shape most often ended up with H color, VS2 clarity" surfaced as an inline signal on the recommendation screen, not just decorative copy.
- **Persistent advisor session** — recommendation and rationale survive across browser sessions, allowing multi-day return visits without restarting the quiz.
- **Rationale on ring builder** — when the shopper moves from diamond to setting, the advisor's reason string persists through the full ring-builder flow to checkout.

---

## User Journeys

### Journey 1: Marcus — The Anxious Proposer *(Primary user, success path)*

Marcus is 31, a software engineer in Austin. Priya has dropped exactly three hints about wanting an oval diamond — once at a jewelry store window, once when a colleague got engaged, and once in a Pinterest board she "accidentally" left open. He has $2,500 and two weeks before he plans to propose at her sister's wedding. He knows nothing about diamonds and is afraid of getting it wrong.

**Opening scene:** He types "lab diamond engagement ring" into Google on his phone during a lunch break. He lands on rarecarat.com. The homepage leads with "Find my diamond." He taps it. *(Note: the advisor flow is designed mobile-first — this journey begins and may end on a phone, with desktop completion as a common variant for the purchase step.)*

**Rising action:** Ajay appears. Six questions, four minutes. Shape: Oval. Budget: $2,500. "What matters most to you?" — Size, Sparkle, or Value. He pauses. He thinks of the Pinterest board — the stones all looked big. He taps **Size**. Quality: "Pretty white, no imperfections to the naked eye" — the middle, recommended option. Cut: best cut.

**Climax:** The recommendation screen loads. "Your stone: 2.47ct Oval, H color, VS1, RC Ideal Cut — $2,280." Reason: *"Largest size at your budget that still catches light like an ideal cut."* Social proof beneath: *"94 couples chose a stone from this quality tier last month."* Two alternates below: "A little sparklier: 2.31ct, G color, $2,280" and "A little bigger: 2.58ct, I color, $2,180." He reads the reason. The social proof holds him. He does not click "See all results." He clicks through to the detail page.

**Resolution:** The rationale string is still there: *"Recommended: largest oval at your budget with ideal-cut sparkle."* He reads the 30-day returns guarantee. He buys in the same session — first visit, no return. Post-purchase: "Did you feel confident in your choice?" He clicks Yes.

**Capabilities revealed:** Priority question in quiz, priority-weighted ranking engine, closing recommendation screen with plain-English reasons and social proof beat, two differentiated alternates, rationale string on detail page, mobile-responsive advisor flow, visible "See all results" escape hatch.

---

### Journey 2: Jamie — The Comparison Looper *(Primary user, edge case)*

Jamie is 28, a teacher in Chicago. She has been on Rare Carat for three weeks — taken the quiz twice, gone back to the filter wall, compared 40 stones across two sessions, bookmarked six. She has not bought. She comes back for the fourth time.

**Opening scene:** The advisor is the front door. She takes it again: round, $1,800, sparkle-first. She has done this before. She is half-expecting the same filter wall dump.

**Rising action:** The recommendation screen shows her pick: 1.42ct round, G VS2, RC Ideal, $1,720. Reason: *"Best cut quality at your budget — will outsparkle stones half a carat larger."* She reads the two alternates. She thinks of the 1.51ct she bookmarked. She clicks "See all results."

**Climax:** The filter wall opens with quiz state pre-loaded into the URL parameters — her shape, budget, and quality floor are already set. Her recommended stone is pinned at the top of results. A persistent recommendation sidebar (collapsed by default, expandable) shows her pick and reason. She finds the 1.51ct. She hovers: "Why the price difference?" — tooltip: *"Larger by 0.09ct. Cut grade is Excellent vs. RC Ideal — slightly less sparkle at this price point."* She returns to the recommendation sidebar. She re-reads the reason. The decision crystallises.

**Resolution:** She buys the recommended stone. Four sessions becomes one.

**Technical note (three distinct capabilities):**
1. Quiz state carried into filter URL parameters on "See all results" click
2. Recommended stone pinned at position 1 in results grid
3. Recommendation sidebar persists in collapsed state; expandable on tap/click

**"Why the price gap" tooltip spec:** Trigger — hover (desktop) / tap info icon (mobile). Data source — delta between the hovered stone's cut grade and the pinned recommendation's cut grade, expressed in plain-English outcome language. Display context — card grid and detail page.

**Capabilities revealed:** "See all results" with quiz state carry, recommendation pin in grid, persistent sidebar, "Why the price gap" tooltip (trigger + data + display context specified).

---

### Journey 3: Diane — The Expert Shopper *(Secondary user, preserved browse path)*

Diane is 45, a gemologist, buying a diamond for her daughter's anniversary gift. She knows exactly what she wants: 1.5ct round, G color, VS1, GIA certified, under $3,500. She comes to rarecarat.com for price comparison, not advice.

**Opening scene:** Homepage. She sees "Find my diamond" as the primary CTA and "Search the catalog" beneath it. She clicks "Search the catalog." The filter wall opens exactly as it always has.

**Journey:** She sets filters in 30 seconds, sorts by price, finds her stone, buys. She does not touch the advisor. It does not slow her down or get in her way.

**Resolution:** She completes her purchase through the existing browse flow. She never sees the advisor mentioned. No interstitials, no "haven't tried the advisor?" nudge, no quiz prompts on return visits.

**Coexistence contract (explicit):** Users who click "Search the catalog" or who have previously demonstrated browse intent (visited filter wall without taking the quiz) receive no advisor overlays, modals, or re-engagement nudges in the current session. The filter wall is fully intact, independently instrumented, and shows zero degradation in any A/B test configuration.

**Capabilities revealed:** "Search the catalog" as a clear, always-available secondary CTA on homepage; no advisor interruptions for browse-intent users; filter wall independently measurable throughout.

---

### Journey 4: The Rare Carat Gemologist — The Curation Layer *(Internal user, Phase 2)*

Leila is a Rare Carat gemologist. Weekly, she receives a batch of stones the AI has scored 15/15 that are surfacing in top advisor recommendation slots. She reviews them against cert data — checks for unusual depth percentages, fluorescence edge cases, proportion anomalies the AI score does not catch. She marks reviewed stones "Gemologist verified." That status surfaces as a distinct badge on the recommendation screen alongside the AI quality score.

**Opening scene:** Leila opens the internal curation queue. Forty stones flagged for review this week.

**Journey:** She works through each stone, cross-referencing cert data, marking pass/flag. Flagged stones are demoted from advisor recommendation slots until re-reviewed. Passed stones carry the endorsement badge.

**Resolution:** Shoppers like Marcus see "Gemologist verified" on their recommended stone — a human validation layer the AI score alone cannot provide.

**Capabilities required (Phase 2, out of MVP scope):** Internal curation tool, gemologist review status field per stone in data model, badge rendering on recommendation screen and detail page, demotion logic for flagged stones.

---

### Journey 5: The Uninformed Gift Buyer *(Future — Phase 2 flag only)*

No journey narrative for MVP. This persona has no style hints ("she mentioned she likes jewelry") and needs a style discovery layer before the current quiz can start. Flagged as a Phase 2 entry point: a "start with style" pre-quiz path surfacing popular styles, ring imagery, and bestseller social proof before asking any spec questions. Requirements deferred.

---

### Journey Requirements Summary

| Capability | Revealed by | Scope |
|------------|-------------|-------|
| Priority question in quiz | Marcus, Jamie | MVP |
| Priority-weighted ranking engine | Marcus, Jamie | MVP |
| Closing recommendation screen (1 match + 2 alternates + reasons) | Marcus, Jamie | MVP |
| Social proof beat on recommendation screen | Marcus | MVP |
| Rationale string on detail page | Marcus, Jamie | MVP |
| Mobile-responsive advisor flow | Marcus | MVP |
| "See all results" escape hatch | Jamie | MVP |
| Quiz state carry into filter URL | Jamie | MVP |
| Recommended stone pinned in results grid | Jamie | MVP |
| Persistent recommendation sidebar | Jamie | MVP |
| "Why the price gap" tooltip (hover/tap, outcome language) | Jamie | Phase 2 |
| "Search the catalog" secondary CTA — homepage | Diane | Phase 2 (homepage reposition) |
| No advisor interruptions for browse-intent users | Diane | MVP (coexistence contract) |
| Filter wall independently instrumented | Diane | MVP |
| Internal curation tool + gemologist badge | Leila | Phase 2 |
| Style discovery pre-quiz path | Uninformed buyer | Future |

---

## Domain-Specific Requirements

This product operates in consumer e-commerce — no heavy regulatory domain (no HIPAA, no PCI-DSS beyond standard payment processing, no SOX). Three domain-specific concerns are unique to the marketplace + recommendation product combination and must be formally addressed.

### Recommendation Integrity (Marketplace Anti-Steering)

Rare Carat is a marketplace listing stones from many sellers. The advisor's ranking engine has an inherent conflict-of-interest surface: results could favour stones with higher seller placement fees or higher gross margin for Rare Carat, at the expense of the shopper's stated priority.

**Requirements:**
- Ranking must be determined solely by shopper-stated priority (size / sparkle / value), budget ceiling, and quality floor — applied against the existing price score and quality score. Seller placement fees and Rare Carat margin must not be ranking inputs.
- Every recommendation must display a plain-English rationale that is derivable from the shopper's stated inputs and the stone's objective specs. A reason the shopper can read is a reason they can reject — this is the anti-steering contract.
- Anti-steering guardrail metric: recommended-stone gross margin vs. catalog average tracked weekly. Trigger a ranking audit if advisor-recommended stones average more than 5% above catalog margin baseline.
- Ranking logic must be auditable: a priority × stone spec matrix must produce deterministic, reproducible results for any given input set.

### Shopper Preference Data (Privacy)

The advisor flow captures preference data — priority, budget, shape, quality tier — that the existing filter wall does not persist. This is net-new data collection with PII-adjacent characteristics.

**Requirements:**
- GDPR (EU shoppers) and CCPA (California shoppers) apply at point of collection. Consent must be captured at or before preference data is stored server-side.
- Data retention policy required: shopper preference data must have a defined retention window and a deletion pathway.
- Right to deletion: if a shopper requests data removal, advisor preference data must be included in the deletion scope alongside account data.
- For MVP: preference data may be stored client-side (session storage / local storage) with no server persistence — this sidesteps GDPR/CCPA server-side obligations for the initial experiment while still enabling the recommendation engine. Server-side persistence is a Phase 2 dependency.

### Multi-Session State Persistence (Vision Scope)

The Vision scope item "persistent advisor session" requires storing quiz answers and recommendation results across browser sessions. This elevates the privacy requirements above MVP scope.

**Requirements (Vision / Phase 2):**
- Server-side session storage for advisor state requires explicit opt-in consent UI at the point the shopper would benefit ("Save your recommendation — we'll remember your preferences next time").
- Stored advisor state must be included in the data export and deletion pathways described above.
- Anonymous persistence (device-keyed, no account required) is acceptable for MVP+ experimentation but must be disclosed in the privacy policy.

---

## Innovation & Novel Patterns

This product does not introduce new technology. The innovation is design and product strategy: applying recommendation transparency principles to a specific marketplace trust problem, with a measurable guardrail against the incentive misalignment that would otherwise undermine it.

### Detected Innovation Areas

**1. Recommendation transparency as a trust mechanism**
Standard marketplace recommendation engines treat ranking logic as proprietary and optimise for platform outcomes (margin, placement revenue). This product inverts that: every recommendation must display a plain-English rationale the shopper can read and reject. The hypothesis is that visible reasoning builds more durable trust than algorithmic precision, and that durable trust converts better at higher retention rates. This is a testable, non-obvious product bet — not an incremental improvement.

**2. "Permission to stop" as an explicit design target**
Conventional e-commerce UX optimises for engagement: discovery, browsing, wishlisting, return visits. This product explicitly optimises for closure — the session succeeds when the shopper stops comparing. That inverts the standard engagement model. It requires different instrumentation (sessions to purchase as the headline metric, not time on site or pages viewed) and different copy principles ("You've found your stone" rather than "See more options").

**3. Anti-steering as a first-class product requirement**
The conflict-of-interest surface in a marketplace recommendation system is typically handled by policy, not by product instrumentation. This PRD makes it a measurable, auditable product requirement: recommended-stone gross margin is tracked weekly, a 5% threshold above catalog average triggers a ranking audit, and the ranking logic must be deterministic and reproducible. Building the anti-steering contract into the product spec — not the terms of service — positions recommendation integrity as a feature, not a compliance checkbox.

### Validation Approach

| Innovation | Hypothesis | Validation Method |
|------------|------------|-------------------|
| Visible reasoning builds trust | Advisor-led confidence score > browse-led confidence score | Post-purchase binary survey, split by path |
| Closure-optimised UX converts better | Advisor path sessions-to-purchase < browse path | A/B test, pre-registered primary metric |
| Anti-steering guardrail works | Recommended-stone margin ≤ catalog average + 5% | Weekly margin monitoring, ranking audit on breach |

### Risk Mitigation

| Risk | Description | Mitigation |
|------|-------------|------------|
| Visible reasoning backfires | Shopper reads the reason, disagrees, and loses trust entirely | Two alternates + "See all results" always visible; recommendation is a starting point, not a mandate |
| Closure framing alienates browsers | "You've found your stone" feels pushy to a shopper who wants to explore | A/B test copy variants; track "See all results" click rate as a discomfort signal |
| Anti-steering guardrail creates perverse incentive | Ranking suppresses high-quality stones because they have above-average margin | Audit protocol reviews both margin deviation AND quality score correlation; flag both directions |

---

## Web App Technical Requirements

### Project-Type Overview

The Diamond Decision Advisor is a feature redesign within Rare Carat's existing React SPA. No architectural change — the advisor quiz and recommendation screen are new SPA route segments extending the current application. The ranking engine is a new backend service (or extension of the existing AI picks service) callable from the frontend via the existing API layer.

### Browser & Device Support

| Platform | Target | Priority |
|----------|--------|----------|
| iOS Safari | Last 2 versions | Critical — primary mobile entry point for target demographic |
| Chrome Android | Last 2 versions | Critical |
| Chrome Desktop | Last 2 versions | High |
| Safari Desktop | Last 2 versions | High |
| Firefox Desktop | Last 2 versions | Medium |
| Edge Desktop | Last 2 versions | Medium |

**Mobile-first requirement:** The advisor quiz and recommendation screen must be fully functional on viewports from 375px width. Recommendation screen card layout must stack cleanly on mobile — single column, full-width cards, readable reason text without truncation.

### Responsive Design

- Quiz steps: single-column, full-screen-height step layout on mobile; centred card on desktop (existing Ajay quiz pattern)
- Recommendation screen: stacked card layout (primary match full-width, two alternates side-by-side on desktop / stacked on mobile)
- Persistent recommendation sidebar (Jamie's journey): collapsed by default on mobile, expandable via tap; fixed sidebar on desktop at ≥1024px

### Performance Targets

| Interaction | Target |
|-------------|--------|
| Quiz step transition | < 200ms (client-side only) |
| Recommendation screen first render | < 2 seconds from quiz completion |
| "Why the price gap" tooltip | < 300ms (pre-fetched stone data) |
| Filter wall load post "See all results" | Matches existing filter wall baseline — no regression |

### SEO Strategy

Quiz flow is session-based and not indexed — no SEO requirement for quiz routes. Recommendation screen URLs are session-only for MVP. **Phase 2:** encode quiz state in recommendation URL for shareability ("send this for a second opinion") — deferred to keep MVP and A/B instrumentation clean.

### Accessibility

WCAG 2.1 AA minimum. Specific requirements:
- Quiz step buttons must be keyboard-navigable and announce selection state to screen readers
- Recommendation screen cards must meet 4.5:1 contrast ratio on reason text and badge labels
- Labels must not rely on colour alone to convey meaning
- "See all results" escape hatch must be reachable via Tab order before the primary CTA

### Implementation Considerations

- **Ranking engine:** New or extended API endpoint accepting quiz state (shape, budget, quality tier, priority) and returning ranked stone results with rationale strings. Must be independently callable for testability and ranking audits.
- **Rationale string persistence:** Rationale passed as URL parameter or session store value on click-through to detail page — not re-derived from stone specs. Ensures the reason on the detail page matches exactly what appeared on the recommendation screen.
- **Quiz state carry to filter wall:** On "See all results" click, quiz inputs encoded into filter wall URL parameters. Recommended stone SKU passed as a pin parameter. Filter wall reads both without changes to its core logic.

---

## Project Scoping & Phased Development

### MVP Strategy & Philosophy

**MVP Approach:** Validated-learning MVP — ship the smallest isolated change that fixes the core defect and is measurable as a standalone A/B test.

**Rationale:** Homepage repositioning and email gate removal are Phase 2 not because they are less important, but because bundling them into MVP makes the experiment unreadable. If conversion lifts, you cannot attribute it to the recommendation screen vs. the email gate removal. Each Phase 2 change is its own isolated experiment, unlocked only after MVP reaches statistical significance.

**Resource Requirements:**

| Role | MVP Scope |
|------|-----------|
| Frontend engineer × 1 | Quiz priority question, recommendation screen UI, rationale carry-through, quiz state URL encoding |
| Backend engineer × 1 | Ranking engine API endpoint, rationale string generation, stone pin parameter |
| Designer × 1 | Recommendation screen layout, card hierarchy, reason copy framework |
| PM × 1 | A/B test instrumentation, anti-steering guardrail monitoring, margin audit |

No new infrastructure required — all work extends existing API layer and SPA.

**Contingency (frontend-only):** Mock ranking engine against existing AI picks API (Overall / Biggest / Highest). Ships recommendation screen UI and measures user behaviour before custom ranking logic is built. Pure UX validation first, ranking engine second.

### MVP Feature Set (Phase 1)

**Core user journeys supported:** Marcus (anxious proposer — success path), Jamie (comparison looper — edge case), Diane (expert shopper — coexistence contract).

**Must-have capabilities:**
1. Priority question added to quiz ("What matters most?" — Size / Sparkle / Value)
2. Priority-weighted ranking engine API (deterministic, auditable)
3. Closing recommendation screen: one primary match, two differentiated alternates, plain-English reason per pick
4. Social proof beat on recommendation screen (cohort count)
5. "See all results" escape hatch with quiz state carry to filter wall
6. Recommended stone pinned at position 1 in filter wall results
7. Rationale string persisted to detail page
8. Mobile-responsive implementation (375px minimum viewport)
9. WCAG 2.1 AA accessibility compliance on all new components
10. A/B test instrumentation and anti-steering guardrail monitoring

### Post-MVP Features

**Phase 2 (Growth — each as an independent experiment):**
- Homepage repositioning: "Find my diamond" primary CTA, "Search the catalog" secondary
- Budget step anchoring: replace empty $0 input with typical range display
- Email capture moved post-recommendation
- "What's actually different" comparison mode (outcome-language delta list)
- "Why the price gap" tooltip (hover/tap trigger, outcome language)
- Gemologist endorsement layer (requires internal curation tooling)
- Persistent recommendation sidebar in filter wall view

**Phase 3 (Vision):**
- Shareable recommendation URL (quiz state encoded as permalink)
- Sparkle simulation in card grid (cut-quality rendered light previews)
- Cohort social proof baked into ranking inputs
- Persistent advisor session across browser sessions (with consent UI)
- Rationale string persisted through ring-builder to checkout
- Style discovery pre-quiz path for uninformed gift buyer

### Risk Mitigation Strategy

| Risk | Type | Mitigation |
|------|------|------------|
| A/B test reads too early | Market | Hold for full purchase cycle; pre-register primary metric and MDE before launch |
| Ranking rationale feels formulaic | Content | Copy QA: test 10+ stone combinations for rationale quality before launch |
| Recommendation wrong; shopper finds better stone by browsing | Trust | Two alternates + "See all results" always visible; measure "See all results" click rate as discomfort signal |
| Phase 2 ships before MVP validated | Resource | Scope gate: Phase 2 experiments only unlock after MVP A/B reaches statistical significance |
| Anti-steering guardrail creates perverse suppression | Technical | Audit reviews margin deviation AND quality score correlation; flag both directions |

---

## Functional Requirements

### Advisor Flow

- **FR1:** Shoppers can complete a guided diamond selection quiz that collects shape, budget ceiling, quality tier, and priority preference
- **FR2:** Shoppers can select their priority preference ("What matters most?") as a single-select option (Size / Sparkle / Value) within the existing quiz flow
- **FR3:** Shoppers can navigate back to any previous quiz step to change their answer before reaching the recommendation screen
- **FR4:** Shoppers can exit the quiz at any step and access the filter wall without losing the option to return to the advisor path

### Recommendation Engine

- **FR5:** The system can generate a ranked list of matching stones based on shopper-stated priority, budget ceiling, and quality floor
- **FR6:** The system can generate a plain-English rationale string for each recommended stone that references the shopper's stated priority and the stone's distinguishing characteristics
- **FR7:** The system produces deterministic, reproducible ranking results for any given combination of priority, budget, and quality tier inputs
- **FR8:** The ranking engine can be queried independently via API for auditing and testing purposes

### Recommendation Screen

- **FR9:** Shoppers can view a recommendation screen displaying one primary match with a plain-English reason
- **FR10:** Shoppers can view two differentiated alternative stones on the recommendation screen, each labelled by how they differ from the primary pick ("A little bigger" / "A little sparklier")
- **FR11:** Shoppers can view a social proof signal on the recommendation screen indicating how many shoppers have chosen a stone from the same quality tier
- **FR12:** Shoppers can view a closing declaration on the recommendation screen before proceeding ("You've found your stone")
- **FR13:** Shoppers can access the full filter wall from the recommendation screen via a visible "See all results" action without losing their quiz context

### Browse Integration

- **FR14:** Shoppers who trigger "See all results" from the recommendation screen access the filter wall with quiz inputs (shape, budget, quality tier) pre-applied as filter parameters
- **FR15:** Shoppers who trigger "See all results" see their primary recommended stone pinned at position 1 in the filter wall results
- **FR16:** Shoppers can view a collapsible recommendation summary in the filter wall that shows their primary recommended stone and its rationale
- **FR17:** Shoppers who navigate directly to the filter wall (bypassing the advisor) receive no advisor prompts, overlays, or interstitials during their session
- **FR18:** Shoppers can access the filter wall directly via a clearly labelled secondary action on the homepage *(Phase 2 — homepage repositioning)*

### Detail Page & Purchase

- **FR19:** Shoppers who arrive at a detail page from the recommendation screen can view the same rationale string that was shown on the recommendation screen
- **FR20:** Shoppers can proceed from the recommendation screen to a stone's detail page in a single action

### Recommendation Integrity

- **FR21:** The system enforces that stone ranking inputs are limited to shopper-stated priority, existing price score, existing quality score, and stone specifications — seller placement fees and gross margin are excluded as ranking inputs
- **FR22:** Administrators can audit the ranking output for any given set of quiz inputs against the expected priority × stone spec matrix
- **FR23:** The system tracks recommended-stone gross margin against catalog average on an ongoing basis and surfaces deviations above a configured threshold for administrator review
- **FR24:** Each recommendation rationale string is derivable solely from the shopper's stated inputs and the stone's objective specifications

### Analytics & Experimentation

- **FR25:** The system supports A/B test path assignment with the advisor flow as treatment and the existing filter wall as control
- **FR26:** The system tracks sessions to purchase separately for advisor-path and filter-wall-path shoppers
- **FR27:** The system tracks stones viewed per session before a detail page click-through, segmented by path
- **FR28:** The system tracks advisor flow completion rate (ratio of quiz starters who reach the recommendation screen)
- **FR29:** The system presents a binary post-purchase confidence survey ("Did you feel confident in your choice?") to purchasers and stores responses segmented by path

### Privacy & Data Management

- **FR30:** The system presents a consent notice at or before the point where shopper preference data is stored beyond the current browser session
- **FR31:** Shoppers can request deletion of their advisor preference data through the existing account data deletion pathway
- **FR32:** Advisor preference data in MVP is stored client-side only (session or local storage) and is not persisted server-side without explicit shopper opt-in

---

## Non-Functional Requirements

### Performance

| Requirement | Target | Context |
|-------------|--------|---------|
| Recommendation screen first render | < 2 seconds from quiz completion | Delay compounds shopper anxiety |
| Quiz step transition | < 200ms | Client-side only; perceived as instant |
| "Why the price gap" tooltip render | < 300ms | Must feel immediate on hover/tap |
| Filter wall load after "See all results" | No regression vs. current baseline | Coexistence requirement |
| Ranking engine API response (p95) | < 1.5 seconds | Leaves 500ms budget for frontend render within 2s total |
| Recommendation screen on 3G mobile | Usable within 4 seconds | Target demographic is mobile-first |

### Security & Privacy

- Shopper preference data stored client-side only in MVP (session / local storage). No server-side persistence without explicit consent.
- All advisor API endpoints served over HTTPS. No new authentication surface — advisor flow is anonymous/pre-auth, matching existing quiz behaviour.
- Post-purchase confidence survey responses stored against existing order record, subject to existing data retention and deletion policies.
- GDPR and CCPA consent surfaced at or before any server-side data storage (Phase 2+). MVP client-side storage disclosed in updated privacy policy.
- Anti-steering audit logs are internal-only, access-controlled to product and analytics team.

### Accessibility

- WCAG 2.1 Level AA for all new components.
- Quiz step buttons keyboard-navigable with visible focus state; selection state announced to screen readers.
- Recommendation screen card labels must not rely on colour alone — icon or text differentiation required.
- Minimum 4.5:1 contrast ratio on all reason text, badge labels, and social proof copy.
- "See all results" appears in Tab order before the primary CTA.

### Reliability

- If ranking engine is unavailable, advisor flow degrades gracefully to existing AI picks (Overall / Biggest / Highest) — no error state shown to shopper.
- Filter wall remains fully operational regardless of advisor flow availability.
- A/B test assignment is sticky per user session — no mid-session path switching.

### Integration

- Ranking engine queries existing stone catalog and pricing data — no new data source required.
- Fallback on unavailability uses existing AI picks endpoint.
- Rationale string passed as URL parameter or session store value to existing detail page — no changes to detail page core logic.
- A/B test events and confidence survey responses instrumented using Rare Carat's existing analytics stack — no new analytics infrastructure required.