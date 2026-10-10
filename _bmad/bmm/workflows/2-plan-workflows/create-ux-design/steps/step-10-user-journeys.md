# Step 10: User Journey Flows

## MANDATORY EXECUTION RULES (READ FIRST):

- 🛑 NEVER generate content without user input

- 📖 CRITICAL: ALWAYS read the complete step file before taking any action - partial understanding leads to incomplete decisions
- 🔄 CRITICAL: When loading next step with 'C', ensure the entire file is read and understood before proceeding
- ✅ ALWAYS treat this as collaborative discovery between UX facilitator and stakeholder
- 📋 YOU ARE A UX FACILITATOR, not a content generator
- 💬 FOCUS on designing user flows and journey interactions
- 🎯 COLLABORATIVE flow design, not assumption-based layouts
- ✅ YOU MUST ALWAYS SPEAK OUTPUT In your Agent communication style with the config `{communication_language}`

## EXECUTION PROTOCOLS:

- 🎯 Show your analysis before taking any action
- ⚠️ Present A/P/C menu after generating user journey content
- 💾 ONLY save when user chooses C (Continue)
- 📖 Update output file frontmatter, adding this step to the end of the list of stepsCompleted.
- 🚫 FORBIDDEN to load next step until C is selected

## COLLABORATION MENUS (A/P/C):

This step will generate content and present choices:

- **A (Advanced Elicitation)**: Use discovery protocols to develop deeper journey insights
- **P (Party Mode)**: Bring multiple perspectives to design user flows
- **C (Continue)**: Save the content to the document and proceed to next step

## PROTOCOL INTEGRATION:

- When 'A' selected: Read fully and follow: {project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml
- When 'P' selected: Read fully and follow: {project-root}/_bmad/core/workflows/party-mode/workflow.md
- PROTOCOLS always return to this step's A/P/C menu
- User accepts/rejects protocol changes before proceeding

## CONTEXT BOUNDARIES:

- Current document and frontmatter from previous steps are available
- Design direction from step 9 informs flow layout and visual design
- Core experience from step 7 defines key journey interactions
- Stitch project (`stitch.projectId`) and chosen direction screen (`stitch.chosenDirectionScreenId`) are live and will host journey screens
- Focus on designing detailed user flows with Mermaid diagrams AND generating a Stitch screen per journey

## PREFLIGHT: Verify Stitch Context

Read `{planning_artifacts}/ux-design-specification.md` frontmatter. Confirm:
- `stitch.projectId` is non-empty
- `stitch.chosenDirectionScreenId` is non-empty

If either is empty, halt with:
"Stitch context is incomplete. Ensure step-08b ran and step-09 locked a chosen direction before re-running this step."

## YOUR TASK:

Design detailed user journey flows for critical user interactions AND generate a Stitch screen per critical journey inside the existing Stitch project.

## USER JOURNEY FLOWS SEQUENCE:

### 1. Load PRD User Journeys as Foundation

Start with user journeys already defined in the PRD:
"Great! Since we have the PRD available, let's build on the user journeys already documented there.

**Existing User Journeys from PRD:**
I've already loaded these user journeys from your PRD:
[Journey narratives from PRD input documents]

These journeys tell us **who** users are and **why** they take certain actions. Now we need to design **how** those journeys work in detail.

**Critical Journeys to Design Flows For:**
Looking at the PRD journeys, I need to design detailed interaction flows for:

- [Critical journey 1 identified from PRD narratives]
- [Critical journey 2 identified from PRD narratives]
- [Critical journey 3 identified from PRD narratives]

The PRD gave us the stories - now we design the mechanics!"

### 2. Design Each Journey Flow

For each critical journey, design detailed flow:

**For [Journey Name]:**
"Let's design the flow for users accomplishing [journey goal].

**Flow Design Questions:**

- How do users start this journey? (entry point)
- What information do they need at each step?
- What decisions do they need to make?
- How do they know they're progressing successfully?
- What does success look like for this journey?
- Where might they get confused or stuck?
- How do they recover from errors?"

### 3. Create Flow Diagrams

Visualize each journey with Mermaid diagrams:
"I'll create detailed flow diagrams for each journey showing:

**[Journey Name] Flow:**

- Entry points and triggers
- Decision points and branches
- Success and failure paths
- Error recovery mechanisms
- Progressive disclosure of information

Each diagram will map the complete user experience from start to finish."

### 4. Optimize for Efficiency and Delight

Refine flows for optimal user experience:
"**Flow Optimization:**
For each journey, let's ensure we're:

- Minimizing steps to value (getting users to success quickly)
- Reducing cognitive load at each decision point
- Providing clear feedback and progress indicators
- Creating moments of delight or accomplishment
- Handling edge cases and error recovery gracefully

**Specific Optimizations:**

- [Optimization 1 for journey efficiency]
- [Optimization 2 for user delight]
- [Optimization 3 for error handling]"

### 4b. Generate Stitch Screens for Each Critical Journey

For each critical journey identified in step 2, generate one Stitch screen representing the journey's primary destination / resolution state (NOT every step of the flow — one anchor screen per journey).

For each journey:

1. Compose a Stitch prompt grounded in:
   - The journey's goal (from step 2)
   - The content blocks the PRD actually specifies for this screen
   - The chosen direction's aesthetic (reference: `stitch.chosenDirectionScreenId`)

   Prompt shape:
   ```
   A [MOBILE|DESKTOP] [screen purpose] for [product type]. The user arrives here after [journey trigger]. They need to [primary task on this screen]. Key elements: [block 1], [block 2], [block 3]. Match the visual direction already established in this project — same layout density, color treatment, and interaction style as the other screens. No new features — only what the PRD specifies for this journey.
   ```

2. Confirm with user: "Send this prompt to Stitch for [Journey Name]? (send / adjust)"

3. Call `mcp__stitch__generate_screen_from_text`:
   ```json
   {
     "projectId": "<stitch.projectId>",
     "deviceType": "<per journey — MOBILE/DESKTOP/TABLET/AGNOSTIC>",
     "modelId": "GEMINI_3_1_PRO",
     "prompt": "<composed prompt>"
   }
   ```

4. Wait for completion (minutes). On connection error, **DO NOT RETRY**. Wait ~30s, then `mcp__stitch__list_screens` to find the new screen.

5. Capture the screen ID. Update frontmatter `stitch.journeyScreens` (map of journey name → screen ID):
   ```yaml
   stitch:
     journeyScreens:
       "<Journey 1 name>": "<screenId>"
       "<Journey 2 name>": "<screenId>"
       "<Journey 3 name>": "<screenId>"
   ```

6. After all journey screens are generated, show the user the Stitch URLs and let them request refinements via `edit_screens` before proceeding.

### 5. Document Journey Patterns

Extract reusable patterns across journeys:
"**Journey Patterns:**
Across these flows, I'm seeing some common patterns we can standardize:

**Navigation Patterns:**

- [Navigation pattern 1]
- [Navigation pattern 2]

**Decision Patterns:**

- [Decision pattern 1]
- [Decision pattern 2]

**Feedback Patterns:**

- [Feedback pattern 1]
- [Feedback pattern 2]

These patterns will ensure consistency across all user experiences."

### 6. Generate User Journey Content

Prepare the content to append to the document:

#### Content Structure:

When saving to document, append these Level 2 and Level 3 sections:

```markdown
## User Journey Flows

### [Journey 1 Name]

[Journey 1 description and Mermaid diagram]

**Stitch screen:** `<stitch.projectUrl>/screens/<journey1ScreenId>` · Screen ID `<journey1ScreenId>`

### [Journey 2 Name]

[Journey 2 description and Mermaid diagram]

**Stitch screen:** `<stitch.projectUrl>/screens/<journey2ScreenId>` · Screen ID `<journey2ScreenId>`

### Journey Patterns

[Journey patterns identified based on conversation]

### Flow Optimization Principles

[Flow optimization principles based on conversation]

### Stitch Screen Map

| Journey | Device | Stitch Screen ID |
|---------|--------|------------------|
| [Journey 1] | [MOBILE/DESKTOP] | `<id>` |
| [Journey 2] | [MOBILE/DESKTOP] | `<id>` |
| [Journey 3] | [MOBILE/DESKTOP] | `<id>` |
```

### 7. Present Content and Menu

Show the generated user journey content and present choices:
"I've designed detailed user journey flows for {{project_name}}. These flows will guide the detailed design of each user interaction.

**Here's what I'll add to the document:**

[Show the complete markdown content from step 6]

**What would you like to do?**
[A] Advanced Elicitation - Let's refine our user journey designs
[P] Party Mode - Bring different perspectives on user flows
[C] Continue - Save this to the document and move to component strategy

### 8. Handle Menu Selection

#### If 'A' (Advanced Elicitation):

- Read fully and follow: {project-root}/_bmad/core/workflows/advanced-elicitation/workflow.xml with the current user journey content
- Process the enhanced journey insights that come back
- Ask user: "Accept these improvements to the user journeys? (y/n)"
- If yes: Update content with improvements, then return to A/P/C menu
- If no: Keep original content, then return to A/P/C menu

#### If 'P' (Party Mode):

- Read fully and follow: {project-root}/_bmad/core/workflows/party-mode/workflow.md with the current user journeys
- Process the collaborative journey insights that come back
- Ask user: "Accept these changes to the user journeys? (y/n)"
- If yes: Update content with improvements, then return to A/P/C menu
- If no: Keep original content, then return to A/P/C menu

#### If 'C' (Continue):

- Append the final content to `{planning_artifacts}/ux-design-specification.md`
- Update frontmatter: append step to end of stepsCompleted array
- Load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-11-component-strategy.md`

## APPEND TO DOCUMENT:

When user selects 'C', append the content directly to the document using the structure from step 6.

## SUCCESS METRICS:

✅ Critical user journeys identified and designed
✅ Detailed flow diagrams created for each journey
✅ Flows optimized for efficiency and user delight
✅ Common journey patterns extracted and documented
✅ One Stitch screen generated per critical journey (anchor/destination state)
✅ `stitch.journeyScreens` map populated in frontmatter
✅ Stitch URLs + IDs included in the documented journey sections
✅ A/P/C menu presented and handled correctly
✅ Content properly appended to document when C selected

## FAILURE MODES:

❌ Not identifying all critical user journeys
❌ Flows too complex or not optimized for user success
❌ Missing error recovery paths
❌ Not extracting reusable patterns across journeys
❌ Flow diagrams unclear or incomplete
❌ Generating multiple Stitch screens per journey (one anchor screen is the contract — flow diagrams carry step-by-step detail, not Stitch)
❌ Retrying Stitch `generate_screen_from_text` on connection error (use `list_screens` recovery pattern)
❌ Leaving `stitch.journeyScreens` empty or partial when proceeding
❌ Generating screens without referencing the chosen direction's aesthetic (screens will drift from step-09's decision)
❌ Not presenting A/P/C menu after content generation
❌ Appending content without user selecting 'C'

❌ **CRITICAL**: Reading only partial step file - leads to incomplete understanding and poor decisions
❌ **CRITICAL**: Proceeding with 'C' without fully reading and understanding the next step file
❌ **CRITICAL**: Making decisions without complete understanding of step requirements and protocols

## NEXT STEP:

After user selects 'C' and content is saved to document, load `{project-root}/_bmad/bmm/workflows/2-plan-workflows/create-ux-design/steps/step-11-component-strategy.md` to define component library strategy.

Remember: Do NOT proceed to step-11 until user explicitly selects 'C' from the A/P/C menu and content is saved!
