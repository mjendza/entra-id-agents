---
description: Ask any question about Entra ID / Azure AD logs. Dispatches via agent-coordinator across the executor farm (sign-in, audit, risk, threat-hunt).
argument-hint: <question or report request, e.g. "failed sign-ins and role changes last 24h">
---

Invoke the `agent-coordinator` subagent to answer the following question
against the Log Analytics workspace resolved from `workspaces.json`
(defaulting to `defaultWorkspace` unless the question names another
workspace).

The coordinator will:

1. Resolve the workspace.
2. Ask `agent-kb-curator` for matching KQL snippets from `kb/`.
3. Decompose into sub-questions and dispatch executors
   (`agent-signin-executor`, `agent-audit-executor`,
   `agent-risk-executor`) in parallel.
4. Compose a single response with per-domain sections.

User question:

$ARGUMENTS
