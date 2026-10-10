# Step 8b: Stitch Project & Design System Bootstrap

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER skip this step — every downstream step (9, 10, 14) depends on `stitch.projectId` and `stitch.designSystemAssetId` being set in the spec frontmatter.

- 📖 CRITICAL: ALWAYS read the complete step file before taking any action.
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read and understood before proceeding.
- 🧰 This step calls the **Stitch MCP** (`mcp__stitch__*` tools). The tools must be connected. If they are not available, halt and tell the user to enable the Stitch MCP server before re-running.
- ⏳ `generate_*` Stitch tools take several minutes. This step does NOT call them — it only creates the project and design system — but later steps will. Do not introduce retries.
- ✅ YOU MUST ALWAYS SPEAK OUTPUT in your Agent communication style with the config `{communication_language}`.

## EXECUTION PROTOCOLS:

- 🎯 Show the values you will send to Stitch before calling the tool and get user confirmation.
- ⚠️ Present A/P/C menu after Stitch objects are created.
- 💾 ONLY update frontmatter and load next step when user chooses C.
- 📖 Update output file frontmatter: append `step-08b-stitch-bootstrap` to stepsCompleted AND populate the `stitch:` block.
- 🚫 FORBIDDEN to load next step until C is selected.

## COLLABORATION MENUS (A/P/C):

- **A (Adjust)**: Re-run `create_design_system` with different values (font, roundness, color) if the user is unhappy with the Stitch output.
- **P (Party Mode)**: Not applicable to this step. Inform the user and re-present A/C.
- **C (Continue)**: Save the Stitch IDs and proceed to step-09.

## CONTEXT BOUNDARIES:

- Visual Foundation from step-08 provides: color system, typography, roundness/shape intent, spacing.
- This step translates those free-form decisions into the Stitch-constrained schema (enum fonts, enum roundness, single customColor hex seed).
- Nothing about user journeys or component strategy is needed here.

## YOUR TASK:

1. Create a Stitch project for this UX effort.
2. Build a Stitch `DesignSystem` from the visual foundation captured in step-08.
3. Register the design system in Stitch and save its asset ID.
4. Persist the Stitch identifiers into the spec frontmatter so later steps can use them.

## BOOTSTRAP SEQUENCE:

### 1. Announce the Step

"Now that we've locked the visual foundation, I'm going to mirror it into **Google Stitch** so every design direction and journey screen we generate from here stays consistent with the tokens you just approved.

I'll do three things:
1. Create a Stitch project named after `{{project_name}}`.
2. Build a Stitch design system from your visual foundation.
3. Save the Stitch identifiers into the UX spec so later steps can push screens into the same project.

Ready? (y/n)"

Halt until user confirms.

### 2. Verify Stitch MCP Availability

Check that the following tools are available in the current session:
- `mcp__stitch__create_project`
- `mcp__stitch__create_design_system`
- `mcp__stitch__update_design_system`
- `mcp__stitch__list_design_systems`

If any are missing, halt with:
"The Stitch MCP server is not connected in this session. Add the `stitch` MCP entry to your Claude configuration (http transport, `https://stitch.googleapis.com/mcp`, with `X-Goog-Api-Key`), restart Claude Code, then re-run this step."

### 3. Map Visual Foundation → Stitch DesignTheme

Read the **Visual Design Foundation** section of `{planning_artifacts}/ux-design-specification.md` that step-08 appended. Extract:

- `primary_color_hex` — the main brand/primary hex from the color system. If the foundation specifies a palette seed, use that; otherwise pick the dominant primary.
- `color_mode` — `LIGHT` unless step-08 clearly committed to a dark-first product.
- `headline_intent` — the vibe words for headlines (modern/classic/playful/etc).
- `body_intent` — readability vs. character for body.
- `roundness_intent` — sharp / moderate / rounded / pill.

Now translate to Stitch's enum-constrained schema using this mapping table. **If step-08 names a font that is in the enum, use it verbatim.** Otherwise apply the fallback:

| Step-08 intent | `headlineFont` | `bodyFont` |
|---|---|---|
| Modern / tech / neutral | `GEIST` | `INTER` |
| Editorial / trustworthy | `NEWSREADER` | `SOURCE_SERIF_FOUR` |
| Friendly / consumer | `PLUS_JAKARTA_SANS` | `DM_SANS` |
| Professional / enterprise | `IBM_PLEX_SANS` | `INTER` |
| Playful / expressive | `SPACE_GROTESK` | `MANROPE` |
| Luxury / premium | `EPILOGUE` | `EB_GARAMOND` |
| Fallback (unsure) | `GEIST` | `INTER` |

Roundness mapping:
| Step-08 intent | `roundness` |
|---|---|
| Sharp / serious / editorial | `ROUND_FOUR` |
| Balanced / default | `ROUND_EIGHT` |
| Friendly / approachable | `ROUND_TWELVE` |
| Fully pill / playful | `ROUND_FULL` |

Color variant: pick from the `colorVariant` enum (`MONOCHROME`, `NEUTRAL`, `TONAL_SPOT`, `VIBRANT`, `EXPRESSIVE`, `FIDELITY`, `CONTENT`, `RAINBOW`, `FRUIT_SALAD`). Default to `TONAL_SPOT` unless the foundation screams monochrome or vibrant.

### 4. Present the Mapping to the User

Show the user the exact payload you are about to send:

```
Stitch DesignSystem payload:
  displayName: "{{project_name}} — UX v1"
  theme:
    colorMode: <LIGHT|DARK>
    customColor: "<#hex>"
    colorVariant: <enum>
    headlineFont: <enum>
    bodyFont: <enum>
    labelFont: <enum or omit>
    roundness: <enum>
    designMd: |
      <1-2 paragraph summary derived from step-08's Visual Foundation
       — goes into Stitch as free-form design instructions>
    overridePrimaryColor: "<#hex — optional, matches customColor>"
    overrideSecondaryColor: "<#hex — optional if step-08 specified>"
    overrideTertiaryColor: "<#hex — optional if step-08 specified>"
```

Ask: "Send this to Stitch, or adjust first? (send / adjust)"

If `adjust`: collect changes and re-present until `send`.

### 5. Create the Stitch Project

Call `mcp__stitch__create_project` with:
```json
{ "title": "{{project_name}} — UX Design" }
```

Capture the returned project resource name (format: `projects/{id}`). Extract:
- `stitchProjectId` = the numeric id after `projects/`
- `stitchProjectResourceName` = the full `projects/{id}` string
- `stitchProjectUrl` = `https://stitch.withgoogle.com/project/{id}` (best-effort; if the tool returns a canonical URL, use that instead)

### 6. Create the Stitch Design System

Call `mcp__stitch__create_design_system` with:
```json
{
  "projectId": "<stitchProjectId>",
  "designSystem": {
    "displayName": "{{project_name}} — UX v1",
    "theme": { <payload from step 4> }
  }
}
```

Capture the returned asset resource name (format: `assets/{asset_id}`).
- `stitchDesignSystemAssetId` = the id after `assets/`

### 7. Apply/Register the Design System on the Project

Per the Stitch `create_design_system` tool docs, immediately call `mcp__stitch__update_design_system` with the same payload + `name: "assets/<assetId>"` + `projectId`. This registers and displays the design system on the project. If the MCP already registered it via `create`, this call is idempotent.

### 8. Persist Stitch IDs to Spec Frontmatter

Update `{planning_artifacts}/ux-design-specification.md` frontmatter `stitch:` block:

```yaml
stitch:
  projectId: "<stitchProjectId>"
  projectResourceName: "<stitchProjectResourceName>"
  projectUrl: "<stitchProjectUrl>"
  designSystemAssetId: "<stitchDesignSystemAssetId>"
  seedScreenId: ""
  chosenDirectionScreenId: ""
  directionVariantScreenIds: []
  journeyScreens: {}
```

Preserve all other frontmatter keys.

### 9. Append a Section to the Spec

Append this content to the body of the spec:

```markdown
## Stitch Design System

- **Stitch project:** [{{project_name}} — UX Design](<stitchProjectUrl>)
- **Project ID:** `<stitchProjectId>`
- **Design system asset ID:** `<stitchDesignSystemAssetId>`
- **Display name:** `{{project_name}} — UX v1`
- **Color mode:** `<LIGHT|DARK>` · **Custom color:** `<#hex>` · **Color variant:** `<enum>`
- **Headline font:** `<enum>` · **Body font:** `<enum>` · **Roundness:** `<enum>`

All design direction variants (step-09) and journey screens (step-10) are generated inside this Stitch project against this design system. The Stitch project is the canonical visual source of truth for {{project_name}}.
```

### 10. Present Content and Menu

Show the user:
- The URL of the Stitch project (clickable)
- The design system asset ID
- The appended spec section

"Stitch project and design system are live. Open the URL above to confirm it renders the way you expect.

**What would you like to do?**
[A] Adjust — tweak the design system (re-run `update_design_system` with new values)
[C] Continue — lock these IDs and move to design direction exploration in Stitch"

### 11. Handle Menu Selection

#### If 'A' (Adjust):

- Ask what to change (font, roundness, color, color variant).
- Call `mcp__stitch__update_design_system` with the same asset `name` and the modified theme.
- Return to step 10.

#### If 'C' (Continue):

- Confirm frontmatter and spec body are saved.
- Update stepsCompleted array: append `step-08b-stitch-bootstrap`.
- Load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md`.

## SUCCESS METRICS:

✅ Stitch project created and URL captured
✅ Stitch design system registered and asset ID captured
✅ `stitch:` frontmatter block populated
✅ "Stitch Design System" section appended to spec body
✅ User confirmed the Stitch output matches their visual foundation intent
✅ A/C menu presented and handled correctly

## FAILURE MODES:

❌ Calling `generate_screen_from_text` here — that's step-09's job, not this step's
❌ Hardcoding a font name outside the allowed enum — always map to the enum
❌ Skipping `update_design_system` after `create_design_system` — the Stitch tool docs require it
❌ Leaving `stitch.projectId` empty — step-09/10/14 will all fail if so
❌ Retrying Stitch calls that "fail due to connection error" — per tool docs, the operation may still have succeeded; instead call `list_projects` or `list_design_systems` to check

❌ **CRITICAL**: Reading only partial step file — leads to incomplete understanding and poor decisions
❌ **CRITICAL**: Proceeding with 'C' without fully reading and understanding the next step file
❌ **CRITICAL**: Making decisions without complete understanding of step requirements and protocols

## NEXT STEP:

After user selects 'C' and frontmatter + spec are saved, load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-09-design-directions.md` to generate design direction variants inside the Stitch project you just bootstrapped.

Remember: Do NOT proceed to step-09 until `stitch.projectId` and `stitch.designSystemAssetId` are both populated in the frontmatter!
