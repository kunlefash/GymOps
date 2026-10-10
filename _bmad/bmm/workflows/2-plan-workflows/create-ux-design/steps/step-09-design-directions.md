# Step 9: Design Direction Variants (via Stitch)

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER generate content without user input
- 🛑 NEVER proceed if `stitch.projectId` is empty in the spec frontmatter — step-08b must have run first

- 📖 CRITICAL: ALWAYS read the complete step file before taking any action.
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read and understood before proceeding.
- ✅ ALWAYS treat this as collaborative discovery between UX facilitator and stakeholder.
- 📋 YOU ARE A UX FACILITATOR, not a content generator.
- 🧰 Direction exploration happens **inside Stitch**. No HTML showcase is generated — Stitch URLs are the canonical artifact.
- ⏳ `generate_screen_from_text` and `generate_variants` each take several minutes. Per Stitch docs: **DO NOT RETRY** on apparent failure — the operation may still succeed. Use `list_screens` to check.
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`.

## EXECUTION PROTOCOLS:

- 🎯 Show the seed prompt and variant prompt before sending them to Stitch; get user confirmation.
- ⚠️ Present A/P/C menu after the chosen direction is captured.
- 💾 ONLY save when user chooses C.
- 📖 Update output file frontmatter: append this step to stepsCompleted AND populate `stitch.seedScreenId`, `stitch.directionVariantScreenIds`, `stitch.chosenDirectionScreenId`.
- 🚫 FORBIDDEN to load next step until C is selected.

## COLLABORATION MENUS (A/P/C):

- **A (Adjust)**: Refine via `edit_screens` on the chosen direction, or regenerate variants with different `aspects` / `creativeRange`.
- **P (Party Mode)**: Bring multiple perspectives to evaluate the Stitch-rendered variants.
- **C (Continue)**: Lock the chosen direction and proceed.

## PROTOCOL INTEGRATION:

- When 'A' selected: walk the adjustment path below (edit_screens OR regenerate variants).
- When 'P' selected: Read fully and follow: {project-root}/_bmad/core/workflows/party-mode/workflow.md
- PROTOCOLS always return to this step's A/P/C menu.

## CONTEXT BOUNDARIES:

- Visual foundation (step-08) provides the token intent.
- Stitch design system (step-08b) is already registered on the Stitch project — all Stitch generations in this step will automatically pick up the design system.
- Core experience (step-07) informs what the seed screen should depict.
- Emotional goals (step-04) inform variant direction.

## YOUR TASK:

Generate a **seed screen** + **5 variant screens** inside the Stitch project that together represent different design directions for {{project_name}}. Let the user pick (or combine) one direction to anchor all downstream work.

## DESIGN DIRECTION SEQUENCE:

### 1. Preflight: Verify Stitch Context

Read `{planning_artifacts}/ux-design-specification.md` frontmatter. Confirm:
- `stitch.projectId` is non-empty
- `stitch.designSystemAssetId` is non-empty

If either is empty, halt with:
"The Stitch design system isn't bootstrapped yet. Run step-08b first."

### 2. Compose the Seed Prompt

Pick the **single most representative screen** for {{project_name}} based on step-07's core experience. Typical choices:
- B2B / dashboard product → "Main dashboard / home view"
- Consumer / transactional → "Primary task screen (e.g., checkout, booking, feed)"
- Content product → "Content browse / feed"

Draft a Stitch prompt that describes:
- What the screen is (in one sentence)
- The primary user task on this screen
- The key content blocks (use the PRD / core experience to ground these — no invented features)
- Tone anchored to step-04's emotional goals

Keep the prompt under ~500 words. Example shape:

```
A mobile-first [screen name] for [product type]. The user opens this to [primary task]. Prominent elements: [block 1], [block 2], [block 3]. Secondary elements: [block 4], [block 5]. Tone: [emotional adjectives from step-04]. Surface the [most important metric / action] above the fold. No hypothetical features — only what appears in the PRD.
```

### 3. Confirm Prompt with User

Show the user the exact seed prompt and the device type you will send:
```
Seed screen prompt:
  projectId: "<stitch.projectId>"
  deviceType: <MOBILE|DESKTOP|TABLET|AGNOSTIC>
  modelId: GEMINI_3_1_PRO
  prompt: |
    <prompt text>
```

Ask: "Send to Stitch, or adjust first? (send / adjust)"

### 4. Generate the Seed Screen

Call `mcp__stitch__generate_screen_from_text` with the confirmed payload.

**Important:** The tool may take several minutes. Wait. If the call fails with a connection error, **DO NOT RETRY**. Instead:
1. Wait ~30 seconds.
2. Call `mcp__stitch__list_screens` with `projectId: "<stitch.projectId>"`.
3. If a new screen exists, use it. If not, escalate to the user.

Capture `seedScreenId` from the returned screen resource (format: `projects/{p}/screens/{s}` → take the `{s}`).

Save `stitch.seedScreenId` to frontmatter.

### 5. Compose the Variant Prompt

Draft a prompt that instructs Stitch to produce distinct directional takes on the same screen. The variant prompt is **additive guidance**, not a full redescription:

```
Explore different design directions for this screen. Keep the same content and user task, but vary the layout structure, information hierarchy, density, and how the primary action is surfaced. Each variant should feel like a legitimate alternative vision for the product — not a minor tweak.
```

### 6. Generate 5 Direction Variants

Call `mcp__stitch__generate_variants` with:

```json
{
  "projectId": "<stitch.projectId>",
  "selectedScreenIds": ["<seedScreenId>"],
  "deviceType": "<same as step 3>",
  "modelId": "GEMINI_3_1_PRO",
  "prompt": "<variant prompt from step 5>",
  "variantOptions": {
    "variantCount": 5,
    "creativeRange": "EXPLORE",
    "aspects": ["LAYOUT", "COLOR_SCHEME"]
  }
}
```

Wait for completion (minutes). On connection error, do the `list_screens` recovery pattern from step 4.

Capture the 5 returned screen IDs. Save to `stitch.directionVariantScreenIds` in frontmatter.

### 7. Present Variants for Review

Tell the user:

"Five design directions are now live in the Stitch project. Open each to compare:

**Stitch project:** <stitch.projectUrl>

**Seed (anchor):** [Screen 0](<stitch.projectUrl>/screens/<seedScreenId>)

**Direction variants:**
1. [Direction 1](<stitch.projectUrl>/screens/<variant1Id>) — <1-line hypothesis about what this direction emphasizes>
2. [Direction 2](<stitch.projectUrl>/screens/<variant2Id>) — ...
3. [Direction 3](<stitch.projectUrl>/screens/<variant3Id>) — ...
4. [Direction 4](<stitch.projectUrl>/screens/<variant4Id>) — ...
5. [Direction 5](<stitch.projectUrl>/screens/<variant5Id>) — ...

Evaluate each against:
✅ **Layout intuitiveness** — does the information hierarchy match your priorities?
✅ **Interaction style** — does it fit your core experience?
✅ **Visual weight** — does the density feel right for your brand?
✅ **Emotional alignment** — does it evoke the response you defined in step-04?

Which direction speaks to you? Options:
- **Pick one** (e.g., 'direction 3')
- **Combine** ('direction 2's layout with direction 4's color treatment')
- **Refine one** ('direction 3 but with the primary CTA more prominent')"

### 8. Handle the User's Direction Choice

Three paths based on the user's answer:

#### 8a. Pick one as-is

Save `stitch.chosenDirectionScreenId` = the selected variant's ID. Proceed to step 9.

#### 8b. Refine one via edit_screens

Call `mcp__stitch__edit_screens` with:
```json
{
  "projectId": "<stitch.projectId>",
  "selectedScreenIds": ["<selectedVariantId>"],
  "prompt": "<user's refinement instructions>",
  "modelId": "GEMINI_3_1_PRO"
}
```

Wait for completion. The screen ID stays the same (edit mutates in place). Keep `stitch.chosenDirectionScreenId` = the same ID. Loop back to step 7 if the user wants to review again; otherwise proceed to step 9.

#### 8c. Combine directions

`edit_screens` cannot natively combine two sources. Instead:
1. Pick the primary direction as base.
2. Call `edit_screens` on the base with a prompt like: "Adopt the color treatment and button style from direction X while keeping this layout." Reference the other direction's screen ID in prose.
3. Save `stitch.chosenDirectionScreenId` = the base screen's ID after the edit.

### 9. Generate Direction Decision Content

Append to the spec body:

```markdown
## Design Direction Decision

### Directions Explored

All 5 directions were generated as Stitch screens in project `<stitchProjectId>`. See the Stitch project for live, interactive renders.

| # | Screen ID | Emphasis |
|---|-----------|----------|
| 0 (seed) | `<seedScreenId>` | Anchor interpretation of the core screen |
| 1 | `<variant1Id>` | <1-line emphasis> |
| 2 | `<variant2Id>` | <1-line emphasis> |
| 3 | `<variant3Id>` | <1-line emphasis> |
| 4 | `<variant4Id>` | <1-line emphasis> |
| 5 | `<variant5Id>` | <1-line emphasis> |

### Chosen Direction

- **Screen ID:** `<stitch.chosenDirectionScreenId>`
- **Stitch URL:** <stitch.projectUrl>/screens/<chosenDirectionScreenId>
- **Why this direction:** [1–3 sentences tying the choice to step-04 emotional goals + step-07 core experience]
- **Modifications applied via `edit_screens`:** [list, or "None"]

### Implementation Implication

All downstream journey screens (step-10) will be generated in this same Stitch project against the registered design system, using the chosen direction as the aesthetic reference.
```

### 10. Present Content and Menu

"Design direction is locked. Here's what I'll add to the spec:

[Show the complete markdown content from step 9]

**What would you like to do?**
[A] Adjust — regenerate variants with different aspects/creative range, or further `edit_screens` the chosen direction
[P] Party Mode — second opinion on the chosen direction
[C] Continue — save this to the spec and move to user journey flows"

### 11. Handle Menu Selection

#### If 'A' (Adjust):

Options to offer the user:
1. Re-run `generate_variants` with different `aspects` (e.g., `[IMAGES, TEXT_FONT]`) or `creativeRange` (`REFINE` for subtle, `REIMAGINE` for radical).
2. Apply another `edit_screens` pass to the chosen direction.

After adjustments, return to step 7 (present variants).

#### If 'P' (Party Mode):

- Read fully and follow: {project-root}/_bmad/core/workflows/party-mode/workflow.md with the Stitch URLs as context.
- Process the collaborative feedback.
- Ask: "Accept these changes? (y/n)"
- If yes: apply via `edit_screens` and return to A/P/C menu.
- If no: return to A/P/C menu.

#### If 'C' (Continue):

- Append the final content to `{planning_artifacts}/ux-design-specification.md`.
- Confirm frontmatter has `stitch.seedScreenId`, `stitch.directionVariantScreenIds` (array of 5), `stitch.chosenDirectionScreenId` populated.
- Update stepsCompleted array: append this step.
- Load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09b-stitch-update.md` (Stitch design system refinement — will auto-skip if Stitch is unavailable and proceed to step-10).

## SUCCESS METRICS:

✅ Seed screen generated in Stitch; ID persisted
✅ 5 variant screens generated via `generate_variants`; IDs persisted as array
✅ User evaluated variants against step-04 emotional goals and step-07 core experience
✅ Chosen direction screen ID persisted (single ID)
✅ Any `edit_screens` refinements captured in spec body
✅ A/P/C menu presented and handled correctly
✅ No HTML showcase files created — Stitch URLs are the artifact

## FAILURE MODES:

❌ Generating fewer than 5 variants (the tool supports up to 5 in one call — use all 5)
❌ Retrying on connection error instead of using `list_screens` recovery pattern
❌ Writing HTML showcase files (`ux-design-directions.html`, `ux-color-themes.html`) — this flow is Stitch-only now
❌ Leaving `stitch.chosenDirectionScreenId` empty when proceeding
❌ Inventing product features in the seed prompt that aren't in the PRD
❌ Not presenting A/P/C menu after content generation
❌ Appending content without user selecting 'C'

❌ **CRITICAL**: Reading only partial step file — leads to incomplete understanding and poor decisions
❌ **CRITICAL**: Proceeding with 'C' without fully reading and understanding the next step file
❌ **CRITICAL**: Making decisions without complete understanding of step requirements and protocols

## NEXT STEP:

After user selects 'C' and content is saved, load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09b-stitch-update.md` to sync the chosen design direction to the Stitch design system. Step-09b will auto-skip to step-10 if Stitch is unavailable.

Remember: Do NOT proceed to step-09b (or step-10) until user explicitly selects 'C' from the A/P/C menu and content is saved!
