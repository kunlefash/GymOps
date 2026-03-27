---
name: zone-qa-automation
description: End-to-end test automation standards for Zone payment platform. Covers
  the zoneqa_automation Playwright framework — BasePage POM, token-cached API testing,
  multi-institution data-driven patterns, Testiny reporting, and MS Teams CI notification.
  Use when writing or modifying Playwright E2E or API tests in zoneqa_automation.
  zone.clientdashboard-automation is DEPRECATED — all tests are harmonized here.
version: 2.0.0
triggers:
  keywords:
    - playwright
    - e2e test
    - qa automation
    - page object model
    - testiny
    - basepage
  files:
    - modules/zoneqa_automation/**
    - modules/**/playwright.config.*
  intents:
    - add_e2e_test
    - fix_flaky_test
    - update_page_object
    - improve_test_reporting
    - review_test_coverage
---

# Zone QA Automation — E2E Testing Skill

> Standards for `zoneqa_automation` — the single canonical Playwright framework for all
> Zone E2E and API tests. `zone.clientdashboard-automation` is deprecated; do not create
> or modify files there.

---

## Framework at a Glance

| Aspect | Value |
|---|---|
| **Scope** | All ZonePay / Cardless PWA, API, and infrastructure tests |
| **Playwright** | v1.49.1 |
| **Module system** | ES Modules (`.mjs` config) |
| **POM pattern** | BasePage inheritance |
| **Reporting** | MS Teams + Testiny |
| **Data-driven axis** | Multi-institution (BANKA/BANKB/OFI) |
| **Workers** | 1 (sequential) |
| **Test timeout** | 60s |
| **CI retries** | 1 |

---

## Tech Stack

| Technology | Purpose |
|---|---|
| **Playwright v1.49.1** | Browser automation & API testing |
| **Chai/Expect** | Assertions (via `@playwright/test`) |
| **Testiny** | Test case management mapping |
| **MS Teams Reporter** | CI notification |
| **Faker.js** | Dynamic test data generation |
| **MSSQL (tedious)** | Database fixture queries |
| **ssh2** | Remote server command execution |
| **ESLint v9** | Code quality |
| **Bitbucket Pipelines** | CI/CD |

---

## Architecture — BasePage Inheritance

All page objects **extend BasePage**, which provides navigation, wait helpers,
institution configuration, and utility methods.

### BasePage Contract

```javascript
// pageObjectClass/basePage.js — ALL page objects extend this
export default class BasePage {
  constructor(page) {
    this.page = page;
    // Institution configs, URL resolution, cookie/storage cleanup
  }

  // Navigation
  async navigateTo(url) { /* cookie cleanup + goto */ }
  async goToPWA() { }
  async goToInstitution(code) { }      // 'BANKA', 'BANKB', 'OFI'
  async goToBankA() { }                 // Shortcuts

  // Wait helpers
  async waitForPageReady() { }          // Comprehensive load check
  async waitForLoginPage() { }
  async waitForVisible(locator) { }
  async waitAndClick(locator) { }       // Wait + click combo
  async waitAndFill(locator, text) { }  // Wait + fill combo

  // Config access
  getInstitution(code) { }              // Returns institution config
  validateEnv(name, value) { }          // Validate env var exists

  // Utilities
  async screenshot(name) { }           // Timestamped capture
  getDate(offsetDays) { }              // Date arithmetic
  getDateRange(days) { }               // Range for filters
}
```

### Creating a Page Object

```javascript
import BasePage from './basePage.js';

export default class PaymentPage extends BasePage {
  constructor(page) {
    super(page);  // ⚠️ REQUIRED — initializes BasePage
    this.amountInput = page.locator(
      'input[name="amount"], input[placeholder*="amount" i]'
    ).first();    // ⚠️ Use .first() to avoid strict mode
    this.submitBtn = page.locator('button[type="submit"]').first();
  }

  // Action
  async fillAmount(amount) {
    await this.waitAndFill(this.amountInput, amount);
  }

  // Verification
  async verifyPaymentSuccess() {
    await expect(this.page.locator('.success')).toBeVisible();
  }

  // Flow (multi-step)
  async makePaymentFlow(amount) {
    await this.fillAmount(amount);
    await this.waitAndClick(this.submitBtn);
    await this.verifyPaymentSuccess();
  }
}
```

### Rules

- ✅ **Always** extend `BasePage`
- ✅ **Always** call `super(page)` in constructor
- ✅ **Always** use `.first()` on ambiguous locators
- ✅ Use `this.waitAndClick()` / `this.waitAndFill()` — never bare `.click()`
- ❌ **Never** create standalone page classes
- ❌ **Never** create alternative base classes

---

## Data-Driven Testing — Multi-Institution Loop

Tests iterate over institutions to verify cross-tenant parity:

```javascript
import { test, expect } from '@playwright/test';
import LoginPage from '../../../pageObjectClass/loginPage.js';

const institutions = ['BANKA', 'BANKB', 'OFI'];

for (const institution of institutions) {
  test(`Verify ${institution} user can login`, async ({ page }) => {
    // Optional Testiny annotation
    test.info().annotations.push({
      type: '14213',
      description: `Login test for ${institution}`
    });

    const loginPage = new LoginPage(page);
    await loginPage.loginAsInstitution(institution);
    await expect(loginPage.dashboardHeader).toBeVisible();
  });
}
```

---

## API Testing — Token-Cached Pattern

```javascript
import { getHeadersForBank, URLS } from '../../../apiManager/apiBase.js';
import { apiPayloadManager } from '../../../apiManager/apiPayloadManager.js';

const institutions = ['bankA', 'bankB', 'OFI', 'SNC1', 'SNC2'];

for (const institution of institutions) {
  test(`Generate payment for ${institution}`, async ({ request }) => {
    const headers = await getHeadersForBank(request, institution);
    const payload = apiPayloadManager.generateDynamicQR(200);

    const response = await request.post(
      `${URLS.ADMINS}/zonepay/api/v1/PaymentLinks/generate`,
      { data: payload, headers }
    );
    expect(response.status()).toBe(200);
  });
}
```

> ⚠️ **Never** fetch tokens directly — always use `getHeadersForBank()` to
> prevent race conditions and token expiry in CI.

---

## Test Data Management

For fixture-based data (Faker, DB, SSH) patterns, see [reference/test-data-patterns.md](reference/test-data-patterns.md).

---

## Logging Conventions

Use emoji markers consistently in all test and page object logging:

```javascript
console.log('✅ Login successful');       // Success
console.log('❌ API returned 500');       // Failure
console.log('⚠️  Token expired');         // Warning
console.log('🔵 Navigating to PWA');      // Info/step
```

---

## CI/CD Integration

For Bitbucket Pipelines configuration, test commands, worker/retry settings, and reporter setup, see [reference/ci-cd-config.md](reference/ci-cd-config.md).

---

## Pilot Stability Suite

The pilot suite provides a fast PR check against live infrastructure:

| Feature | Value |
|---|---|
| Command | `npm run test:pilot` |
| Location | `tests/pilot/*.spec.js` |
| SUT guard | `ensureInstitutionAvailable(test, institution)` |
| Skip behavior | Skip with reason if host unreachable |
| Quality gates | `quality-gates.md` |
| Coverage map | `coverage-matrix.csv` |
| Shared fixtures | `authFixture.js`, `apiFixture.js`, `sutAvailability.js` |

---

## Naming Conventions

| Element | Convention | Example |
|---|---|---|
| Test files | `camelCase.spec.js` | `activatePwa.spec.js` |
| Page objects | `camelCase.js` (PascalCase class) | `loginPage.js` → `LoginPage` |
| Fixtures | `camelCaseFixture.js` | `helperFixture.js` |
| Methods — actions | `perform*`, `fill*`, `click*` | `performLogin()` |
| Methods — verify | `verify*`, `check*` | `verifyLoginSuccess()` |
| Methods — flows | `*Flow` | `activateTerminalFlow()` |

---

## Directory Structure

| Path | Purpose |
|---|---|
| `tests/cardless/pwa/` | E2E browser tests |
| `tests/cardless/api/` | API tests |
| `tests/pilot/` | Pilot stability suite |
| `pageObjectClass/` | Page objects (BasePage pattern) |
| `apiManager/` | Token-cached API helpers |
| `fixtures/` | DB, SSH, Faker fixtures |

---

## Common Anti-Patterns

| ❌ Don't | ✅ Do |
|---|---|
| Create page without BasePage | `extends BasePage` + `super(page)` |
| Fetch tokens directly | `getHeadersForBank(request, inst)` |
| `page.waitForTimeout(5000)` | `await expect(el).toBeVisible()` |
| Hardcode selectors in tests | Use page object methods |
| Hardcode test data | Use fixtures / Faker |
| Missing `.first()` on locators | Add `.first()` to ambiguous queries |
| Inconsistent emoji logging | Use ✅❌⚠️🔵 consistently |
| Write E2E/API tests in source modules | Always write to `zoneqa_automation` |

---

## Advanced Testing (TEA Module)

The BMAD TEA (Test Architecture Enterprise) module provides advanced testing workflows beyond standard E2E automation. When loaded as a domain skill in `zone-qa` or other CI skills, these capabilities are available for deeper testing work.

| Workflow | Slash Command | Path | Purpose |
|---|---|---|---|
| **ATDD** | `/bmad-tea-testarch-atdd` | `_bmad/tea/workflows/testarch/atdd/workflow.yaml` | Generate failing acceptance tests using TDD cycle |
| **Automate** | `/bmad-tea-testarch-automate` | `_bmad/tea/workflows/testarch/automate/workflow.yaml` | Expand test automation coverage for codebase |
| **Test Design** | `/bmad-tea-testarch-test-design` | `_bmad/tea/workflows/testarch/test-design/workflow.yaml` | Create system-level or epic-level test plans |
| **Test Review** | `/bmad-tea-testarch-test-review` | `_bmad/tea/workflows/testarch/test-review/workflow.yaml` | Review test quality using best practices validation |
| **Framework** | `/bmad-tea-testarch-framework` | `_bmad/tea/workflows/testarch/framework/workflow.yaml` | Initialize test framework with Playwright or Cypress |
| **CI Pipeline** | `/bmad-tea-testarch-ci` | `_bmad/tea/workflows/testarch/ci/workflow.yaml` | Scaffold CI/CD quality pipeline with test execution |
| **NFR Assessment** | `/bmad-tea-testarch-nfr` | `_bmad/tea/workflows/testarch/nfr-assess/workflow.yaml` | Assess NFRs like performance, security, and reliability |
| **Traceability** | `/bmad-tea-testarch-trace` | `_bmad/tea/workflows/testarch/trace/workflow.yaml` | Generate traceability matrix and quality gate decision |

**TEA Config**: `_bmad/tea/config.yaml`
**TEA Agent Persona**: `_bmad/tea/agents/tea.md`
