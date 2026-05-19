---
description: Generate ready-to-import Entra ID policy / config templates — Conditional Access JSON, custom roles, claims-mapping policies, auth-method policies, entitlement-management YAML — for a topic. Single-deliverable variant of /entra-solution.
argument-hint: <topic, e.g. "Block legacy authentication and require MFA for admins">
---

Invoke the `agent-solution-coordinator` subagent with the following
prompt body. Only the policy author will be dispatched; the coordinator
will still call the librarian and the reviewer.

Prompt body to pass to the coordinator:

```
topic: $ARGUMENTS
deliverables: policy
```
