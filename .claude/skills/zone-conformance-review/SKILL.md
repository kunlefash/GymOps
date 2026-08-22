---
name: zone-conformance-review
description: Master review that checks a completed story against what the requirements actually say — acceptance criteria, PRD functional requirements, architecture invariants and NFR budgets. Gates the next story. Complements zone-code-review, which judges code quality rather than requirements conformance.
version: 1.0.0
triggers:
  keywords:
    - zone-conformance-review
    - master-review
    - requirements-review
    - conformance-check
  intents:
    - review_story_against_requirements
    - gate_story_completion
---

# Zone Conformance Review — the master review

`zone-code-review` asks *"is this code any good?"*. This skill asks a different
and harder question: **"is this the thing the requirements asked for?"**

Code can be clean, well-tested and completely wrong. A story can have passing
tests that assert the wrong behaviour. This review is the gate that catches that,
by checking the implementation against the documents that define done:

| Source | What it fixes |
| --- | --- |
| `epics.md` — the story's acceptance criteria | Whether each Given/When/Then actually holds |
| `prd.md` — the FRs the story claims | Whether the user-facing capability exists |
| `architecture.md` — the invariants | Whether the non-negotiable rules survived |
| `prd.md` — the NFRs | Whether the performance and security budgets hold |

**Input:** a story key (e.g. `1.2`) or an epic-and-story title.
**Output:** `###ZONE-CONFORMANCE-RESULT###{"status":"0","critical":0,"high":0,"unmet_acs":0}###ZONE-CONFORMANCE-RESULT###`

`status` is `0` only when there are no CRITICAL or HIGH findings **and** every
acceptance criterion is met with evidence. Anything else is `1`.

---

## Phase 0 — Resolve the story

1. Read `_bmad-output/planning-artifacts/epics.md`. Locate the story by key.
   Extract its title, user story, and **every** acceptance criterion verbatim.
2. Note the FRs its parent epic claims to cover.
3. Identify the diff under review: the story's feature branch against `main`, or
   the commits since the last conformance review if working on `main`.

If the story key does not resolve, stop and report it. Do not guess which story
was meant — reviewing the wrong requirements is worse than not reviewing.

## Phase 1 — Architecture invariants (mechanical)

Run the scanner:

```bash
python3 .claude/skills/zone-conformance-review/scripts/check_invariants.py \
  --repo-root /Users/mac/Documents/fitbase --diff-base main --json
```

It checks the rules `architecture.md` declares non-negotiable — tenant scoping
from JWT only, integer kobo money, auth guards in layouts not pages, no hard
deletes, the query-key factory, no raw fetch in components, tests outside `src/`,
no literal credentials.

Every CRITICAL here fails the review outright. These are not opinions: each one
names a specific way the system loses money, leaks across tenants, or destroys an
audit trail.

Drop `--diff-base` to sweep the whole repo rather than one story's changes.

## Phase 2 — Acceptance criteria (judgment)

This is the core of the review and cannot be automated.

For **each** acceptance criterion, produce one row:

| AC | Verdict | Evidence |
| --- | --- | --- |
| *Given… When… Then…* | MET / UNMET / PARTIAL | `file.ts:42` or the test that proves it |

Rules for this table:

- **Evidence is a file:line or a test name.** "Looks implemented" is not evidence.
  If you cannot point at the code that makes an AC true, it is UNMET.
- **A passing test is only evidence if it asserts the AC's actual claim.** A test
  named `sends OTP` that only checks a 200 status does not prove a code was sent.
  Read the assertion, not the test name.
- **PARTIAL is a real verdict.** An AC that holds for the happy path but not the
  error branch it explicitly describes is PARTIAL, not MET.
- **Do not accept scope reduction silently.** If the implementation deliberately
  defers part of an AC, that is UNMET with a note — the decision to descope
  belongs to the user, not the reviewer.

## Phase 3 — Functional requirements

For each FR the story claims: state whether the capability is reachable by the
user the FR names, and through what route or component.

An FR is not delivered because the API route exists. `FR15: staff can search
members by partial name or phone` needs the endpoint, the UI that calls it, and
the debounce that meets the NFR — otherwise it is partially delivered, and the
epic's FR coverage map is lying.

## Phase 4 — NFR spot checks

Only the NFRs the story plausibly touches. Check the mechanism, not a stopwatch:

- **≤300ms member search** — is there a composite index on `(businessId, name)`
  and `(businessId, phone)`? Is the input debounced?
- **≤500ms payment** — is the write a single transaction? Is the WhatsApp send
  decoupled through the outbox rather than awaited inline?
- **≤3s load / ≤1s repeat** — is anything heavy (QR scanner, charts) statically
  imported into a route that does not need it?
- **OTP 5/hour, 10-min single use** — enforced server-side, not just in the UI.
- **Idempotency** — do payment and check-in POSTs accept and honour an
  `idempotencyKey`? Without it the offline queue (Epic 11) will double-charge.
- **Tenant isolation** — is there a test that asserts gym A cannot read gym B?

## Phase 5 — Verdict

Report in this order:

1. **Verdict** — PASS or FAIL, one line, first.
2. **Unmet ACs** — the table rows that are not MET. Omit the section if empty.
3. **Invariant violations** — grouped by severity, each with file:line.
4. **FR coverage** — delivered / partial / not delivered.
5. **NFR risks** — with the mechanism that is missing.
6. **Notes** — anything true and useful that is not a finding, kept short.

Then emit the result marker.

### Gating

- **FAIL** → the story does not advance. Findings become tasks on the story file,
  in the same format `zone-code-review` produces, so the dev agent can pick them
  up directly.
- **PASS** → the story is done and the next one may start.

Do not soften a FAIL because the work is nearly there, and do not manufacture
findings to look thorough. A review that always passes and a review that always
finds something are equally useless — both stop carrying information.

## What this skill does not do

- **Code quality** — naming, duplication, structure. That is `zone-code-review`.
- **Fixing** — this review reports; the dev agent fixes. Keeping them separate is
  what stops a reviewer from rationalising its own code.
- **Re-running the suite** — CI already did. Read its result; do not re-litigate
  a green build.
