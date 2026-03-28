# {Module Name}

{One-sentence description: what the module does and its role in the GymOps platform.}

---

<!-- ============================================================
     SELECT THE VARIANT THAT MATCHES THE MODULE TYPE.
     Delete all other variants before using this template.
     ============================================================ -->

---

## VARIANT A: Next.js Service or Library
<!-- Use for: zone.gymops, zone.pggateway, zone.framework, gymops.settlement, etc. -->
<!-- Gold standard: src/gymops/README.md -->

## Overview

{2–3 sentences. What the module does, which business capability it owns, and which other services interact with it.}

## Architecture

The project follows App Router architecture with clear separation of concerns:

```
├── {Module}.Api/              # Web API layer — controllers, middleware, global exception handling
├── {Module}.Core/             # Business entities, domain logic, interfaces
├── {Module}.Infrastructure/   # Data access, EF Core configurations, external integrations
└── tests/                     # Unit and integration test projects
```

{Add sub-sections for distributed or multi-tenant architecture if relevant.}

## Key Features

- **{Feature 1}**: {brief description}
- **{Feature 2}**: {brief description}
- **{Feature 3}**: {brief description}

## Core Entities

| Entity | Description |
|--------|-------------|
| `{Entity1}` | {what it represents} |
| `{Entity2}` | {what it represents} |

## Configuration

| Key | Source | Description |
|-----|--------|-------------|
| `DatabaseType` | Vault / ENV | `SqlServer` or `PostgreSql` |
| `{Config Key}` | Vault `kv/zoneswitch/{path}` | {description} |

**Vault path pattern**: `secret/zone/{institution}/{service-name}`

## Docker Setup

```bash
# Start local dependencies
docker-compose up -d

# Run database migrations
{migration command}
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `{METHOD}` | `{path}` | {description} |

See `doc/apispec.yaml` for full OpenAPI spec (if present).

## Troubleshooting

| Symptom | Likely Cause | Resolution |
|---------|-------------|------------|
| {symptom} | {cause} | {fix} |

---

## VARIANT B: Frontend Application
<!-- Use for: zone.clientdashboard, zone.gymopspwa, zone.gymops.qrrouter -->

## Overview

{2–3 sentences. What the app does, which users it serves, and its role in the platform.}

## Tech Stack

- **Framework**: {React 18 / Next.js 15}
- **Language**: TypeScript (strict)
- **Styling**: {Tailwind CSS / CSS Modules / etc.}
- **State**: {Redux / Zustand / Context}

## Getting Started

```bash
npm install
npm run dev
```

## Project Structure

```
src/
├── components/     # Reusable UI components
├── pages/          # Route-level components (Next.js) or views
├── services/       # API client calls
├── store/          # State management
└── types/          # TypeScript type definitions
```

## Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `NEXT_PUBLIC_{VAR}` | {description} | Yes |
| `{VAR}` | {description} | No |

Never commit real values. Use `.env.local` for local dev; Vault/CI for deployed environments.

## Deployment

Deployed via Cloudflare Pages. See `zone.helm` for Kubernetes configs if applicable.

---

## VARIANT C: Infrastructure — Helm / Liquibase
<!-- Use for: zone.helm, gymops.helmtemplate, gymops.helmvalues, zone.liquibase, gymops.version2sqlscripts -->

## Overview

{2–3 sentences. What this repo does in the deployment or migration pipeline.}

## How It Works

{Step-by-step description of the key pipeline: input → processing → output.}

## Configuration

| Parameter | Description | Example |
|-----------|-------------|---------|
| `{param}` | {description} | `{example}` |

## Usage Examples

```bash
# {Example operation}
{command}
```

## Directory Structure

```
{annotated tree of key files and directories}
```

---

## VARIANT D: QA Automation
<!-- Use for: zoneqa_automation, zone.clientdashboard-automation -->

## Overview

{2–3 sentences. What this repo tests, which application it targets, and which framework it uses.}

## Framework

- **Test runner**: Playwright
- **Language**: JavaScript (ESM)
- **Pattern**: {POM — Page Object Model / Index facade}

## Test Structure

```
{pageObjectClass/ or pageObjectRepo/}
├── {PageName}.js       # Page object for {page}
└── ...
{apiManager/ or apiManager/}
└── {ApiName}.js        # API test helpers
```

## Running Tests

```bash
# Install dependencies
npm install

# Run all tests
npx playwright test

# Run specific suite
npx playwright test --grep "{suite name}"
```

## CI Integration

Tests run in {TeamCity / GitHub Actions} on {trigger condition}. See `zone.ci` for pipeline DSL.
