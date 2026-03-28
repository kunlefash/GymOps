# CI/CD Integration

## zoneqa_automation — GitHub Actionss

```bash
npm test                   # All tests
npm run testapi            # API tests only
npm run testui             # UI tests only
npm run test:pilot         # Pilot stability suite
npm run test:smoke         # Smoke subset
npm run testiny:import     # Sync results to Testiny
npm run lint               # Lint check
```

- **Workers**: 1 (sequential)
- **Retries**: 1 in CI
- **Reporters**: list, JSON, MS Teams, Testiny
- **5-shard parallel**: Full regression via `full-regression` custom pipeline
- **PR/main**: Lint + pilot suite only

## zone.clientdashboard-automation — GitHub Actionss

```bash
npx playwright test                          # All tests
npx playwright test tests/withLogin/         # Authenticated tests
npm run lint:ci                              # Zero-warnings lint
npx allure generate ./out/allure-results     # Generate Allure report
```

- **Workers**: 3 in CI (parallel)
- **Retries**: 2 in CI
- **Browser projects**: Chromium + Firefox
- **Reporters**: list, Allure
- **Load testing**: Custom `load-test` pipeline (JMeter)
- **PR/default**: Lint + pilot suite only
