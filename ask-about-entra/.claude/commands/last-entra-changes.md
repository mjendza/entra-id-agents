---
description: Report what changed in Microsoft Entra ID over the last 7 or 30 days — a de-duplicated table with scope/area, change type, short summaries and reference links, plus a longer write-up per change. Sourced from your configured RSS channels. Read-only, writes no files.
argument-hint: "[7d|30d] (default 7d)"
---

Invoke the `agent-entra-change-tracker` subagent with the prompt body below. The agent runs
`scripts/entra-feeds.py` to pull every RSS/Atom channel configured in
`.claude/feeds/entra-feeds.json`, filters to the requested window, merges changes that appear
in more than one channel, cross-checks against Entra News, then classifies each change by
scope/area and writes a short and a long summary for it.

When the agent returns, **relay its answer to the user verbatim** — do not summarize,
truncate, or re-wrap it, and do not write any files. The agent's message is already formatted
for display.

Prompt body to pass to the agent (if no window was given, `7d` is the default):

```
window: $ARGUMENTS
```
