# Step 14: Workflow Completion

## MANDATORY EXECUTION RULES (READ FIRST):

- ✅ THIS IS A FINAL STEP - Workflow completion required

- 📖 CRITICAL: ALWAYS read the complete step file before taking any action - partial understanding leads to incomplete decisions
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read and understood before proceeding
- 🛑 NO content generation - this is a wrap-up step
- 📋 FINALIZE document and update workflow status
- 💬 FOCUS on completion, validation, and next steps
- 🎯 UPDATE workflow status files with completion information
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Show your analysis before taking any action
- 💾 Update the main workflow status file with completion information
- 📖 Suggest potential next workflow steps for the user
- 🚫 DO NOT load additional steps after this one

## TERMINATION STEP PROTOCOLS:

- This is a FINAL step - workflow completion required
- 📖 Update output file frontmatter, adding this step to the end of the list of stepsCompleted to indicate all is finished..
- Output completion summary and next step guidance
- Update the main workflow status file with finalized document
- Suggest potential next workflow steps for the user
- Mark workflow as complete in status tracking

## CONTEXT BOUNDARIES:

- Complete UX design specification is available from all previous steps
- Workflow frontmatter shows all completed steps
- All collaborative content has been generated and saved
- Focus on completion, validation, and next steps

## YOUR TASK:

Complete the UX design workflow, update status files, and suggest next steps for the project.

## WORKFLOW COMPLETION SEQUENCE:

### 1. Announce Workflow Completion

Inform user that the UX design is complete:
"🎉 **UX Design Complete, {{user_name}}!**

I've successfully collaborated with you to create a comprehensive UX design specification for {{project_name}}.

**What we've accomplished:**

- ✅ Project understanding and user insights
- ✅ Core experience and emotional response definition
- ✅ UX pattern analysis and inspiration
- ✅ Design system choice and implementation strategy
- ✅ Core interaction definition and experience mechanics
- ✅ Visual design foundation (colors, typography, spacing)
- ✅ Design direction mockups and visual explorations
- ✅ User journey flows and interaction design
- ✅ Component strategy and custom component specifications
- ✅ UX consistency patterns for common interactions
- ✅ Responsive design and accessibility strategy

**The complete UX design specification is now available at:** `{planning_artifacts}/ux-design-specification.md`

**Supporting Visual Assets (live in Google Stitch):**

- Stitch project: `<stitch.projectUrl>` (ID `<stitch.projectId>`)
- Registered design system: `assets/<stitch.designSystemAssetId>`
- Chosen direction screen: `<stitch.projectUrl>/screens/<stitch.chosenDirectionScreenId>`
- Per-journey Stitch screens (see `ux-stitch-artifacts.md`)

This specification — plus the live Stitch project — is now ready to guide visual design, implementation, and development."

### 2. Write ux-stitch-artifacts.md

Before updating status, consolidate all Stitch identifiers captured through steps 08b / 09 / 10 into a dedicated artifact file at `{planning_artifacts}/ux-stitch-artifacts.md`.

Read the `stitch:` block from `ux-design-specification.md` frontmatter and the per-journey Stitch IDs documented in the spec body. Then write:

```markdown
---
name: ux-stitch-artifacts
description: Stitch project, design system, and screen inventory for {{project_name}} UX
type: reference
---

# {{project_name}} — Stitch Artifacts

## Project

- **Project name:** {{project_name}} — UX Design
- **Project ID:** `<stitch.projectId>`
- **Project URL:** <stitch.projectUrl>
- **Project resource name:** `<stitch.projectResourceName>`

## Design System

- **Asset ID:** `<stitch.designSystemAssetId>`
- **Display name:** {{project_name}} — UX v1
- (See "Stitch Design System" section of `ux-design-specification.md` for theme token values.)

## Screens

### Seed

- `<stitch.seedScreenId>` — initial anchor interpretation of the core screen

### Direction Variants (all 5)

| # | Screen ID |
|---|-----------|
| 1 | `<variant1Id>` |
| 2 | `<variant2Id>` |
| 3 | `<variant3Id>` |
| 4 | `<variant4Id>` |
| 5 | `<variant5Id>` |

### Chosen Direction

- `<stitch.chosenDirectionScreenId>` — locked visual direction; all journey screens match its aesthetic

### Journey Screens

| Journey | Screen ID |
|---------|-----------|
| <journey 1 name> | `<id>` |
| <journey 2 name> | `<id>` |
| <journey 3 name> | `<id>` |

## How to use this artifact

- When implementing a journey, open the journey's Stitch screen alongside the UX spec — treat the Stitch screen as the visual source of truth and the spec as the behavioral/accessibility source of truth.
- When generating a NEW screen post-UX (e.g., during development), call `mcp__stitch__generate_screen_from_text` with `projectId: <stitch.projectId>` so the new screen inherits the registered design system.
- To refine any existing screen, use `mcp__stitch__edit_screens` with its screen ID.
```

Populate all `<...>` placeholders from the captured frontmatter. If any Stitch field in the frontmatter is empty, halt and tell the user which upstream step left the gap — do NOT write an artifacts file with missing IDs.

### 3. Workflow Status Update

Update the main workflow status file:

- Load `{status_file}` from workflow configuration (if exists)
- Update workflow_status["create-ux-design"] = "{default_output_file}"
- Save file, preserving all comments and structure
- Mark current timestamp as completion time

### 4. Suggest Next Steps

UX Design complete. Read fully and follow: `{project-root}/_bmad/core/tasks/help.md`

### 5. Final Completion Confirmation

Congratulate the user on the completion you both completed together of the UX.



## SUCCESS METRICS:

✅ UX design specification contains all required sections
✅ All collaborative content properly saved to document
✅ Workflow status file updated with completion information
✅ Clear next step guidance provided to user
✅ Document quality validation completed
✅ User acknowledges completion and understands next options

## FAILURE MODES:

❌ Not updating workflow status file with completion information
❌ Missing clear next step guidance for user
❌ Not confirming document completeness with user
❌ Workflow not properly marked as complete in status tracking
❌ User unclear about what happens next

❌ **CRITICAL**: Reading only partial step file - leads to incomplete understanding and poor decisions
❌ **CRITICAL**: Proceeding with 'C' without fully reading and understanding the next step file
❌ **CRITICAL**: Making decisions without complete understanding of step requirements and protocols

## WORKFLOW COMPLETION CHECKLIST:

### Design Specification Complete:

- [ ] Executive summary and project understanding
- [ ] Core experience and emotional response definition
- [ ] UX pattern analysis and inspiration
- [ ] Design system choice and strategy
- [ ] Core interaction mechanics definition
- [ ] Visual design foundation (colors, typography, spacing)
- [ ] Design direction decisions and mockups
- [ ] User journey flows and interaction design
- [ ] Component strategy and specifications
- [ ] UX consistency patterns documentation
- [ ] Responsive design and accessibility strategy

### Process Complete:

- [ ] All steps completed with user confirmation
- [ ] All content saved to specification document
- [ ] Frontmatter properly updated with all steps
- [ ] Workflow status file updated with completion
- [ ] Next steps clearly communicated

## NEXT STEPS GUIDANCE:

**Immediate Options:**

1. **Wireframe Generation** - Create low-fidelity layouts based on UX spec
2. **Interactive Prototype** - Build clickable prototypes for testing
3. **Solution Architecture** - Technical design with UX context
4. **Figma Visual Design** - High-fidelity UI implementation
5. **Epic Creation** - Break down UX requirements for development

**Recommended Sequence:**
For design-focused teams: Wireframes → Prototypes → Figma Design → Development
For technical teams: Architecture → Epic Creation → Development

Consider team capacity, timeline, and whether user validation is needed before implementation.

## WORKFLOW FINALIZATION:

- Set `lastStep = 14` in document frontmatter
- Update workflow status file with completion timestamp
- Provide completion summary to user
- Do NOT load any additional steps

## FINAL REMINDER:

This UX design workflow is now complete. The specification serves as the foundation for all visual and development work. All design decisions, patterns, and requirements are documented to ensure consistent, accessible, and user-centered implementation.

**Congratulations on completing the UX Design Specification for {{project_name}}!** 🎉

**Core Deliverables:**

- ✅ UX Design Specification: `{planning_artifacts}/ux-design-specification.md`
- ✅ Stitch Artifacts Index: `{planning_artifacts}/ux-stitch-artifacts.md`
- ✅ Live Stitch project: `<stitch.projectUrl>` (with registered design system and all generated screens)
