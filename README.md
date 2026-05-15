# Entra ID Agents

A collection of multi-agent Claude Code "farms" for Microsoft Entra ID
work. Each subdirectory is a self-contained project with its own
agents, slash commands, and MCP configuration.

## Projects

### [`observability/`](./observability/)
Multi-agent farm for querying **Microsoft Entra ID logs** stored in a
Log Analytics workspace. A coordinator decomposes user questions, asks
a KB librarian for matching KQL patterns from `kb/`, and dispatches
executor specialists (sign-in, audit, risk / threat-hunt) that run
queries via Azure-MCP.

Entry points:
- `/entra <question>` — main entry; routes through `agent-coordinator`.
- `/entra-weekly-signin`, `/entra-threat-hunt`, `/entra-audit-changes`
  — canned reports.
- `/update-workspace <key>` — auto-discover Azure resource group +
  Log Analytics workspace.

### [`entra-as-code/`](./entra-as-code/)
Multi-agent reviewer for **Terraform resources** using the
`microsoft/microsoft-graph` provider (`msgraph_*`). A coordinator
parses a pasted HCL block, dispatches a docs fetcher
(`microsoft-learn` MCP) and a live-tenant GET (`Lokka-Microsoft` MCP)
in parallel, then hands the results to a reviewer that produces
findings and a proposed unified diff. Read-only — no `.tf` edits.

Entry point:
- `/tf-msgraph-review <pasted msgraph_* resource block>`

## Conventions

Both projects share the same pattern:

- `<project>/.claude/agents/agent-*.md` — agent definitions.
- `<project>/.claude/commands/*.md` — slash commands.
- `<project>/.claude/settings.local.json` — MCP enablement +
  pre-allowed tool permissions.
- `<project>/.mcp.json` — environment-specific MCP server config
  (gitignored).
- `<project>/.mcp.ref.json` — reference template with empty
  credentials. Copy to `.mcp.json` and fill in.

The repo `.gitignore` excludes `.mcp.json` and `workspaces.json`
from every subdirectory, so credentials and workspace IDs stay local.
