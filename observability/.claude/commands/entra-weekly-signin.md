---
description: Canned weekly sign-in health report. Fans out across sign-in tables and risky sign-ins via agent-coordinator.
argument-hint: (no arguments; uses last 7 days)
---

Invoke the `agent-coordinator` subagent with the following predefined
weekly sign-in health report request. Use the workspace resolved from
`workspaces.json` (defaulting to `defaultWorkspace`).

Request:

Generate a weekly Entra ID sign-in health report covering the last 7
days. Include the following sub-queries (route each to the appropriate
executor):

1. **Sign-in volume by day** (signin) — daily counts across
   `union SigninLogs, AADNonInteractiveUserSignInLogs`.
2. **Top 10 apps by sign-in count** (signin) — `AppDisplayName`.
3. **Failed sign-ins by ResultType / ResultDescription** (signin) — top 10
   failure reasons.
4. **Conditional Access denials** (signin) — `ConditionalAccessStatus ==
   "failure"`, group by `AppDisplayName` and policy.
5. **MFA challenge outcomes** (signin) — break down by
   `AuthenticationRequirement` and `Status.errorCode`.
6. **Risky sign-ins** (risk) — top risky users from `RiskyUsers` and
   recent `AADUserRiskEvents`.

Compose a single report with one section per sub-query.
