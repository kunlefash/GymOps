# Step 6b: Design System → Stitch Sync

## PURPOSE

Automatic sync step that seeds `.stitch/DESIGN.md` with the design system framework choice and any brand context established so far. Runs silently after step-06 saves, before step-07 loads.

This step ensures Stitch has early context about the design direction even before full visual tokens are defined in step-08.

## MANDATORY EXECUTION RULES (READ FIRST):

- 🤖 THIS IS AN AUTOMATED STEP — no user interaction required
- 📖 CRITICAL: ALWAYS read the complete step file before taking any action
- ⏱️ Execute quickly — do not present menus or wait for input
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`
- 📢 Inform the user briefly about what is happening (one short sentence)

## SKIP CONDITIONS:

Skip this entire step silently and proceed directly to step-07 if ANY of the following are true:
- `{stitch_available}` is false or not set
- The UX spec does not contain a "Design System Foundation" section (step-06 output was empty or not saved)

If skipping, load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-07-defining-experience.md` immediately.

## EXECUTION SEQUENCE:

### 1. Read Design System Foundation

Read `{planning_artifacts}/ux-design-specification.md` and extract the content under `## Design System Foundation` (the section appended by step-06). Capture:

- **Framework choice** — Custom, Established (which one), or Themeable (which one)
- **Rationale** — why this framework was chosen
- **Brand context** — any brand colors, fonts, or guidelines mentioned in the rationale or customization strategy
- **Platform** — from earlier steps (step-03) if present in frontmatter or document

### 2. Seed or Update `.stitch/DESIGN.md`

**If `.stitch/DESIGN.md` does NOT exist:**

Create it with a preliminary seed structure:

```markdown
# Design System: {project_name}

**Source:** _bmad-output/planning-artifacts/ux-design-specification.md
**Status:** Preliminary — will be refined after Visual Foundation (step 8) and Design Direction (step 9)

## 1. Visual Theme & Atmosphere

{Infer atmosphere from the design system framework choice and any brand context. For example:
- Custom system + fitness/gym → "Energetic, motivating, with bold typography and a high-contrast palette"
- Themeable (Tailwind) + consumer → "Modern, flexible, with utility-first approach enabling rapid iteration"
- Established (Material) + enterprise → "Structured, familiar, leveraging Material Design's proven patterns"}

## 2. Color Palette & Roles

{If any brand colors were mentioned in the design system rationale or customization strategy, list them here with their roles. Otherwise:}

> Palette will be defined in Visual Foundation (step 8). Brand guidelines noted so far:
> - {Any brand colors mentioned, or "None specified yet"}

## 3. Typography Rules

{If font preferences were mentioned, capture them. Otherwise:}

> Typography will be defined in Visual Foundation (step 8). Framework defaults:
> - {Framework-specific font defaults if applicable, e.g., "Material Design: Roboto", "Tailwind: system font stack"}

## 4. Component Stylings

> Component styling details will be defined in Visual Foundation (step 8) and refined in Design Directions (step 9).
> Framework: {chosen framework} — {key component characteristics of that framework}

## 5. Layout Principles

> Layout principles will be defined in Visual Foundation (step 8).
> Framework defaults: {any layout conventions from the chosen framework}

## 6. Design System Notes for Stitch Generation

> **STATUS: PRELIMINARY** — This section will be populated with complete tokens after Visual Foundation (step 8).
>
> Framework: {framework choice}
> Platform: {platform from UX spec, if known}
> Brand context: {any brand guidelines captured so far}
```

**If `.stitch/DESIGN.md` ALREADY exists:**

Read the existing file. Update only the sections that have new information from step-06:
- Update Section 1 (atmosphere) if the framework choice informs it
- Update Section 2 if brand colors were mentioned
- Update Section 3 if font preferences were mentioned
- Add a note in Section 6 about the framework choice
- Preserve all existing content that is more specific than the new seed data (do not overwrite richer content with placeholder text)

### 3. Ensure Directory Structure

Create `.stitch/` and `.stitch/designs/` directories if they do not exist.

### 4. Brief Status Update

Inform the user (in Sally's voice, one sentence):

> "I've seeded your Stitch design system with the {framework name} framework context — this will grow richer as we define your visual foundation next!"

### 5. Update Frontmatter and Proceed

- Update the UX spec frontmatter: append `step-06b` to the end of `stepsCompleted` array
- Load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-07-defining-experience.md`

## SUCCESS METRICS:

- `.stitch/DESIGN.md` exists with at least framework context seeded
- `.stitch/` and `.stitch/designs/` directories exist
- UX spec frontmatter updated with step-06b
- Step completed in under 10 seconds of processing (no user interaction)
- Proceeds to step-07 automatically

## FAILURE MODES:

- Writing `.stitch/DESIGN.md` fails → warn user, skip, proceed to step-07
- UX spec cannot be read → skip, proceed to step-07
- Never block the workflow — this step is supplementary, not critical

## NEXT STEP:

Load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-07-defining-experience.md` immediately after completion or skip.
