---
description: Produce an Entra ID architecture / design document (Markdown) for a topic, grounded in Microsoft Learn and Entra news. Single-deliverable variant of /entra-solution.
argument-hint: <topic, e.g. "Conditional Access for high-privilege admins">
---

Invoke the `agent-solution-coordinator` subagent with the following
prompt body. Only the design author will be dispatched; the coordinator
will still call the librarian and the reviewer.

Prompt body to pass to the coordinator:

```
topic: $ARGUMENTS
deliverables: design
```
