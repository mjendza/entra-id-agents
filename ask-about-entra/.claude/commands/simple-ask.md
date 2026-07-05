---
description: Ask a single Entra ID question and get an Identity Architect answer on screen — concise summary plus Microsoft Learn docs and Entra News article links. Read-only, writes no files.
argument-hint: <question, e.g. "list all authentication strengths for a Conditional Access policy">
---

Invoke the `agent-entra-architect` subagent with the question below. The agent answers as a
senior Entra ID Identity Architect, grounding its response in Microsoft Learn (authoritative
docs) and Entra News (recency + community), and returns a screen-ready Markdown answer with
a summary plus documentation and article links.

When the agent returns, **relay its answer to the user verbatim** — do not summarize,
truncate, or re-wrap it, and do not write any files. The agent's message is already formatted
for display.

Question to pass to the agent:

```
$ARGUMENTS
```
