---
description: Query Entra ID / Azure AD logs in Log Analytics via the agent-entra-log-helper subagent.
argument-hint: <question, e.g. "active users last 7d">
---

Invoke the `agent-entra-log-helper` subagent to answer the following question
against the Log Analytics workspace resolved from `workspaces.json`
(defaulting to `defaultWorkspace` unless the question names another workspace):

$ARGUMENTS
