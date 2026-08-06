---
description: Generate Terraform (typed azuread_* or generic msgraph_resource) from a natural-language requirement, grounded in Microsoft Learn docs and the live tenant, quality-gated by a generate→review→revise loop (up to 3 rounds; the reviewer independently re-fetches the Graph create doc, since terraform validate/plan cannot check msgraph_resource bodies), and written to generated/<slug>/. Read-only toward the tenant — nothing is applied.
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

## Step 4: closed-loop quality gate (up to 3 rounds)

`terraform validate`/`plan` cannot check a `msgraph_resource` body —
the provider treats it as an opaque map, and a wrong body only fails
as a 400 at apply time. The reviewer's independent doc verification
is therefore the only pre-apply check of the Graph request, and every
revised draft must go back through it.

Loop **generator → reviewer**, at most **3 rounds total** (initial
draft + 2 revisions):

1. Extract the ` ```hcl ` block from the generator's reply and
   dispatch the reviewer:

   - `subagent_type: agent-tf-reviewer`, prompt body:
     ```
     original_block: |
       <the generated resource block(s)>
     graph_docs: |
       <same verbatim JSON as Step 3>
     tenant_shape: |
       <same verbatim JSON as Step 3>
     ```

2. **Accept** the draft as final if the reviewer reports no `error`
   findings and no `warning` findings **with diff changes** — i.e.
   only `info` findings, pure-caveat warnings (beta surface,
   license/permission notes, missing-validation-block warnings you
   choose to keep), or a diff that says `# No changes proposed.`
   For a conditional access policy, acceptance additionally requires
   a security summary to exist (the reviewer's `### Security summary`
   or the README's `## Security summary`); a missing summary is a
   revision note like any other finding — it consumes a round from
   the same 3-round cap, never an extra dispatch.

3. Otherwise, if rounds remain, re-dispatch `agent-tf-generator` with
   the Step 3 prompt body plus:
   ```
   prior_draft: |
     <the generator's previous hcl block, verbatim>
   revision_notes:
     - <one line per error/warning finding>
   ```
   Then go back to 1: **the revised draft is re-dispatched to the
   reviewer** — never accept a revision unreviewed.

4. If `error` findings remain after round 3: stop looping, but do NOT
   silently accept. Prepend this comment block to the final HCL
   before writing it in Step 5, and repeat the findings in Step 6:
   ```hcl
   # KNOWN ISSUES (unresolved review findings):
   # - [error] <finding>
   # ...
   # Review these against the cited docs before terraform apply —
   # terraform validate/plan will NOT catch body errors.
   ```

## Step 5: write files

Write exactly two files (the only writes this command makes):

- `generated/<slug>/main.tf` — the final ` ```hcl ` block content.
- `generated/<slug>/README.md` — the generator's ` ```markdown `
  apply-instructions block content.

## Step 6: respond

Report to the user:

1. The file paths written.
2. The final HCL (fenced).
3. The reviewer's findings — how many review rounds ran, which
   findings the revision passes fixed, and any that remain open.
   Remind the user that `terraform validate`/`plan` cannot validate a
   `msgraph_resource` body, so open `error` findings mean the apply
   will likely fail with a Graph 400.
4. References (doc URLs from the fetchers).
5. **If the requirement is a conditional access policy**: the
   **Security summary** — surface the reviewer's `### Security
   summary` section (falling back to the README's `## Security
   summary`) verbatim and prominently, directly after the HCL. No
   extra dispatches here — the Step 4 acceptance gate already
   guarantees it exists; if rounds were exhausted without one, say
   so alongside the KNOWN ISSUES block instead.

## Safety rails

- Never modify `.mcp.json`, `.claude/`, or anything outside
  `generated/<slug>/`.
- Never echo credentials from `.mcp.json` (CLIENT_SECRET, etc.).
- Never run `terraform apply` or any Graph write. The tenant is only
  touched by the lookup agent's single read-only GET; the generated
  files are for the user to review, plan, and apply themselves.
