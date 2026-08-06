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
`permission_denied` results are fine — proceed with docs only. If the
lookup agent cannot be spawned at all (e.g. its MCP server isn't
configured, so its tool list resolves to nothing), treat that as
`{"status":"auth_unavailable","detail":"<the error>"}` and continue —
do not retry it and do not try to substitute another agent.

## Step 2a: stage the grounding to disk (do this once)

The grounding JSON is consumed by up to six dispatches. Re-pasting it
into each one duplicates thousands of tokens per round, so write it
**once** and pass paths thereafter:

- `Write` the verbatim `agent-graph-docs` JSON to
  `<scratchpad>/graph_docs.json`.
- `Write` the verbatim `agent-graph-tenant-lookup` JSON (or
  `{"status":"no_identifier"}` / the `auth_unavailable` object) to
  `<scratchpad>/tenant_shape.json`.

`<scratchpad>` is the session scratchpad directory from your
environment — never inside `generated/`. Write the fetcher output
**verbatim**: do not summarize, re-key, or "clean up" the JSON on the
way in. These two files are the single source of grounding truth for
every dispatch below.

## Step 3: dispatch the generator

Issue **one** `Agent` call:

- `subagent_type: agent-tf-generator`, prompt body:
  ```
  requirement: <verbatim>
  provider_choice: <azuread | msgraph_resource>
  graph_docs_path: <scratchpad>/graph_docs.json
  tenant_shape_path: <scratchpad>/tenant_shape.json
  ```

Pass paths, not inlined JSON. Both the generator and the reviewer
`Read` these files themselves.

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
     graph_docs_path: <scratchpad>/graph_docs.json
     tenant_shape_path: <scratchpad>/tenant_shape.json
     ```
     Add a `confirmed_facts:` list for anything you verified yourself
     out-of-band (a provider argument, an api_version), so the reviewer
     spends its fetch budget on what's still unknown instead of
     re-checking settled ground. On round 2+, also list which prior
     findings were fixed so it doesn't re-raise them.

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

   Keep revision rounds cheap and correct:

   - **Fold in what you can verify yourself.** If a finding hinges on a
     fact you can check directly — a Terraform provider argument or
     resource type (the registry renders client-side; fetch
     `raw.githubusercontent.com/<owner>/<provider-repo>/main/docs/...`
     instead), or whether an endpoint is beta-only — check it and pass
     the answer as a CONFIRMED fact in `revision_notes`. Telling the
     generator the answer costs a fraction of letting it search, and it
     stops the reviewer re-flagging the same item next round.
   - **Vet the reviewer's proposed diff before relaying it.** It is a
     recommendation, not a verdict. If a proposed fix is wrong or a
     no-op, say so explicitly in the revision note and state the
     correct fix instead — do not pass through a change that would ship
     a false sense of safety.
   - **Batch every finding into one round.** Never spend a round on a
     single finding when several are open.
   - **Don't re-litigate settled items.** Each round, tell the reviewer
     which findings are already fixed and which facts are CONFIRMED.

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

Write exactly two files into the project (plus the Step 2a scratchpad
grounding files, which are throwaway):

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

## Cost discipline

This pipeline can spend hundreds of thousands of tokens if the loop is
run loosely. Past failure mode: a single generator draft made 61 tool
calls and cost 345k tokens, and an under-fetching reviewer forced two
extra rounds. Keep it tight:

- **The generator authors; it does not research.** It gets 1
  code-sample search on a first draft and **0** on revisions. If a
  reply shows it searching repeatedly, that is the bug — supply the
  missing fact as a CONFIRMED note rather than dispatching it again.
- **The reviewer should spend its fetch budget.** Up to 4 fetches, and
  under-verifying is the expensive error: one unverified endpoint costs
  a whole extra generator round.
- **Round 1 should usually be enough.** Two rounds is normal for a
  multi-resource requirement; three means grounding was thin — note in
  Step 6 what was missing.
- **Never dispatch an agent to learn something you can check in one
  tool call yourself.**

## Safety rails

- Never modify `.mcp.json` or `.claude/`. The only project writes are
  the two files in `generated/<slug>/`; the Step 2a grounding files go
  to the session scratchpad, never into the repo.
- Never echo credentials from `.mcp.json` (CLIENT_SECRET, etc.).
- Never run `terraform apply` or any Graph write. The tenant is only
  touched by the lookup agent's single read-only GET; the generated
  files are for the user to review, plan, and apply themselves.
