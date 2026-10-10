# Step 9b: Design Direction → Stitch Design System Refinement

## PURPOSE

Automatic sync step that refines `.stitch/DESIGN.md` with the finalized design direction choices from step-09. After the user selects their preferred design direction (or combination of directions), this step updates the Stitch design system to reflect those specific visual decisions.

This is the second leg of design system bidirectionality: UX spec visual decisions flow into Stitch's source of truth, ensuring all subsequent screen generation matches the approved direction.

## MANDATORY EXECUTION RULES (READ FIRST):

- 🤖 THIS IS AN AUTOMATED STEP — no user interaction required
- 📖 CRITICAL: ALWAYS read the complete step file before taking any action
- ⏱️ Execute quickly — do not present menus or wait for input
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- 📢 Inform the user briefly about what is happening (one short sentence)

## SKIP CONDITIONS:

Skip this entire step silently and proceed directly to step-10 if ANY of the following are true:
- `{stitch_available}` is false or not set
- `.stitch/DESIGN.md` does not exist (step-06b was skipped)
- The UX spec does not contain a "Design Direction Decision" section (step-09 output was empty)

If skipping, load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-10-user-journeys.md` immediately.

## EXECUTION SEQUENCE:

### 1. Read Design Direction Decision

Read `{planning_artifacts}/ux-design-specification.md` and extract:

- **Chosen Direction** — which direction (or combination) the user selected
- **Design Rationale** — why this direction was chosen
- **Key Visual Characteristics** — layout approach, visual weight, color application, navigation pattern, component usage, brand alignment notes
- **Implementation Approach** — any specific implementation decisions

Also read the **Visual Design Foundation** section (from step-08) if present, to get the full token set.

### 2. Read Current `.stitch/DESIGN.md`

Read the existing `.stitch/DESIGN.md` to understand its current state (preliminary seed from step-06b, or full version from step-08b after the Stitch project was created).

### 3. Refine `.stitch/DESIGN.md`

Update `.stitch/DESIGN.md` with the design direction specifics. For each section:

**Section 1 — Visual Theme & Atmosphere:**
- Enrich the atmosphere description with the chosen direction's character
- Include the visual weight preference (light/dense/balanced)
- Add the layout approach keywords (e.g., "card-based with generous whitespace")
- Reference the rationale for the direction choice

**Section 2 — Color Palette & Roles:**
- If the chosen direction specified different color applications than the base palette, update the usage descriptions
- If specific color combinations were highlighted in the direction, note them
- Preserve all hex values — only refine the role descriptions and usage context

**Section 3 — Typography Rules:**
- If the chosen direction uses typography differently (e.g., larger headings, different weight distribution), capture those adjustments
- Update hierarchy descriptions to match the chosen direction's visual weight

**Section 4 — Component Stylings:**
- Update component descriptions to match the chosen direction:
  - Button style (rounded, sharp, pill, ghost, etc.)
  - Card treatment (elevated, flat, bordered, etc.)
  - Navigation pattern (sidebar, top bar, bottom nav, etc.)
  - Input/form style adjustments
- Include interaction style notes (hover states, transitions, animations)

**Section 5 — Layout Principles:**
- Update density description to match the chosen direction
- Capture spacing rhythm and visual hierarchy decisions
- Note responsive behavior preferences from the direction choice

**Section 6 — Design System Notes for Stitch Generation:**
- Rebuild the prompt block with finalized values:
  - Update atmosphere keywords from the chosen direction
  - Include specific layout/density preferences
  - Add component style descriptors
  - Remove the `STATUS: PRELIMINARY` flag if step-08b has already populated full tokens
  - If step-08b hasn't fired yet (no full tokens), update the preliminary block with direction-specific context

### 4. Update Stitch MCP Design System (if bootstrapped)

**Only if `stitch.projectId` is non-empty in the spec frontmatter** (meaning step-08b has already created a Stitch project and design system):

Check if the design direction choice implies changes to Stitch design system parameters:

- If the direction changes the color application → update `overridePrimaryColor`, `overrideSecondaryColor`
- If the direction changes roundness/shape language → update `roundness`
- If the direction changes color mood → update `colorVariant`

If any parameters changed, call `mcp__stitch__update_design_system` with:
- `name`: `"assets/{stitch_design_system_asset_id}"`
- `projectId`: `"{stitch_project_id}"`
- `designSystem`: updated theme parameters

### 5. Update UX Spec Cross-Reference

If the UX spec already has a "Stitch Design System" subsection (added by step-08b), append a note:

```markdown

**Design Direction Applied:** {chosen direction name/number} — DESIGN.md updated with direction-specific visual characteristics on {date}.
```

### 6. Brief Status Update

Inform the user (in Sally's voice, one sentence):

> "Your design direction choice has been synced to the Stitch design system — all future screen generation will reflect your {chosen direction} vision!"

### 7. Update Frontmatter and Proceed

- Update the UX spec frontmatter: append `step-09b` to the end of `stepsCompleted` array
- Load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-10-user-journeys.md`

## SUCCESS METRICS:

- `.stitch/DESIGN.md` updated with design direction visual characteristics
- Section 6 prompt block reflects the chosen direction
- Stitch MCP design system updated (if `stitch.projectId` is populated in frontmatter)
- UX spec frontmatter updated with step-09b
- Step completed quickly (no user interaction)
- Proceeds to step-10 automatically

## FAILURE MODES:

- `.stitch/DESIGN.md` read/write fails → warn user, skip, proceed to step-10
- Stitch MCP update fails → warn user (design system may be slightly out of sync), continue
- UX spec cannot be read → skip, proceed to step-10
- Never block the workflow — this step is supplementary, not critical

## NEXT STEP:

Load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-10-user-journeys.md` immediately after completion or skip.
