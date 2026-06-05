---
description: Closed-loop Entra ID solution bundle — runs the full design + runbook + IaC + policy pipeline, then iterates with a quality inspector (up to 3 rounds) until every draft passes or the loop stagnates.
argument-hint: <topic, e.g. "passwordless rollout for 1000-user tenant">
---

Invoke the `agent-improvement-coordinator` subagent with the following
prompt body. The coordinator will ask `agent-learn-librarian` for MS
Learn + Entra-news excerpts (once, cached), dispatch the design /
runbook / IaC / policy authors in parallel, run `agent-doc-reviewer`
for the strict citation gate, then loop with `agent-quality-inspector`
— re-dispatching authors with the inspector's hard_issues + improvements
— until every draft passes or 3 inspector iterations have run.

Output lands under `solutions/<topic-slug>/` with the usual files plus
an `improvement-log.md` summarizing each iteration.

Prompt body to pass to the coordinator:

```
topic: $ARGUMENTS
deliverables: design, runbook, iac, policy
iac_flavor: bicep
max_iterations: 3
```
