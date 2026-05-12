---
description: Canned threat-hunt sweep using kb/Dalonso threat-hunting patterns. Fans out across signin, NonInteractive, ADFS, and risk tables via agent-coordinator.
argument-hint: (no arguments; uses last 7 days)
---

Invoke the `agent-coordinator` subagent with the following predefined
threat-hunt sweep. Use the workspace resolved from `workspaces.json`
(defaulting to `defaultWorkspace`).

Request:

Run a threat-hunt sweep across Entra ID telemetry for the last 7 days
using patterns from `kb/Dalonso-Security-Repo/Use Cases Threat Hunting/`.
Include these sub-hunts (route each to `agent-risk-executor`, except
where noted):

1. **Token theft / refresh-token replay from new location**
   (threat-hunt) — use `kb/.../AadNonInteractiveUserSigninLogs/01-TokenTheft-RefreshTokenReplayNewLocation.yaml`.
2. **Impossible travel** (threat-hunt) — pattern from
   `kb/.../SigninLogs-ThreatHunting/`.
3. **ADFS extranet lockout / sustained brute force** (threat-hunt) —
   pattern from `kb/.../ADFSSignInLogs/`.
4. **NonInteractive sign-in anomalies** (threat-hunt) — master pattern in
   `kb/.../AadNonInteractiveUserSigninLogs/AADNonInteractiveUserSignInLogs-ThreatHunting.kql`.
5. **Risky users summary** (risk) — top users from `RiskyUsers` joined
   with recent `AADUserRiskEvents`.

Cap each hunt at `| take 50` to keep latency manageable. Compose a single
report with one section per hunt, citing the `kb/` source for each.
