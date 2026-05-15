---
description: Review a single Terraform resource block from the microsoft/microsoft-graph provider (msgraph_*) against the Graph REST docs and the live tenant. Returns findings + a proposed unified diff. Read-only.
argument-hint: <paste a single msgraph_* HCL resource block>
---

Invoke the `agent-tf-coordinator` subagent to review the following
Terraform resource block.

The coordinator will:

1. Parse the block (resource type, attributes, identifier hint).
2. Dispatch `agent-graph-docs` and `agent-graph-tenant-lookup` **in
   parallel** to fetch the Microsoft Graph REST schema, the
   `microsoft/microsoft-graph` Terraform provider schema, and the
   live tenant shape (best-effort).
3. Dispatch `agent-tf-reviewer` to compare the block against both
   schemas and the tenant shape, and produce Findings + a proposed
   unified diff.

Read-only: nothing is applied; the diff is for the user to review and
apply manually.

User-pasted resource block:

$ARGUMENTS
