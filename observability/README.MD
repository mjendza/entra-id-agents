## About
The repository contains a multi-agent farm for querying Microsoft Entra ID
logs stored in a Log Analytics workspace. A central coordinator decomposes
user questions, asks a KB librarian for matching KQL patterns from `kb/`,
and dispatches executor specialists (one per data-source family) that run
the queries via Azure-Mcp.

## Architecture

```
User: /entra <question>
        |
        v
[main session]  --> agent-coordinator (Read/Glob/Grep/Agent)
                       |
                       +-- 1. agent-kb-curator   (read-only librarian for kb/)
                       |       returns matching KQL snippets, tagged by domain
                       |
                       +-- 2. executors in parallel:
                       |     - agent-signin-executor  -- SigninLogs, AADNonInteractive*, SP, ManagedIdentity, MicrosoftGraphActivityLogs
                       |     - agent-audit-executor   -- AuditLogs, AADProvisioningLogs
                       |     - agent-risk-executor    -- RiskyUsers, AADUserRiskEvents, Dalonso threat-hunt KQL
                       |       each: adapts KQL, runs via mcp__Azure-Mcp__monitor, returns Summary/Table/KQL
                       |
                       v
                  Coordinator composes a single response
                  (Overall summary + per-domain sections + Workspace line)
```

## Agents
- **`agent-coordinator`** — central orchestrator. Reads `workspaces.json`,
  asks the curator, dispatches executors in parallel, composes the final
  response.
- **`agent-kb-curator`** — read-only librarian for `kb/`. Returns
  candidate KQL snippets tagged by domain (`signin`, `audit`, `risk`,
  `threat-hunt`).
- **`agent-signin-executor`** — runs KQL against sign-in tables
  (`SigninLogs`, `AADNonInteractiveUserSignInLogs`,
  `AADServicePrincipalSignInLogs`, `AADManagedIdentitySignInLogs`,
  `MicrosoftGraphActivityLogs`).
- **`agent-audit-executor`** — runs KQL against directory-change tables
  (`AuditLogs`, `AADProvisioningLogs`).
- **`agent-risk-executor`** — runs KQL against Entra ID Protection
  tables (`RiskyUsers`, `AADUserRiskEvents`, etc.) and heavyweight
  threat-hunt patterns from `kb/Dalonso-Security-Repo/`.

## Slash commands
- **`/entra <question>`** — main entry point. Routes any Entra ID log
  question through `agent-coordinator`.
- **`/entra-weekly-signin`** — canned weekly sign-in health report.
- **`/entra-threat-hunt`** — canned threat-hunt sweep using
  `kb/Dalonso-Security-Repo/` patterns.
- **`/entra-audit-changes`** — canned directory-changes report (roles,
  apps, CA policies, user lifecycle, provisioning).
- **`/update-workspace <key>`** — discover Azure resource groups and Log
  Analytics workspaces via Azure-Mcp and populate `workspaces.json`.

## How to use

### MCP
Access to the Log Analytics workspace is via the Azure-Mcp server.
Configure it before the agents will work:

1. Copy `.mcp.ref.json` to `.mcp.json` and fill in your Azure credentials
   (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`,
   `AZURE_SUBSCRIPTION_ID`).
2. Copy `workspaces.ref.json` to `workspaces.json` or run
   `/update-workspace prod` to auto-discover and populate it.

Both `.mcp.json` and `workspaces.json` are gitignored — they contain
environment-specific values.

### Knowledge base (`kb/`)
The `kb/` directory holds the KQL patterns the curator searches:

- `kb/kql-entra-id/queries.kql` — foundational snippets curated from
  Microsoft Learn and Entra.news.
- `kb/kql-entra-id/README.md` — KQL idioms reference (CorrelationId
  dedupe, linkable identifiers, time windows).
- `kb/Dalonso-Security-Repo/Use Cases Threat Hunting/` — heavyweight
  threat-hunt master `.kql` files and numbered `.yaml` detection rules.
- `kb/AzureCustomDetections/` — additional analytic and hunting rules.

## Thank you
David Alonso for sharing extensive Entra ID Logs knowledge in the repo:
https://github.com/davidalonsod/Dalonso-Security-Repo
