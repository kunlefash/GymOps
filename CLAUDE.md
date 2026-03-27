# GymOps - BMAD Agentic SDLC

## Project Overview
GymOps is a gym operations management platform built with the BMAD (Build, Method, Agents, Design) framework for structured AI-driven development.

## Tech Stack
- **Frontend**: Next.js 15, TypeScript (strict), Tailwind CSS, shadcn/ui
- **Backend**: Node.js, Next.js API Routes, TypeScript
- **Database**: PostgreSQL + Prisma ORM
- **Deployment**: Vercel (frontend + serverless API)
- **Testing**: Jest (unit), React Testing Library (components), Playwright (E2E)
- **CI/CD**: GitHub Actions

## BMAD Framework

### Agent Commands
| Command | Description |
|---------|-------------|
| `/bmad-help` | Show all available commands |
| `/bmad-agent-bmm-pm` | Activate PM agent (John) — PRD, product briefs, epics |
| `/bmad-agent-bmm-dev` | Activate Dev agent (Amelia) — TDD implementation |
| `/bmad-agent-bmm-qa` | Activate QA agent (Quinn) — Test automation |
| `/bmad-agent-bmm-architect` | Activate Architect agent (Winston) — System design |
| `/bmad-agent-bmm-tech-writer` | Activate Tech Writer — Documentation |
| `/bmad-agent-bmm-ux-designer` | Activate UX Designer — User experience |
| `/bmad-agent-bmm-analyst` | Activate Analyst — Research & analysis |
| `/bmad-agent-bmm-sm` | Activate Scrum Master — Sprint management |
| `/bmad-agent-bmad-master` | Activate BMAD Master — Framework orchestrator |
| `/bmad-agent-tea-tea` | Activate Test Architect (TEA) — Advanced testing |

### Workflow Shortcut Commands
| Command | Phase | Description |
|---------|-------|-------------|
| `/bmad-bmm-create-product-brief` | 1. Analysis | Create product brief |
| `/bmad-bmm-create-prd` | 2. Planning | Create PRD |
| `/bmad-bmm-validate-prd` | 2. Planning | Validate existing PRD |
| `/bmad-bmm-edit-prd` | 2. Planning | Edit existing PRD |
| `/bmad-bmm-create-ux-design` | 2. Planning | Create UX design specs |
| `/bmad-bmm-create-architecture` | 3. Solutioning | Design system architecture |
| `/bmad-bmm-create-epics-and-stories` | 3. Solutioning | Decompose PRD into epics/stories |
| `/bmad-bmm-create-story` | 3. Solutioning | Create individual story |
| `/bmad-bmm-check-implementation-readiness` | 3. Solutioning | Validate readiness for dev |
| `/bmad-bmm-dev-story` | 4. Implementation | TDD development of a story |
| `/bmad-bmm-code-review` | 4. Implementation | AI code review |
| `/bmad-bmm-qa-generate-e2e-tests` | 4. Implementation | Generate E2E tests |
| `/bmad-bmm-sprint-planning` | 4. Sprint Ops | Plan a sprint |
| `/bmad-bmm-sprint-status` | 4. Sprint Ops | View sprint progress |
| `/bmad-bmm-correct-course` | 4. Sprint Ops | Mid-sprint course correction |

### Research & Utility Commands
| Command | Description |
|---------|-------------|
| `/bmad-bmm-market-research` | Market analysis |
| `/bmad-bmm-domain-research` | Domain deep-dive |
| `/bmad-bmm-technical-research` | Technical research |
| `/bmad-brainstorming` | Structured brainstorming session |
| `/bmad-party-mode` | Multi-agent discussion |
| `/bmad-review-adversarial-general` | Adversarial review |
| `/bmad-review-edge-case-hunter` | Edge case analysis |
| `/bmad-bmm-document-project` | Generate project documentation |

### TEA (Test Architecture) Commands
| Command | Description |
|---------|-------------|
| `/bmad-tea-testarch-framework` | Set up test framework |
| `/bmad-tea-testarch-test-design` | Test design methodology |
| `/bmad-tea-testarch-atdd` | Acceptance Test-Driven Development |
| `/bmad-tea-testarch-automate` | Test automation |
| `/bmad-tea-testarch-ci` | CI pipeline integration |
| `/bmad-tea-testarch-nfr` | Non-functional requirements testing |
| `/bmad-tea-testarch-test-review` | Test review |
| `/bmad-tea-testarch-trace` | Requirements traceability |
| `/bmad-tea-teach-me-testing` | Testing education |

### Development Flow
```
Product Brief → PRD → Architecture → Epics/Stories → Sprint Plan
                                                         ↓
                                          Dev Story (TDD) → Code Review → QA → Merge
                                                ↑                              ↓
                                                └──── Fix Review Items ←───────┘
```

## Conventions
- **TDD Required**: Write tests FIRST, then implement (RED→GREEN→REFACTOR→EXPAND)
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`, `test:`, `refactor:`)
- **Branches**: `feat/{story-key}`, `fix/{story-key}`, `hotfix/{description}`
- **Test Coverage**: Minimum 80% on new/modified files
- **No Secrets**: Use environment variables, never commit secrets
- **PRs**: All code goes through PR review (AI + human)

## Project Structure
```
GymOps/
├── _bmad/                          # BMAD Framework (463 files)
│   ├── _config/                    # Agent configs, manifests, IDE configs (20)
│   ├── _memory/                    # Project context & persistent state (3)
│   ├── bmm/                        # BMAD Method Module
│   │   ├── agents/                 # Agent personas - PM, Dev, QA, Architect, etc. (9)
│   │   ├── config.yaml             # Central configuration
│   │   ├── data/                   # Templates and data files
│   │   └── workflows/              # Phase 1-4 workflow steps (171)
│   ├── core/                       # Core engine (28)
│   │   ├── tasks/                  # workflow.xml, help, editorial review, etc.
│   │   └── workflows/              # Party mode, brainstorming, advanced elicitation
│   └── tea/                        # Test Architecture Enterprise (230)
│       └── workflows/              # ATDD, automation, CI, test design, NFR, trace
├── _bmad-output/                   # Generated artifacts
│   ├── planning-artifacts/         # PRDs, architecture, epics
│   └── implementation-artifacts/   # Stories, sprints
├── .claude/
│   ├── commands/                   # Slash commands (52 entry points)
│   └── skills/                     # CI/headless skills (20 modules, 71 files)
├── .github/workflows/              # GitHub Actions (CI, AI agents)
├── src/                            # Application source (Next.js)
├── prisma/                         # Database schema & migrations
└── tests/                          # Test files
```

## Key Rules
1. Always read `_bmad/bmm/config.yaml` before executing any workflow
2. Always read the agent persona file before assuming that agent's role
3. Follow workflow steps in EXACT numerical order
4. Save output after every `<template-output>` tag
5. TDD is non-negotiable — RED phase comes first
6. Never modify existing passing tests without explicit approval
7. All AI-generated code goes through PR review
