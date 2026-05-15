# KQL in Entra ID Context — Entra ID KB

> Curated from Entra.news (+ Microsoft Learn). Maintained by `entra-kb-curator`.

## Description

Kusto Query Language (KQL) is the query language for Azure Monitor Log
Analytics and Microsoft Sentinel, and it is the primary way administrators
and SOC analysts interrogate Microsoft Entra ID telemetry at scale. Once you
route Entra diagnostic settings (`SigninLogs`, `AuditLogs`,
`AADNonInteractiveUserSignInLogs`, `AADServicePrincipalSignInLogs`,
`AADManagedIdentitySignInLogs`, `RiskyUsers`, `UserRiskEvents`,
`AADProvisioningLogs`, `MicrosoftGraphActivityLogs`) to a Log Analytics
workspace, KQL becomes the lingua franca for conditional-access audits,
anomaly detection, risky-user triage, password-spray hunts, MFA manipulation
investigations, privileged-role reviews, and cross-service correlation via
linkable identifiers.

This KB distills the KQL patterns and community resources surfaced through
Entra.news together with the canonical Microsoft Learn references. Use
`queries.kql` as an interactively runnable playbook against any Log Analytics
workspace that is sinking Entra diagnostic logs.

## Summary

- Kusto Query Language (KQL) is the read-only pipeline language used in both Log Analytics and Microsoft Sentinel — master it once, reuse everywhere.
- Before you can query a single row, enable Entra ID diagnostic settings for `SigninLogs`, `AuditLogs`, and the non-interactive / service-principal / managed-identity variants.
- Log Analytics shows multiple rows per sign-in that share a `CorrelationId`; collapse them with `arg_max` before drawing conclusions.
- Linkable identifiers (`uti`, `sid`, `oid`, `deviceid`) let you join `MicrosoftGraphActivityLogs` against every `*SignInLogs` stream for end-to-end token tracing.
- Sentinel data-lake sample queries cover location anomalies, rare audit activity, password-spray baselines, and privilege-escalation joins out of the box.
- The Entra.news community has published multi-year KQL hunt libraries — notably GoXDR (Göksel Atakan) and the cyb3rmik3/KQL-threat-hunting-queries repo — which pair well with David Alonso Dominguez's Sentinel + MCP series on identity-risk and password-spray hunting.

## Key Concepts

### Diagnostic settings are the prerequisite
You cannot query what you do not collect. Configure Entra ID diagnostic
settings to stream to a Log Analytics workspace. At minimum enable
`SignInLogs`, `AuditLogs`, `NonInteractiveUserSignInLogs`,
`ServicePrincipalSignInLogs`, `ManagedIdentitySignInLogs`, `RiskyUsers`,
`UserRiskEvents`, and — if you want cross-service tracing —
`MicrosoftGraphActivityLogs`. The least privileged role to run the resulting
KQL queries is **Reports Reader**, but collection setup requires **Security
Administrator** on the Entra side plus **Log Analytics Contributor** on the
Azure side. ([MS Learn tutorial](https://learn.microsoft.com/entra/identity/monitoring-health/tutorial-configure-log-analytics-workspace))

### CorrelationId is how you deduplicate a single sign-in
During interactive sign-in a user may fail MFA once and retry — Log Analytics
persists every request as its own row, while the Entra admin center portal
collapses them into a single event. Any dashboard that naively counts
`SigninLogs` rows will overstate both successes and failures. The canonical
pattern is `summarize ... by CorrelationId, UserPrincipalName` with
`arg_max(TimeGenerated, ResultType, ConditionalAccessStatus)` to take the
final outcome. ([MS Learn](https://learn.microsoft.com/entra/identity/monitoring-health/howto-analyze-activity-logs-log-analytics#multiple-sign-in-records-in-log-analytics))

### Linkable identifiers unlock end-to-end investigation
`uti` (Unique Token Identifier / `SignInActivityId`), `sid` (Session ID),
`oid` (User object ID), `tid` (Tenant ID), and `deviceid` are the
cross-service join keys. With `MicrosoftGraphActivityLogs` in your workspace
you can pivot from a single suspicious sign-in to every Graph call the
resulting token made — essential for token-theft and consent-phishing
investigations. ([MS Learn](https://learn.microsoft.com/entra/identity/authentication/how-to-authentication-track-linkable-identifiers#linkable-identifiers-in-microsoft-graph-activity-logs))

### Entra ID Protection has its own tables
Risk signal lives in `AADUserRiskEvents`, `RiskyUsers`,
`AADServicePrincipalRiskEvents`, and `RiskyServicePrincipals` — not in
`SigninLogs`. The Microsoft Learn risk-remediation playbook walks through
turning these tables into an actionable triage view per user. ([MS Learn](https://learn.microsoft.com/entra/architecture/id-protection-guide-analyze#create-a-log-analytics-workspace))

### Microsoft Sentinel data lake ships sample KQL
If you are on Sentinel, the out-of-the-box KQL library already includes
anomalous-sign-in-location trend analysis, daily-app-baseline queries, rare
audit-by-app detectors, and privilege-escalation joins. Treat them as a
starting point rather than a final detection — tune the lookback windows
and privileged-role list to your environment. ([MS Learn](https://learn.microsoft.com/azure/sentinel/datalake/kql-sample-queries))

### Community hunt libraries extend the basics
Entra.news has repeatedly highlighted community KQL collections worth
bookmarking:

- **GoXDR KQL Query Library** by Göksel Atakan — surfaced in EN #144.
- **cyb3rmik3/KQL-threat-hunting-queries** — surfaced in EN #98, covers Sentinel-native identity hunts such as "password-never-expires with blast-radius tagging".
- **David Alonso Dominguez's Sentinel & MCP series** — SigninLogs threat-hunting workbook (EN #139) plus ongoing password-spray / identity-risk hunts (EN #144).
- **Thabet Awad — Hunting for MFA manipulations in Entra ID tenants using KQL** (EN #47).
- **Kijo Girardi — AiTM & BEC threat hunting with KQL** (EN #4).
- **Patrick Binder — Entra ID Password Spraying using APIM as IP-Rotating Mechanism** (EN #140): attacker playbook you should write detections against.

## Artifacts

- [`queries.kql`](./queries.kql) — 20+ ready-to-run KQL snippets covering basic sign-in introspection, CorrelationId merging, privilege-escalation joins, password-spray baselines, MFA-manipulation hunts, ID-Protection triage, token-protection enforcement, and Graph activity correlation.
- [`snippets.ps1`](./snippets.ps1) — PowerShell helpers to enable Entra diagnostic settings on a Log Analytics workspace, run KQL via `Invoke-AzOperationalInsightsQuery`, and fetch sign-ins directly from Microsoft Graph when Log Analytics is unavailable.

## Sources

### Entra.news

- [Issue #4 — Your weekly dose of Microsoft Entra](https://entra.news/p/entranews-4-your-weekly-dose-of-microsoft) — 2023-08-06 (AiTM & BEC threat hunting with KQL — Kijo Girardi)
- [Issue #47 — This week in Microsoft Entra](https://entra.news/p/entranews-47-this-week-in-microsoft) — 2024-06-02 (Hunting for MFA manipulations in Entra ID tenants using KQL — Thabet Awad; ADX customized reports tutorial)
- [Issue #98 — This week in Microsoft Entra](https://entra.news/p/entra-news-98-this-week-in-microsoft) — 2025-05-25 (cyb3rmik3/KQL-threat-hunting-queries; nathanmcnulty operational groups)
- [Issue #139 — Passkeys, Conditional Access, Hard-match updates, GSA BYOD](https://entra.news/p/passkeys-conditional-access-hard) — 2026-03-07 (SigninLogs Threat Hunting Workbook — David Alonso Dominguez)
- [Issue #140 — How to Migrate from Legacy VPNs to Entra Private Access](https://entra.news/p/how-to-migrate-from-legacy-vpns-to) — 2026-03-14 (Entra ID Password Spraying using APIM as IP-Rotating Mechanism — Patrick Binder)
- [Issue #142 — Finding Every MFA Gap: Testing 250 Million CA Combinations](https://entra.news/p/finding-every-mfa-gap-testing-250) — 2026-03-28 (CA Insight offline evaluation — Emilien Socchi)
- [Issue #144 — This week in Microsoft Entra](https://entra.news/p/entra-news-144-this-week-in-microsoft) — 2026-04-12 (GoXDR KQL Query Library — Göksel Atakan; Sentinel & MCP identity-risk & password-spray hunting — David Alonso Dominguez)

### Microsoft Learn

- [Tutorial: Create a Log Analytics workspace to analyze sign-in logs](https://learn.microsoft.com/entra/identity/monitoring-health/tutorial-configure-log-analytics-workspace) — end-to-end setup + starter KQL examples.
- [Analyze Microsoft Entra activity logs with Log Analytics](https://learn.microsoft.com/entra/identity/monitoring-health/howto-analyze-activity-logs-log-analytics) — CorrelationId deduplication and advanced query recipes.
- [Track and investigate identity activities with linkable identifiers in Microsoft Entra](https://learn.microsoft.com/entra/identity/authentication/how-to-authentication-track-linkable-identifiers) — `uti`/`sid`/`oid` join patterns against `MicrosoftGraphActivityLogs`.
- [Sample KQL queries for Microsoft Sentinel data lake](https://learn.microsoft.com/azure/sentinel/datalake/kql-sample-queries) — anomalous sign-in locations, rare audit activity, privilege-escalation joins.
- [Entra ID Protection scenario: Mastering risk analysis for effective remediation](https://learn.microsoft.com/entra/architecture/id-protection-guide-analyze) — querying `AADUserRiskEvents`, `RiskyUsers`, and friends.
- [Azure Monitor Logs overview — KQL and Log Analytics](https://learn.microsoft.com/azure/azure-monitor/logs/data-platform-logs#kusto-query-language-kql-and-log-analytics) — language fundamentals and Simple mode vs KQL mode.
- [Conditional Access — Token Protection](https://learn.microsoft.com/entra/identity/conditional-access/concept-token-protection) — per-user enforcement KQL sample.

<!-- agent-owned sections end -->

## Notes (manual)
<!-- add manual notes below this line -->

---
*Last refreshed: 2026-04-19T10:45:00Z — entra-kb-curator*
