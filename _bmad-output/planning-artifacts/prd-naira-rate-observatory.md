---
stepsCompleted: [step-01-init, step-02-discovery, step-02b-vision, step-02c-executive-summary, step-03-success, step-04-journeys, step-05-domain, step-09-functional, step-10-nonfunctional, step-12-complete]
inputDocuments:
  - /Users/mac/Downloads/naira-rate-observatory-brief.md
workflowType: 'prd'
classification:
  projectType: web_app
  domain: fintech_adjacent_market_data
  complexity: medium
  projectContext: greenfield
---

# Product Requirements Document - Naira Rate Observatory

**Author:** Adekunle
**Date:** 2026-07-25

---

## Executive Summary

There is no single Naira rate — the official rate, the parallel rate, the crypto-implied rate, and what a remittance recipient actually receives are four different numbers, and nobody publishes the divergence between them as a continuous, sourced, timestamped series. Naira Rate Observatory is that record: a scheduled collector reads USD/NGN signals from CBN, FMDQ, local crypto exchanges, offshore P2P venues, parallel-market aggregators, and remittance apps six times a day, appends every observation (including failures) to an append-only store, and republishes two JSON files that drive a static site. The product is the archive, not the site — value compounds with the length of the history, so the collector must start running before any front end exists.

### What Makes This Special

The differentiator is discipline, not novelty: the collector never writes a value it did not observe, gaps render as gaps rather than being smoothed over, every source is tagged with a published confidence tier on every row, and the full methodology is public before the first data point ships. That rule is what separates this from every existing rate scraper, and it's enforced in code, not left to editorial promise. The signature output — a horizontal spectrum plotting every source's rate on one axis with a bracket showing the spread — makes market fragmentation a physical distance instead of a statistic, which is what makes it worth screenshotting and sharing.

## Project Classification

- **Project Type:** web_app — static site (no SPA framework, no server, no database) generated from two JSON files, backed by a scheduled collector job
- **Domain:** fintech-adjacent market-data publishing — touches FX/payments subject matter but performs no transactions, holds no funds, and is not a regulated financial service
- **Complexity:** medium — the difficulty is reputational/political (see the AbokiFX and Binance NGN P2P precedents), not compliance-driven
- **Project Context:** greenfield

---

## Success Criteria

### User Success

A sceptical reader — a payments professional, a journalist, a remittance user comparing apps — can land on the site and within seconds see how wide the Naira market currently is, who is quoting what, and how confident each number is. They can click through to the methodology and the raw JSON and verify any published figure themselves. Success is a reader saying "I didn't know it was that wide" and sharing the spectrum chart.

### Business Success

- **30 days:** Collector has run six times a day without a missed cycle it didn't honestly record as a failure; `METHODOLOGY.md` is public; at minimum Tier A (CBN, FMDQ) plus two Tier B sources are live.
- **90 days:** Full source set (Tiers A–C) collecting; static site live with spectrum, 30-day chart, and observations table; first monthly post published with a real number (e.g., "the widest single-moment gap over 30 days was X%").
- **12 months:** A standing monthly post cadence; the dataset is cited or referenced by at least one external party (press, researcher, or payments company) as a source, which is the signal the record has become a reference rather than a toy.

### Technical Success

- Zero smoothed-over gaps: every failed collection produces a failure record, never a carried-forward value.
- Every published figure is reproducible from the raw archive (raw response body stored and hashed per observation).
- Six commits/day sustained indefinitely without manual intervention under normal operating conditions.

### Measurable Outcomes

- Collector uptime: percentage of the six daily scheduled runs per source that produced either a valid observation or an honest failure record (target: 100% — a missed cron run is a defect).
- Source count live vs. Tier A/B/C target set.
- Intraday dispersion (max − min across all channels) tracked as a first-class metric from day one, since it's the differentiated data point nobody else publishes.

## Product Scope

### MVP - Minimum Viable Product

- Collector for CBN, FMDQ, and two exchange order books (Tier A + partial Tier B), running on the six-times-daily cadence, committing append-only rows to the store with raw response hashing.
- `METHODOLOGY.md` published alongside the first commits, before any front end exists.
- The rule that a failed source writes a failure record, never a carried-forward or interpolated value, enforced in the collector itself.

### Growth Features (Post-MVP)

- Remaining Tier B/C sources: remaining local exchanges, offshore P2P, parallel-market aggregators, and all five remittance apps (fixed $500 test amount, fixed US→Nigeria bank-payout corridor, promo flag).
- Static site: masthead with live collection timestamp, statement line, the spectrum (signature visual), 30-day divergence chart with channel toggles, observations table, footer with disclaimer and raw JSON links.
- Failure alerting so a broken collector is caught quickly rather than silently degrading the record.

### Vision (Future)

- Additional corridors beyond US→Nigeria (GBP, EUR) as separate tracked rows.
- Monthly post cadence sustained for 12+ months, with the dataset referenced externally as a citation-grade source on Naira market fragmentation.

---

## User Journeys

### The Sceptical Reader (Primary — Success Path)

Amara is a payments analyst who has seen "the Naira gap" mentioned in a dozen LinkedIn posts with no source. She lands on Naira Rate Observatory from a shared link. The masthead shows the collection timestamp in WAT and a source count — not "now," because the page never claims freshness it can't back up. The statement line tells her the current spread as a percentage. The spectrum shows her, physically, how far apart the CBN rate sits from the street rate and the remittance-effective rate at that exact moment. She scrolls to the observations table, finds the CBN row, and checks its age-since-last-return — it's fresh. She clicks through to the raw JSON and confirms the number herself. She screenshots the spectrum and shares it. This journey reveals: masthead timestamp logic, statement line computation, the spectrum visualization, the observations table, and raw JSON export.

### The Data Journalist (Primary — Edge Case)

Femi is writing a piece on remittance pricing and needs a specific number: the effective spread the Send App corridor showed over the last month. He opens the 30-day divergence chart, isolates the remittance-effective line via the legend toggle, and notices a gap in the series — a day the collector failed to reach the source. The chart renders it as a visible break, not a smoothed line, which is exactly what makes him trust the rest of the series. He reads `METHODOLOGY.md` to confirm the $500 test amount and bank-payout corridor rules before quoting a number in his article, and cites the promo flag rule when he notices one flagged row. This journey reveals: legend-toggleable multi-line chart, gap rendering, methodology document accessibility, and promo-marker visibility in the underlying data.

### The Collector Operator / Maintainer (Secondary — Operations)

Adekunle runs the scheduled job. At 04:00 WAT the pre-dawn collection cycle fires; one exchange API times out. The collector writes a failure record — source ID, timestamp, error — rather than retrying indefinitely or reusing the last good value. The append-only store gets a new row either way. Six hours later Adekunh checks the observations table and sees that source's age-since-last-return flagged stale (>8 hours). He investigates, fixes the credential issue, and the next cycle resumes clean. This journey reveals: the append-only data model, the never-interpolate rule enforced at the collector level, staleness flagging per source, and the git-commit-as-audit-trail architecture.

### API / Data Consumer

A researcher wants to build their own chart from the raw data rather than trust the site's rendering. They pull the two published JSON files directly — no authentication, no rate limit beyond static hosting — and recompute the parallel premium and crypto-implied rate themselves from the raw buy/sell/mid rows. This journey reveals: the two-JSON-file architecture with no front-end-only logic, and the requirement that every derived metric be recomputable from the raw published data.

### Journey Requirements Summary

These journeys require: a timestamp-honest masthead, a single-axis spectrum visualization, a legend-toggleable multi-line chart with true gap rendering, a sortable observations table with per-source age/staleness, a public methodology document, raw JSON export with no logic hidden in the front end, an append-only collector with an enforced no-interpolation rule, and per-source failure/staleness tracking.

---

## Domain Requirements

Given the fintech-adjacent, reputationally sensitive nature of this domain (the AbokiFX 2021 CBN dispute and the 2024 Binance NGN P2P episode are the cautionary precedents cited in the brief), the following requirements apply:

- The product must publish **observed data with sources cited**, never a single quotable "the rate."
- No single headline number may be presented in a way that could be read as a benchmark or pricing reference.
- Framing is explicit and consistent: "research on market fragmentation," never a pricing service, and never using "black market" or similar loaded terminology (product is named neutrally: Naira Rate Observatory).
- Commentary accompanying the data is descriptive, not prescriptive about policy.
- Remittance app sources — including Flutterwave's Send App — receive identical test amount, corridor, and disclosure treatment as every other listed provider, with the rule stated in the public methodology before data collection begins, given the author's employment context in this exact sector.

---

## Functional Requirements

### Data Collection

- FR1: The collector can read USD/NGN rate signals from CBN and FMDQ (Tier A sources) on the six-times-daily cadence.
- FR2: The collector can read order-book data (bid, ask, depth) from local crypto exchanges via public REST APIs (Tier B).
- FR3: The collector can read ad-level NGN quotes from offshore P2P venues via semi-public endpoints (Tier B).
- FR4: The collector can read parallel-market aggregator quotes at low confidence (Tier C).
- FR5: An operator can manually enter a remittance app's effective rate when no automated endpoint exists, and the system records it as manual with a Tier C confidence marker.
- FR6: The collector writes a failure record (source, timestamp, error) when a source cannot be read, and never carries forward or interpolates a prior value.
- FR7: The collector stores every raw response body and a hash of it alongside the parsed observation, so any published figure can be recomputed from source later.
- FR8: The collector runs on a fixed six-times-daily UTC cron schedule anchored to the Nigerian trading day.

### Rate Normalization & Derived Metrics

- FR9: The system computes and stores buy, sell, and mid rates per source, per collection cycle.
- FR10: A source that publishes only one rate is stored and labeled as mid rather than assumed to be a sell rate.
- FR11: The system computes the parallel premium (street mid over official mid) as a percentage.
- FR12: The system computes the crypto-implied rate as USDT/NGN ÷ USDT/USD.
- FR13: The system computes the remittance effective spread (recipient NGN per sender USD versus P2P mid at the same timestamp).
- FR14: The system computes intraday dispersion (highest minus lowest observed rate across all channels at a single collection moment).
- FR15: The system applies volume-weighted averaging across the first ~5m of order book depth rather than using top-of-book quotes.
- FR16: The system enforces a minimum liquidity threshold before a source's quote counts as a valid observation.
- FR17: Every remittance app quote is tested against a fixed $500 test amount and a fixed US-to-Nigeria bank-payout corridor.
- FR18: A promotional or first-transfer bonus rate is recorded with a promo marker rather than being excluded, and the standard (non-promo) rate is used in chart series.

### Data Storage & Audit

- FR19: All observations are stored as append-only rows; corrections are new rows that reference what they supersede, never in-place edits.
- FR20: Each stored row carries a published confidence tier (A/B/C) visible on every downstream display of that data.
- FR21: Each source's age since its last successful observation is tracked and can be flagged as stale (>8 hours) independent of the overall collection cadence.
- FR22: All rate storage is in UTC with WAT used for display and explicit labeling of both.
- FR23: The data store's history is committed to git, providing a tamper-evident audit trail of every published change.

### Site Publication

- FR24: A reader can view a masthead showing wordmark, current source count, and the collection timestamp (never the deploy timestamp, never "now").
- FR25: If the collector has not run successfully, the masthead states that explicitly rather than silently showing stale data as current.
- FR26: A reader can view a one-line thesis statement plus a live-numbers sentence (rates observed, lowest, highest, spread percentage).
- FR27: A reader can view the spectrum: every source plotted as a labeled point (rate + name) on a single horizontal axis from cheapest to dearest, with a bracket showing the full spread.
- FR28: A reader can view a 30-day divergence chart with four toggleable lines (official, remittance effective, crypto-implied, street), where missing collections render as visible breaks, never bridged.
- FR29: A reader can view an observations table sorted low to high showing name, channel, tier, rate, difference from official, and age since last return, for every source.
- FR30: A reader can access a footer stating what the project is and is not, linking to `METHODOLOGY.md` and to the raw JSON files.
- FR31: A reader can download the two published JSON files directly, with no derived logic hidden only in the front end.
- FR32: The site renders usably on a mobile browser, since most link-shared traffic arrives from mobile.

### Methodology & Governance

- FR33: A reader can access a public `METHODOLOGY.md` document describing every methodology decision (side convention, depth weighting, liquidity minimum, time handling, no-interpolation rule) before or alongside the first published data.

## Non-Functional Requirements

### Reliability

- The collector must complete or honestly fail each of the six daily scheduled runs per source; a missed cron execution with no failure record is treated as a defect, not a degraded outcome.
- The append-only store must never lose a previously written row; corrections are additive only.

### Data Integrity

- Every published rate must be traceable to a stored raw response and its hash; recomputation of any historical figure from the raw archive must be possible without relying on any smoothed or interpolated intermediate value.
- Gaps in any time series must render as visible breaks in the UI, never bridged or estimated.

### Performance

- The static site must load and render the spectrum and 30-day chart on a typical mobile connection without a backend round-trip, since the site reads only pre-generated JSON files.

### Security & Trust

- No user authentication or payment handling exists anywhere in the product, since it collects only public market data; the primary trust risk is data integrity and framing, not access control.
- Every public-facing figure must carry a visible confidence tier so a reader can independently weight how much to trust it.

### Cost & Operability

- Architecture must run without a server or database bill (scheduled job → collector → static JSON → static host), keeping ongoing infrastructure cost near zero at the six-commits-a-day volume (~2,200 commits/year).

---

## Risks & Mitigations

- **Regulatory misreading risk** (per AbokiFX 2021 and Binance NGN P2P 2024 precedents): mitigated by publishing observed, sourced data rather than a single quotable rate, avoiding any headline number that could function as a benchmark, and using neutral, non-inflammatory naming and framing throughout.
- **Conflict-of-interest optics** (author's employment in this sector, Flutterwave's Send App among tracked sources): mitigated by applying identical methodology to all remittance apps and publishing that methodology before data collection begins.
