# Test Data Management

## zoneqa_automation — Fixture-Based

```javascript
// Dynamic data (Faker)
import { generateTestData } from '../../../fixtures/testData.js';
const testData = generateTestData();
const alias = testData.randomString(12);

// Database
import { connectToDB, runQuery, closeAllDBs } from '../../../fixtures/mysqldbClient.js';
test.beforeAll(async () => { await connectToDB('primary'); });
test.afterAll(async () => { await closeAllDBs(); });

// SSH
import { runCommandByServerName } from '../../../fixtures/sshClient.js';
const result = await runCommandByServerName('zonepay', 'ls -la /home/qaadmin');
```

## zone.clientdashboard-automation — JSON Files

All test data in `utils/testdata/*.json`:

```javascript
import loginData from "../../utils/testdata/logindata.json";
import urls from "../../utils/testdata/url.json";

const email = loginData.email[0];
const password = loginData.passwords.valid[0];
const url = urls.urlElevenZeroEighty + "/client/account/login";
```

JSON files: `logindata`, `url`, `transactionsdata`, `settlementsdata`,
`walletdata`, `disputedata`, `settingsdata`, `terminaldata`, `onboardingdata`,
`companydata`, `audittraildetails`.
