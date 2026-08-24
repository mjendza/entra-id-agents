---
description: What changed in Microsoft Entra ID over the last 30 days — a de-duplicated table with scope/area, change type, short summaries and reference links, plus a longer write-up per change. Fixed 30-day window, no argument needed. Read-only, writes no files.
---

Invoke the `agent-entra-change-tracker` subagent with the prompt body below. The agent runs
`scripts/entra-feeds.py` to pull every RSS/Atom channel configured in
`.claude/feeds/entra-feeds.json`, filters to the last 30 days, merges changes that appear in
more than one channel, cross-checks against Entra News, then classifies each change by
scope/area and writes a short and a long summary for it.

When the agent returns, **relay its answer to the user verbatim** — do not summarize,
truncate, or re-wrap it, and do not write any files. The agent's message is already formatted
for display.

A 30-day window returns noticeably more rows than the weekly one. Keep the table sorted
newest first and keep deprecations, retirements and breaking changes pinned to the top of
their day so the important items stay findable in a longer list.

This command takes no arguments; the window is fixed. For a different window use
`/entra-changes-week` (7 days) or `/last-entra-changes <window>`.

Prompt body to pass to the agent:

```
window: 30d
```
