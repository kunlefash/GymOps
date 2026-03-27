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

### Quick Start Commands
| Command | Description |
|---------|-------------|
| `/bmad-help` | Show all available commands |
| `/bmad-pm` | Activate PM agent (John) |
| `/bmad-dev` | Activate Dev agent (Amelia) |
| `/bmad-qa` | Activate QA agent (Quinn) |
| `/bmad-architect` | Activate Architect agent (Winston) |
| `/bmad-techwriter` | Activate Tech Writer agent (Maya) |
| `/bmad-ux` | Activate UX Designer agent (Sage) |

### Workflow Commands
| Command | Phase | Description |
|---------|-------|-------------|
| `/bmad-create-brief` | 1. Analysis | Create product brief |
| `/bmad-create-prd` | 2. Planning | Create PRD from brief |
| `/bmad-validate-prd` | 2. Planning | Validate existing PRD |
| `/bmad-create-architecture` | 3. Solutioning | Design system architecture |
| `/bmad-create-epics` | 3. Solutioning | Decompose PRD into epics/stories |
| `/bmad-check-readiness` | 3. Solutioning | Validate readiness for dev |
| `/bmad-dev-story {key}` | 4. Implementation | TDD development of a story |
| `/bmad-code-review {key}` | 4. Implementation | AI code review |
| `/bmad-qa-test {key}` | 4. Implementation | Generate tests |
| `/bmad-sprint-plan` | 4. Sprint Ops | Plan a sprint |
| `/bmad-sprint-status` | 4. Sprint Ops | View sprint progress |

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
├── _bmad/                          # BMAD Framework
│   ├── _config/                    # Integration configs
│   ├── _memory/                    # Project context & state
│   ├── bmm/                        # BMAD Method Module
│   │   ├── agents/                 # Agent personas (PM, Dev, QA, etc.)
│   │   ├── config.yaml             # Central configuration
│   │   ├── data/templates/         # Document templates
│   │   └── workflows/              # Phase 1-4 workflow steps
│   └── core/tasks/                 # Workflow engine
├── _bmad-output/                   # Generated artifacts
│   ├── planning-artifacts/         # PRDs, architecture, epics
│   └── implementation-artifacts/   # Stories, sprints
├── .claude/commands/               # Claude Code slash commands
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
