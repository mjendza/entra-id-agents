---
description: Generate Terraform (typed azuread_* or generic msgraph_resource) from a natural-language requirement, grounded in Microsoft Learn docs and the live tenant, quality-gated by the reviewer, and written to generated/<slug>/. Read-only toward the tenant — nothing is applied.
argument-hint: <requirement, e.g. "create Intune policy for Enterprise Android" or "create Cloud PKI certification authority">
---

Generate Terraform for the requirement below. You (the main session)
orchestrate directly — do not invoke `agent-tf-coordinator`.

Requirement:

$ARGUMENTS

## Step 1: parse the requirement, pick provider and slug

- Derive a short kebab-case `slug` from the requirement (e.g.
  `intune-android-enterprise-policy`). Output folder:
  `generated/<slug>/`.
- Pick `provider_choice` from this decision table:
  - **`azuread`** (typed `hashicorp/azuread` resources) if the
    requirement is a core directory object the provider covers:
    application / app registration, service principal, group, user,
    conditional access policy, named location, directory role
    assignment, app role assignment, invitation / guest user,
    administrative unit.
  - **`msgraph_resource`** (generic `Microsoft/msgraph` provider:
    `url` / `api_version` / `body`) for everything else — Intune /
    deviceManagement (policies, configurations, compliance), Cloud PKI,
    authentication event flows / user flows, authentication methods
    policy, cross-tenant access, lifecycle workflows, and any
    beta-only surface.
  - If the user names a provider explicitly in the requirement, honor
    it; if the named provider cannot express the requirement, say so
    and use the other one.

## Step 2: dispatch fetchers in parallel

In **one assistant message**, issue exactly two `Agent` calls:

- `subagent_type: agent-graph-docs`, prompt body (requirement mode):
  ```
  requirement: <the requirement, verbatim>
  provider_choice: <azuread | msgraph_resource>
  ```
- `subagent_type: agent-graph-tenant-lookup`, prompt body. If you can
  already guess the Graph collection path (e.g.
  `deviceManagement/deviceConfigurations`), use direct-URL sample mode:
  ```
  graph_url: <collection path, no leading slash>
  api_version: <v1.0 | beta — best guess; the GET is best-effort>
  identifier_hint: null
  ```
  If you cannot guess a path, skip this call and treat the tenant
  shape as `{"status": "no_identifier"}`.

The tenant lookup is best-effort: `auth_unavailable`, `not_found`, or
`permission_denied` results are fine — proceed with docs only.

## Step 3: dispatch the generator

Issue **one** `Agent` call:

- `subagent_type: agent-tf-generator`, prompt body:
  ```
  requirement: <verbatim>
  provider_choice: <azuread | msgraph_resource>
  graph_docs: |
    <verbatim JSON from agent-graph-docs>
  tenant_shape: |
    <verbatim JSON from agent-graph-tenant-lookup, or {"status":"no_identifier"}>
  ```

Pass the fetcher outputs verbatim — do not summarize or rewrite them.

## Step 4: closed-loop quality gate

Extract the ` ```hcl ` block from the generator's reply and dispatch
the reviewer:

- `subagent_type: agent-tf-reviewer`, prompt body:
  ```
  original_block: |
    <the generated resource block(s)>
  graph_docs: |
    <same verbatim JSON as Step 3>
  tenant_shape: |
    <same verbatim JSON as Step 3>
  ```

- If the reviewer reports only `info` findings (or none), or its diff
  says `# No changes proposed.` (warnings that are pure caveats — beta
  surface, license/permission notes — need no revision): accept the
  draft as final.
- If it reports `error` or `warning` findings **with diff changes**:
  re-dispatch
  `agent-tf-generator` **once**, adding to the Step 3 prompt body:
  ```
  prior_draft: |
    <the generator's previous hcl block, verbatim>
  revision_notes:
    - <one line per error/warning finding>
  ```
  Accept the revised draft as final. **Max one revision round** — do
  not loop again even if findings remain; surface them instead.

## Step 5: write files

Write exactly two files (the only writes this command makes):

- `generated/<slug>/main.tf` — the final ` ```hcl ` block content.
- `generated/<slug>/README.md` — the generator's ` ```markdown `
  apply-instructions block content.

## Step 6: respond

Report to the user:

1. The file paths written.
2. The final HCL (fenced).
3. The reviewer's findings — including any that the revision pass
   fixed and any that remain open.
4. References (doc URLs from the fetchers).

## Safety rails

- Never modify `.mcp.json`, `.claude/`, or anything outside
  `generated/<slug>/`.
- Never echo credentials from `.mcp.json` (CLIENT_SECRET, etc.).
- Never run `terraform apply` or any Graph write. The tenant is only
  touched by the lookup agent's single read-only GET; the generated
  files are for the user to review, plan, and apply themselves.
