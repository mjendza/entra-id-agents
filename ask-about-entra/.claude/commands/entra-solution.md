---
description: Build a full Entra ID solution bundle (design + runbook + IaC + policy). Dispatches via agent-solution-coordinator, grounded in Microsoft Learn and Entra news.
argument-hint: <topic, e.g. "passwordless rollout for 1000-user tenant">
---

Invoke the `agent-solution-coordinator` subagent with the following
prompt body. The coordinator will ask `agent-learn-librarian` for MS
Learn + Entra-news excerpts, dispatch the design / runbook / IaC /
policy authors in parallel, run `agent-doc-reviewer`, then write the
artifacts under `solutions/<slug>/` and post a chat summary.

Prompt body to pass to the coordinator:

```
topic: $ARGUMENTS
deliverables: design, runbook, iac, policy
iac_flavor: bicep
```
