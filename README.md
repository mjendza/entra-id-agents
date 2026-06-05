# Entra ID Agents

Entra ID administration is broad and fast-moving — querying sign-in and
audit logs, reviewing infrastructure-as-code, and producing design docs
/ runbooks / policies that stay current with Microsoft guidance. These
agents encode that work so it can be done consistently and repeatably,
grounded in live tenant data and Microsoft Learn rather than memory.

This is the **first version** of these agents, and it is intentionally
shipped *as code* — agent definitions, slash commands, and MCP wiring
all live in the repo. Keeping it as code makes it far easier to
iterate on, review, and maintain while the patterns are still settling.
The **future plan is to surface these agents in a UI** once the
behaviors have stabilized.

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

### [`ask-about-entra/`](./ask-about-entra/)
Multi-agent farm that produces **documents and solutions** for Entra
ID, grounded in Microsoft Learn best practices and informed by recent
Entra-news entries. A coordinator asks a research librarian for MS
Learn excerpts, dispatches specialist authors (design, runbook, IaC,
policy) in parallel, fact-checks every draft against those excerpts,
and writes the result to `solutions/<topic-slug>/`. A closed-loop
variant adds a quality-inspection loop for high-stakes bundles.

Entry points:
- `/entra-solution <topic>` — full bundle: design + runbook + IaC +
  policy.
- `/entra-solution-loop <topic>` — closed-loop full bundle with up to
  three quality-inspector iterations; adds an `improvement-log.md`.
- `/entra-design`, `/entra-runbook`, `/entra-iac`, `/entra-policy`
  `<topic>` — single-artifact variants.

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
