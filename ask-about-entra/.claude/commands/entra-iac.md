---
description: Generate Infrastructure-as-Code (Bicep by default, append "as terraform" to switch) for an Entra ID topic — Conditional Access, app registrations, named locations, custom roles, etc. Single-deliverable variant of /entra-solution.
argument-hint: <topic, optionally with "as terraform", e.g. "named locations and CA blocks for high-risk countries">
---

Invoke the `agent-solution-coordinator` subagent with the following
prompt body. Only the IaC author will be dispatched; the coordinator
will still call the librarian and the reviewer.

If the user's topic ends with `as terraform`, strip that suffix and
set `iac_flavor: terraform`. Otherwise default to Bicep.

Prompt body to pass to the coordinator:

```
topic: $ARGUMENTS
deliverables: iac
iac_flavor: bicep
```
