# {Operation Name}

- **Last Verified**: {YYYY-MM-DD}
- **Owner**: {team or role, e.g. DevOps / Settlement Team}
- **Estimated Duration**: {e.g. 45 minutes}
- **Risk Level**: {Low | Medium | High}
- **Related Initiative**: {Jira epic key} — {initiative title}
- **Related Stories**: {story IDs, e.g. Story 6.1, 6.2}

## Purpose

{One paragraph. What does this operation do and when is it used?}

## Prerequisites

Before starting, confirm the following are true:

- [ ] {Prerequisite 1, e.g. Full SQL Server backup taken and restore-tested}
- [ ] {Prerequisite 2, e.g. PostgreSQL instance provisioned and accessible — `pg_isready -h {host}`}
- [ ] {Prerequisite 3, e.g. Vault token with read access to `secret/zone/{institution}/database`}
- [ ] {Prerequisite 4, e.g. Maintenance window communicated to stakeholders}
- [ ] {Prerequisite 5, e.g. All required CLI tools available: `liquibase`, `kubectl`, `vault`}

## Pre-Operation Checklist

| Check | Command | Expected Result |
|-------|---------|----------------|
| {Check 1} | `{command}` | {expected output} |
| {Check 2} | `{command}` | {expected output} |

## Steps

### Step 1: {Step Name}

**Action**: {What to do}

**Command**:
```bash
{command or script path}
```

**Expected outcome**: {What success looks like}

**Estimated duration**: {e.g. 2 minutes}

**If this step fails**: {Troubleshooting guidance or "Go to Rollback"}

---

### Step 2: {Step Name}

**Action**: {What to do}

**Command**:
```bash
{command or script path}
```

**Expected outcome**: {What success looks like}

**Estimated duration**: {e.g. 5 minutes}

**If this step fails**: {Troubleshooting guidance}

---

<!-- Repeat Step blocks as needed -->

## Validation

Run these checks after all steps complete to confirm the operation succeeded.

| Validation | Command | Expected Result |
|------------|---------|----------------|
| {Validation 1} | `{command}` | {expected} |
| {Validation 2} | `{command}` | {expected} |

**Validation criteria** (from architecture): {Reference specific thresholds if documented, e.g. "error rate must be <5%, latency regression <20%"}

## Rollback

**Rollback triggers** — initiate rollback immediately if any of the following occur:
- {Trigger 1, e.g. Error rate >5% after cutover}
- {Trigger 2, e.g. Settlement report mismatch}
- {Trigger 3, e.g. Data integrity issue detected}

**Rollback steps**:

1. {Step 1, e.g. `vault kv put secret/zone/{institution}/database connectionString="..." databaseType=SqlServer`}
2. {Step 2, e.g. `kubectl rollout restart deployment/{service-name} -n {namespace}`}
3. {Step 3, e.g. Verify services healthy — repeat Validation section}

**Post-rollback decision tree**:
- If rollback occurred **within the maintenance window**: {guidance}
- If rollback occurred **after the maintenance window**: {guidance}
- Rollback window expiry: {e.g. 7 days — then decommission SQL Server backup}

## Post-Operation Monitoring

Monitor the following for the first **{recommended observation period, e.g. 30 minutes}** after the operation completes:

| Metric | Where to Check | Alert Threshold |
|--------|---------------|----------------|
| Error rate | Grafana → {dashboard name} | {threshold} |
| Latency (p99) | Grafana → {dashboard name} | {threshold} |
| {Domain metric, e.g. Settlement report correctness} | {location} | {criteria} |

**Declaring success**: Operation is declared successful when all monitoring checks pass for {duration} with no alerts triggered.

## Known Limitations

<!-- Document any steps that depend on tooling not yet implemented. Remove section if none. -->

| Limitation | Workaround | Future Resolution |
|------------|-----------|------------------|
| {e.g. Data export tooling} | {e.g. Manual BCP/pg_dump} | {e.g. Story 6.2} |

<!-- ============================================================
     COMPLIANCE NOTE
     Include this section only if the operation touches compliance-sensitive
     modules (zone.zonepay, zone.cardlesstransactionprocessing, zonepay.settlement,
     zone.pggateway, zonedc.settlement, zone.smartcontracts.sui, zone.settlement.sui,
     zone.admin.api funding/liquidation paths).
     Delete this comment block and the section if not applicable.
     ============================================================ -->

## Compliance Note

- **Regulatory Body**: {CBN | NIBSS | PTSA}
- **Applicable Rule**: {specific regulation or requirement}
- **Impact**: {what this operation means for compliance posture}
- **CBN Notification Required**: {Yes — reason | No — reason}
