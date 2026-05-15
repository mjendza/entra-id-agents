---
description: Canned directory-changes report for Entra ID. Summarizes role assignments, app/SP creations, CA policy changes, and user lifecycle events via agent-coordinator.
argument-hint: (no arguments; uses last 7 days)
---

Invoke the `agent-coordinator` subagent with the following predefined
directory-changes report request. Use the workspace resolved from
`workspaces.json` (defaulting to `defaultWorkspace`).

Request:

Summarize Entra ID directory changes for the last 7 days. Include the
following sub-queries (route each to `agent-audit-executor`):

1. **Role assignments** (audit) — `AuditLogs` with `OperationName contains
   "role"`; project initiator, target, role name.
2. **Application / service principal creations** (audit) — `AuditLogs`
   with `Category == "ApplicationManagement"` and OperationName for app
   or SP create / consent.
3. **Conditional Access policy changes** (audit) — `AuditLogs` with
   `Category == "Policy"` and OperationName containing CA-related verbs.
4. **User lifecycle events** (audit) — `AuditLogs` with `OperationName
   contains "user"` (Add / Update / Delete user). Show counts by
   operation and initiator.
5. **Provisioning events** (audit) — `AADProvisioningLogs` summary of
   inbound / outbound provisioning outcomes.

Compose a single report with one section per sub-query.
