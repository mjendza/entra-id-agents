---
description: What changed in Microsoft Entra ID over the last 7 days — a de-duplicated table with scope/area, change type, short summaries and reference links, plus a longer write-up per change. Fixed 7-day window, no argument needed. Read-only, writes no files.
---

Invoke the `agent-entra-change-tracker` subagent with the prompt body below. The agent runs
`scripts/entra-feeds.py` to pull every RSS/Atom channel configured in
`.claude/feeds/entra-feeds.json`, filters to the last 7 days, merges changes that appear in
more than one channel, cross-checks against Entra News, then classifies each change by
scope/area and writes a short and a long summary for it.

When the agent returns, **relay its answer to the user verbatim** — do not summarize,
truncate, or re-wrap it, and do not write any files. The agent's message is already formatted
for display.

This command takes no arguments; the window is fixed. For a different window use
`/entra-changes-month` (30 days) or `/last-entra-changes <window>`.

Prompt body to pass to the agent:

```
window: 7d
```
