---
description: Ask a single Entra ID question and get an Identity Architect answer on screen — concise summary plus Microsoft Learn docs and Entra News article links. The question may also reference local files (e.g. an exported tenant config to review). Read-only, writes no files.
argument-hint: <question, e.g. "list all authentication strengths for a Conditional Access policy">
---

Invoke the `agent-entra-architect` subagent with the question below. The agent answers as a
senior Entra ID Identity Architect, grounding its response in Microsoft Learn (authoritative
docs) and Entra News (recency + community), and returns a screen-ready Markdown answer with
a summary plus documentation and article links.

The question can be anything Entra ID related — a plain how-to or enumeration question needs
no extra handling: pass it through as-is.

Only if the question happens to reference local files or a folder (an exported tenant config,
a policy JSON, a log, a script — whatever it is), resolve that reference to an **absolute
path** first (Glob it to confirm it exists and note roughly what's there), and append a short
context block to the question you pass:

> Context: the files the question refers to live under `{absolute path}` ({count} files,
> {brief shape}). Read all of them before forming conclusions.

Do not enumerate every file path yourself — the agent has Glob and discovers the files. Do
not read or summarize the files yourself; the agent does the analysis.

When the agent returns, **relay its answer to the user verbatim** — do not summarize,
truncate, or re-wrap it, and do not write any files. The agent's message is already formatted
for display.

Question to pass to the agent:

```
$ARGUMENTS
```
