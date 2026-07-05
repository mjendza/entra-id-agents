## About

The `ask-about-entra` farm produces **documents and solutions** for
Microsoft Entra ID, grounded in Microsoft Learn best practices and
informed by the latest entries from Entra-news. A central coordinator
asks a research librarian for MS Learn excerpts, dispatches specialist
authors (one per artifact type), runs a fact-check pass against the
excerpts, and writes the result to `solutions/<topic-slug>/`.

It is a complement to `../observability/`, which queries Entra ID logs
in a Log Analytics workspace. This farm answers: *"How should I design
/ configure / document &lt;Entra ID feature&gt; according to current
Microsoft guidance?"*

## Architecture

```
User: /entra-solution <topic>
        |
        v
[main session] --> agent-solution-coordinator (Read/Glob/Grep/Write/Agent)
                       |
                       +-- 1. agent-learn-librarian
                       |       MCP: microsoft-learn (search/fetch/code-samples)
                       |            entra-news-mcp (recent changes/deprecations
                       |                            + community tools)
                       |       returns JSON: excerpts (by deliverable),
                       |            recent_changes, community_tools
                       |
                       +-- 2. authors in parallel (only the requested ones):
                       |     - agent-design-author   -> design.md
                       |     - agent-runbook-author  -> runbook.md
                       |     - agent-iac-author      -> iac/main.bicep | main.tf
                       |     - agent-policy-author   -> policy/*.json | *.yaml
                       |
                       +-- 3. agent-doc-reviewer
                             fact-checks every draft against the excerpts;
                             coordinator allows one revision round per draft
                       v
                  Coordinator writes solutions/<slug>/ and posts a
                  short chat summary with links to each file.
```

### Closed-loop variant

`/entra-solution-loop` swaps the coordinator for
`agent-improvement-coordinator`, which runs the same baseline pipeline
above and then enters a quality-inspection loop driven by
`agent-quality-inspector`:

```
User: /entra-solution-loop <topic>
        |
        v
agent-improvement-coordinator
        |
        +-- baseline: librarian -> authors (parallel) -> agent-doc-reviewer
        |             (excerpts are cached and reused across the loop;
        |              librarian is NEVER called more than once)
        |
        +-- loop (up to 3 iterations):
              agent-quality-inspector  (Sonnet, holistic)
                  -> per-draft verdict {pass | improve}
                  -> hard_issues (must fix)
                  -> improvements (additive enhancements)
              -> re-dispatch flagged authors via the existing
                 `revision_notes:` channel, with HARD: / IMPROVE: prefixes
              exits on: all-pass | max-iterations | stagnation

        v
   Writes the usual artifacts plus solutions/<slug>/improvement-log.md
```

The inspector checks things the strict citation gate cannot: coverage
gaps against unused excerpts, cross-artifact consistency (param names,
policy filenames, CA policy names), deprecation propagation into every
draft, and example-variant completeness in the runbook. Use this when
the bundle is high-stakes; use plain `/entra-solution` when you want
the fast single-shot path.

## Agents

- **`agent-solution-coordinator`** — central orchestrator. Derives the
  topic slug, calls the librarian, dispatches authors in parallel,
  runs the reviewer, writes the artifacts.
- **`agent-learn-librarian`** — read-only research librarian. Queries
  Microsoft Learn (search → fetch → code samples) for authoritative docs
  and the Entra-news MCP (`search_entra_news` + `find_tool_mentions`) for
  community signal and recency. Returns a structured JSON block of
  excerpts tagged by deliverable type, plus a `recent_changes` list with
  deprecations flagged and a `community_tools` list of highlighted
  community tools/projects.
- **`agent-design-author`** — writes the architecture / design doc
  (Markdown). Content-only; returns a string.
- **`agent-runbook-author`** — writes the implementation runbook
  (Markdown, with portal + Microsoft Graph + Azure CLI variants where
  the excerpts support them).
- **`agent-iac-author`** — writes Bicep (default) or Terraform for
  Entra ID resources. Uses `microsoft_code_sample_search` when the
  librarian's excerpts don't already include a usable sample.
- **`agent-policy-author`** — writes ready-to-import policy / config
  templates (Conditional Access JSON, custom-role JSON,
  authentication-method policy JSON, entitlement-management YAML,
  etc.).
- **`agent-doc-reviewer`** — read-only fact-checker. Flags drafts that
  contain claims, commands, or schemas not supported by the librarian's
  excerpts. Coordinator allows one revision round per flagged draft.
- **`agent-improvement-coordinator`** — closed-loop peer of
  `agent-solution-coordinator`. Drives the `/entra-solution-loop`
  pipeline: same baseline draft + doc-review pass, then up to three
  inspector-driven revision rounds with cached excerpts. Writes an
  `improvement-log.md` alongside the usual artifacts.
- **`agent-quality-inspector`** — read-only quality inspector used by
  the closed-loop variant. Goes beyond citation checking: coverage
  gaps, cross-artifact consistency, deprecation propagation, and
  example-variant completeness. Returns per-draft verdicts of `pass`
  or `improve` plus `hard_issues` / `improvements` lists, with a
  stagnation flag the coordinator uses for early exit.
- **`agent-entra-architect`** — read-only Identity Architect for the
  lightweight `/simple-ask` path. Answers a single Entra ID question
  directly, grounded in Microsoft Learn (authoritative docs) and Entra
  News (recency + community tools), and returns a screen-ready summary
  with documentation and article links. Chat-only; writes no files and
  bypasses the coordinator/librarian pipeline.

## Slash commands

- **`/entra-solution <topic>`** — full bundle: design + runbook + IaC
  + policy.
- **`/entra-solution-loop <topic>`** — closed-loop full bundle. Same
  pipeline as `/entra-solution`, then up to three quality-inspector
  iterations (re-dispatching flagged authors with hard_issues +
  improvements) until every draft passes or the loop stagnates. Adds
  an `improvement-log.md` to the output folder.
- **`/entra-design <topic>`** — design doc only.
- **`/entra-runbook <topic>`** — runbook only.
- **`/entra-iac <topic>`** — IaC only (Bicep default; append
  `as terraform` to the topic for Terraform).
- **`/entra-policy <topic>`** — policy templates only.
- **`/simple-ask <question>`** — lightweight, chat-only Q&A. Answers a
  single Entra ID question as an Identity Architect (summary + Microsoft
  Learn and Entra News links) printed on screen. Writes no files and
  bypasses the solution-builder pipeline.

## How to use

### MCP

The `.mcp.json` at this directory wires up two MCPs:

- `microsoft-learn` (HTTP MCP at `https://learn.microsoft.com/api/mcp`)
- `entra-news-mcp` (npx-launched)

Both are enabled in `.claude/settings.local.json`, and their read tools
are pre-allowed so they don't prompt on every call: the Microsoft Learn
tools (`microsoft_docs_search`, `microsoft_docs_fetch`,
`microsoft_code_sample_search`) and the Entra-news tools
(`search_entra_news`, `find_tool_mentions`). Writes are pre-allowed only
under `solutions/**`.

`microsoft-learn` is the **authoritative** source (official docs,
schemas, code samples); `entra-news-mcp` is the **community + recency**
source (recent changes, deprecation signals, and community tools from
the weekly Entra News newsletter archive). Only `agent-learn-librarian`
calls these MCPs — every other agent works off its curated excerpts. On
first launch `entra-news-mcp` downloads a small SQLite archive; keyword
search works out of the box (semantic search additionally needs an
OpenAI key).

### Output layout

Each slash command writes a folder under `solutions/`:

```
solutions/
  <topic-slug>/
    README.md           # overview + recent-changes + community-tools + links
    design.md           # if `design` was requested
    runbook.md          # if `runbook` was requested
    iac/
      main.bicep        # or main.tf
      README.md         # apply instructions
    policy/
      ca-*.json         # one file per Conditional Access policy
      role-*.json       # custom-role definitions
      ...               # other policy artifacts as needed
    sources.md          # every MS Learn / Entra-news URL cited
    improvement-log.md  # only when built via /entra-solution-loop:
                        # one section per inspector iteration with the
                        # verdict per draft and the actions taken
```

`<topic-slug>` is derived from the user's topic (kebab-case,
filler-words stripped). If the slug already exists the coordinator
appends `-v2`, `-v3`, etc. — existing solutions are never overwritten.

### Grounding & deprecation handling

- Every non-obvious claim, command, resource type, and schema field in
  the generated artifacts traces back to an excerpt the librarian
  pulled. The reviewer flags fabrications.
- Every generated document includes a *Recent changes / deprecations*
  section sourced from the Entra-news MCP for the last 90 days, with
  deprecations called out explicitly.
- When the Entra-news MCP surfaces relevant community tools/projects for
  the topic, the solution README gains a *Community tools* section
  linking each one.
- If MS Learn / Entra-news return nothing usable for a topic, the
  coordinator stops before dispatching authors and asks the user to
  broaden the topic.

## Thank you

Microsoft Learn for the public MCP endpoint, and the maintainers of
[`entra-news-mcp`](https://www.npmjs.com/package/entra-news-mcp) for
keeping deprecation signals one MCP call away.
