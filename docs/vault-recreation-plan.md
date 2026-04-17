# Vault Recreation Plan — obsidian-nexus

> Self-contained guide to recreate the Obsidian Nexus vault from scratch in any environment.
> Every directory, file, template, skill, and config is included verbatim below.
> An AI agent or human can follow this linearly to produce an identical vault.

---

## Prerequisites

- Git installed
- Obsidian installed (desktop app)
- A terminal with `mkdir -p` support (bash, zsh, Git Bash on Windows)

---

## Step 1: Create directory structure

```bash
VAULT="$HOME/obsidian-nexus"   # adjust path as needed

mkdir -p "$VAULT"
cd "$VAULT"

# Core directories
mkdir -p _system
mkdir -p _inbox/clips _inbox/imports _inbox/screenshots _inbox/voice
mkdir -p atlas/concepts atlas/entities atlas/patterns atlas/guides
mkdir -p sources/articles sources/papers sources/books sources/conversations
mkdir -p projects
mkdir -p areas/engineering areas/home-automation
mkdir -p daily
mkdir -p templates
mkdir -p .skills
mkdir -p .githooks
mkdir -p .obsidian
```

---

## Step 2: Add .gitkeep files (preserve empty folders in git)

```bash
for dir in \
  atlas/concepts atlas/entities atlas/patterns atlas/guides \
  sources/articles sources/papers sources/books sources/conversations \
  projects daily \
  areas/engineering areas/home-automation \
  _inbox/clips _inbox/imports _inbox/screenshots _inbox/voice; do
  touch "$VAULT/$dir/.gitkeep"
done
```

---

## Step 3: System files

### `_system/index.md`

```markdown
---
title: "Master Index"
type: source
status: evergreen
provenance: synthesized
summary: "Auto-maintained catalog of all vault content by type and domain"
---

# Vault Index

> This file is maintained by LLM agents. Do not edit manually unless correcting errors.

## Concepts
<!-- atlas/concepts/ — Mental models, frameworks, theories -->

## Entities
<!-- atlas/entities/ — People, orgs, tools, technologies -->

## Patterns
<!-- atlas/patterns/ — Reusable solutions, best practices -->

## Guides
<!-- atlas/guides/ — How-tos, playbooks, runbooks -->

## Sources
<!-- sources/ — Processed source summaries -->

## Projects
<!-- projects/ — Active project workspaces -->

## Areas
<!-- areas/ — Ongoing responsibility areas -->

## Decisions
<!-- ADRs across all projects -->
```

### `_system/taxonomy.md`

```markdown
---
title: "Taxonomy"
type: source
status: evergreen
provenance: human
summary: "Controlled vocabulary for all frontmatter enum fields"
---

# Taxonomy — Controlled Vocabulary

> All agents MUST use values from this file. Propose additions via `_system/log.md` before using new terms.

## type
- `concept` — Ideas, frameworks, theories, mental models
- `entity` — People, organizations, tools, technologies, products
- `decision` — Architecture Decision Records (ADRs)
- `pattern` — Reusable solutions, best practices, recurring approaches
- `guide` — How-tos, playbooks, runbooks, tutorials
- `source` — Processed summaries of articles, papers, books, conversations
- `daily` — Daily notes
- `project` — Project overviews and workspaces
- `area` — Ongoing responsibility areas

## status
- `seed` — Stub or newly created, minimal content
- `growing` — Being actively enriched, not yet stable
- `evergreen` — Stable, reviewed, reliable reference
- `archived` — No longer current, kept for history

## domain
- `engineering` — Code, architecture, tooling, DevOps, databases, APIs, systems
- `polymath` — Science, philosophy, mental models, learning, broad knowledge
- `professional` — Work projects, career, business, meetings, deliverables
- `home-automation` — IoT, home control, sensors, Jarvis project

## provenance
- `human` — Written by a human (highest trust)
- `extracted` — LLM pulled directly from a source document
- `synthesized` — LLM combined information from multiple sources
- `inferred` — LLM's own reasoning, not directly from any source (lowest trust)

## confidence
- `high` — Verified, well-sourced, or from authoritative source
- `medium` — Plausible, single source, or partially verified
- `low` — Uncertain, contradicted, or speculative

## tags (initial vocabulary)

### Engineering
- `architecture`, `api`, `database`, `devops`, `docker`, `git`
- `python`, `rust`, `typescript`, `go`
- `llm`, `embeddings`, `rag`, `vector-db`
- `n8n`, `ollama`, `obsidian`
- `networking`, `security`, `performance`

### Polymath
- `mental-model`, `philosophy`, `science`, `mathematics`
- `learning`, `productivity`, `creativity`
- `books`, `papers`, `articles`

### Professional
- `project-management`, `career`, `meeting-notes`
- `stakeholder`, `deliverable`, `deadline`

### Home Automation
- `iot`, `sensors`, `voice-control`, `jarvis`
- `steam-deck`, `llama`, `automation`
```

### `_system/log.md`

```markdown
---
title: "Operation Log"
type: source
status: evergreen
provenance: synthesized
summary: "Chronological append-only record of all vault operations"
---

# Operation Log

> Append-only. Each entry starts with `## [YYYY-MM-DD] action | details` for parseable history.
> `grep "^## \[" _system/log.md | tail -10` shows last 10 operations.

## [YYYY-MM-DD] init | Vault scaffolded
- Created folder structure: _system, _inbox, atlas, sources, projects, areas, daily, templates, .skills
- Created 8 frontmatter templates (concept, entity, decision, pattern, guide, source, daily, project)
- Created taxonomy.md with controlled vocabulary
- Created vault-health.base dashboard
- Created 6 .skills/ definitions
- Created agent bootstrap files (CLAUDE.md, AGENTS.md, GEMINI.md)
- Agent: [your agent name]
```

### `_system/.manifest.json`

```json
{
  "version": 1,
  "description": "Tracks processed files for idempotent ingest. Updated by ingest pipeline.",
  "processed": {}
}
```

### `_system/vault-health.base`

```yaml
filters:
  and:
    - file.ext == "md"
    - not:
        - file.inFolder("templates")
        - file.inFolder("_system")
formulas:
  days_since_modified: (now() - file.mtime).days
  days_since_created: (now() - file.ctime).days
  is_stale: if((now() - file.mtime).days > 90, "STALE", "")
  is_orphan: if(file.backlinks.length == 0 && file.links.length == 0, "ORPHAN", "")
  health_flag: if(file.backlinks.length == 0 && file.links.length == 0, "ORPHAN", if((now() - file.mtime).days > 90, "STALE", if(status == "seed" && (now() - file.ctime).days > 30, "SEED", "OK")))
  link_count: file.links.length + file.backlinks.length
properties:
  formula.days_since_modified:
    displayName: Days Idle
  formula.health_flag:
    displayName: Health
  formula.link_count:
    displayName: Connections
views:
  - type: table
    name: Knowledge Inventory
    groupBy:
      property: type
      direction: ASC
    order:
      - file.name
      - type
      - status
      - domain
      - provenance
      - confidence
      - formula.link_count
      - formula.days_since_modified
    summaries:
      formula.link_count: Average
      formula.days_since_modified: Average
      type: Filled
  - type: table
    name: Needs Attention
    filters:
      or:
        - formula.health_flag != "OK"
    groupBy:
      property: formula.health_flag
      direction: ASC
    order:
      - file.name
      - formula.health_flag
      - type
      - status
      - provenance
      - confidence
      - formula.days_since_modified
    summaries:
      formula.health_flag: Filled
  - type: table
    name: LLM Provenance Audit
    filters:
      or:
        - provenance == "extracted"
        - provenance == "synthesized"
        - provenance == "inferred"
    groupBy:
      property: provenance
      direction: ASC
    order:
      - file.name
      - provenance
      - confidence
      - source
      - formula.days_since_created
    summaries:
      confidence: Unique
      provenance: Filled
  - type: table
    name: Recent Growth
    order:
      - file.name
      - type
      - domain
      - provenance
      - file.ctime
    limit: 30
    summaries:
      type: Unique
      domain: Unique
```

---

## Step 4: Templates (8 files)

All templates use [Templater](https://github.com/SilentVoid13/Templater) syntax (`{{title}}`, `{{date:YYYY-MM-DD}}`).

### `templates/concept.md`

```markdown
---
title: "{{title}}"
aliases: []
type: concept
status: seed
domain: []
tags: []
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: human
confidence: high
source: ""
related: []
summary: ""
---

```

### `templates/entity.md`

```markdown
---
title: "{{title}}"
aliases: []
type: entity
status: seed
domain: []
tags: []
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: human
confidence: high
source: ""
related: []
summary: ""
---

```

### `templates/decision.md`

```markdown
---
title: "{{title}}"
aliases: []
type: decision
status: seed
domain: []
tags: []
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: human
confidence: high
source: ""
related: []
summary: ""
---

## Context


## Decision


## Rationale


## Consequences

```

### `templates/pattern.md`

```markdown
---
title: "{{title}}"
aliases: []
type: pattern
status: seed
domain: []
tags: []
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: human
confidence: high
source: ""
related: []
summary: ""
---

## Problem


## Solution


## When to use


## Examples

```

### `templates/guide.md`

```markdown
---
title: "{{title}}"
aliases: []
type: guide
status: seed
domain: []
tags: []
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: human
confidence: high
source: ""
related: []
summary: ""
---

## Prerequisites


## Steps


## Troubleshooting

```

### `templates/source.md`

```markdown
---
title: "{{title}}"
aliases: []
type: source
status: seed
domain: []
tags: []
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: extracted
confidence: high
source: ""
related: []
summary: ""
---

## Key Takeaways


## Notes


## Quotes

```

### `templates/daily.md`

```markdown
---
title: "{{date:YYYY-MM-DD}}"
type: daily
status: growing
domain: []
tags: [daily]
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: human
summary: ""
---

## Log


## Tasks

- [ ] 

## Notes

```

### `templates/project.md`

```markdown
---
title: "{{title}}"
aliases: []
type: project
status: seed
domain: []
tags: []
created: "{{date:YYYY-MM-DD}}"
modified: "{{date:YYYY-MM-DD}}"
provenance: human
confidence: high
source: ""
related: []
summary: ""
---

## Goals


## Status


## Key Decisions


## Notes

```

---

## Step 5: Agent skills (6 files)

### `.skills/vault-ingest.md`

```markdown
---
name: vault-ingest
description: Process raw content from _inbox/ into structured atlas/ notes with frontmatter
triggers:
  - /vault-ingest
  - "ingest new content"
  - "process inbox"
---

## Context

This vault uses structured YAML frontmatter for all notes. See `_system/taxonomy.md` for allowed values. See `templates/` for note templates.

### Folder mapping
- Concepts, frameworks, theories -> `atlas/concepts/`
- People, orgs, tools, technologies -> `atlas/entities/`
- Reusable solutions, best practices -> `atlas/patterns/`
- How-tos, playbooks -> `atlas/guides/`
- Source summaries -> `sources/{articles,papers,books,conversations}/`

## Instructions

1. List files in `_inbox/` (clips, voice, screenshots, imports)
2. For each unprocessed file:
   a. Read the full content
   b. Extract entities, concepts, patterns, key claims
   c. Search `atlas/` for existing notes on the same topics (check titles + aliases)
   d. If existing note found with >70% topic overlap -> MERGE (append, don't reorganize)
   e. If no match -> CREATE new note using appropriate template from `templates/`
   f. Add `[[wikilinks]]` to related concepts mentioned in the text
   g. Update `related:` fields bidirectionally
3. Set frontmatter:
   - `provenance: extracted` for direct facts, `synthesized` for cross-source connections
   - `confidence:` based on source quality (reputable = high, blog = medium, forum = low)
   - `summary:` 1-2 sentences (this is what RAG reads first)
4. Append entry to `_system/log.md`
5. Git commit with message: `[llm:{your-model}] ingest: {summary of what was processed}`

## Rules
- Never overwrite content with `provenance: human`
- Never delete files from `_inbox/` — move to `_inbox/.processed/` or leave for human
- Use tags from `_system/taxonomy.md` — propose new tags in log before using
- Every claim must trace to a source
- Set `modified:` date on every touched note
```

### `.skills/vault-query.md`

```markdown
---
name: vault-query
description: Answer questions by searching the vault knowledge base with citations
triggers:
  - /vault-query
  - "search the vault"
  - "what do I know about"
---

## Context

This vault contains structured markdown notes with YAML frontmatter. The `summary:` field provides a quick preview without reading the full note. The `_system/index.md` catalogs all content by type.

## Instructions

1. Read `_system/index.md` to identify potentially relevant pages
2. Filter by `domain:` and `type:` if the query has a clear scope
3. Read `summary:` fields of candidate notes first (token-efficient)
4. Load full content only for the top 3 most relevant notes
5. Synthesize an answer with `[[wikilink]]` citations to source notes
6. If the answer reveals a novel insight worth preserving:
   a. Write it as a new note in `atlas/concepts/` or `atlas/patterns/`
   b. Set `provenance: synthesized`, `confidence:` based on source quality
   c. Cross-link to the notes that informed the answer
   d. Update `_system/index.md` and `_system/log.md`

## Rules
- Always cite sources with `[[wikilinks]]`
- Distinguish between what the vault says vs general knowledge
- Flag contradictions between notes if found
- Never fabricate vault content — if the vault doesn't cover a topic, say so
```

### `.skills/vault-lint.md`

```markdown
---
name: vault-lint
description: Health-check the vault for broken links, stale content, and quality issues
triggers:
  - /vault-lint
  - "check vault health"
  - "lint the vault"
---

## Context

The vault uses structured frontmatter. See `_system/taxonomy.md` for allowed values.

## Instructions

Scan all `.md` files (excluding `templates/` and `_system/`) and check:

### Structural issues (Critical)
- Broken `[[wikilinks]]` pointing to non-existent notes
- Missing required frontmatter fields: `title`, `type`, `status`, `provenance`, `summary`
- Invalid frontmatter values (not in taxonomy.md enums)

### Staleness issues (Warning)
- `status: seed` AND created > 30 days ago
- `status: evergreen` AND modified > 90 days ago
- `type: source` with no recent references from other notes

### Trust issues (Warning)
- `provenance: inferred` AND `confidence: low`
- `provenance: extracted` with empty `source:` field
- Empty `summary:` field (breaks tiered retrieval)

### Graph issues (Info)
- Orphan notes: zero incoming + outgoing links
- Notes with empty body (frontmatter only)

### Taxonomy drift (Info)
- Tags used in notes but not listed in `_system/taxonomy.md`
- Domain values not in taxonomy

## Output

Write report to `_system/lint-report-YYYY-MM.md` with frontmatter:

```yaml
type: source
status: evergreen
provenance: synthesized
confidence: high
summary: "Vault lint report — N issues found"
```

Group findings by severity: Critical -> Warning -> Info.
Append entry to `_system/log.md`.

## Rules
- Never modify notes — only read and report
- Never delete or archive — only flag for human review
- Always produce a report, even if clean (confirms health)
```

### `.skills/vault-crosslink.md`

```markdown
---
name: vault-crosslink
description: Discover unlinked mentions and create wikilink connections between notes
triggers:
  - /vault-crosslink
  - "find connections"
  - "cross-link notes"
---

## Context

Notes use `[[wikilinks]]` and `related:` frontmatter for explicit connections. Titles and `aliases:` in frontmatter define discoverable entity names.

## Instructions

1. Build an entity index: read all `atlas/` notes, extract `title` + `aliases`
2. For each note, scan body text for unlinked mentions of any entity name/alias
3. If mention found without `[[wikilink]]`:
   a. Wrap the mention in `[[wikilinks]]`
   b. Add to `related:` in both notes' frontmatter (bidirectional)
4. After cross-linking, compute graph analytics:
   - **Hub pages**: top 10 by connection count (inlinks + outlinks)
   - **Orphan pages**: zero connections — flag for enrichment or archival
   - **Bridge pages**: notes connecting otherwise separate clusters
   - **Cross-domain connections**: links between different `domain:` values
5. Write findings to `_system/insights.md`
6. Append to `_system/log.md`
7. Git commit: `[llm:{model}] crosslink: discovered N new connections`

## Rules
- Never create new notes — only modify existing ones
- Never change note body content — only add wikilinks
- Preserve existing formatting
- Case-insensitive matching for entity names
- Don't link common words that happen to match entity names (use context)
```

### `.skills/vault-distill.md`

```markdown
---
name: vault-distill
description: Extract lasting knowledge from LLM conversation transcripts into vault notes
triggers:
  - /vault-distill
  - "distill conversation"
  - "extract insights"
---

## Context

Conversation transcripts land in `_inbox/imports/`. Distilled insights go to `sources/conversations/` with cross-links to `atlas/` notes.

## Instructions

1. Read the conversation transcript
2. Identify valuable segments:
   - **Decisions**: Explicit choices with rationale
   - **Patterns**: Reusable approaches that worked
   - **Discoveries**: Non-obvious facts or insights
   - **Problems solved**: Root causes and fixes (if generalizable)
3. Filter noise — skip:
   - Debugging iterations (keep only root cause if novel)
   - Small talk, greetings, meta-discussion
   - Trivial Q&A with easily searchable answers
   - Code already committed to repos
4. Create source note in `sources/conversations/`:
   - `provenance: synthesized`
   - `confidence: high` (direct from conversation)
   - Structured sections: Decisions, Patterns, Insights
5. For novel patterns -> create/update `atlas/patterns/` note
6. For new entities -> create/update `atlas/entities/` note
7. Cross-link all distilled notes to relevant existing atlas/ content
8. Update `_system/log.md`

## Rules
- Be aggressive with filtering — only keep what's useful 6+ months from now
- Prefer enriching existing notes over creating near-duplicates
- Every extracted claim references the conversation as source
- Set `provenance: synthesized` on all distilled content
```

### `.skills/vault-status.md`

```markdown
---
name: vault-status
description: Report vault metrics, growth stats, and graph analytics summary
triggers:
  - /vault-status
  - "vault stats"
  - "how big is the vault"
---

## Context

The vault uses structured frontmatter on all notes. `_system/vault-health.base` provides a live Obsidian dashboard. This skill provides a CLI-friendly summary.

## Instructions

1. Count notes by:
   - `type:` (concept, entity, pattern, guide, source, daily, project, area)
   - `status:` (seed, growing, evergreen, archived)
   - `domain:` (engineering, polymath, professional, home-automation)
   - `provenance:` (human, extracted, synthesized, inferred)
2. Count total `[[wikilinks]]` and average links per note
3. Identify:
   - Most connected notes (top 5 by link count)
   - Most recent additions (last 5 by `created:` date)
   - Notes needing attention (orphans, stale seeds, low-trust)
4. Read last 5 entries from `_system/log.md` for recent activity
5. Present as a concise summary

## Output format

```
Vault: obsidian-nexus
Notes: N total (X concepts, Y entities, Z patterns, ...)
Status: X seed / Y growing / Z evergreen / W archived
Provenance: X human / Y extracted / Z synthesized / W inferred
Links: N total, avg M per note
Top hubs: [[A]] (N), [[B]] (N), [[C]] (N)
Recent: [last 3 operations from log.md]
Attention: X orphans, Y stale seeds, Z low-trust
```

## Rules
- Read-only — never modify any files
- Include the `_system/vault-health.base` path for detailed dashboard
```

---

## Step 6: Agent bootstrap files

### `CLAUDE.md`

```markdown
# Obsidian Nexus — Claude Agent Bootstrap

You are operating on a structured Obsidian vault that serves as a persistent, self-improving knowledge base. This vault is part of a 3-tier AI orchestration system.

## Vault Schema

```
_system/        -> Vault metadata: index.md, taxonomy.md, log.md, vault-health.base
_inbox/         -> Raw capture staging (clips, voice, screenshots, imports)
atlas/          -> Evergreen knowledge (concepts, entities, patterns, guides)
sources/        -> Processed source summaries (articles, papers, books, conversations)
projects/       -> Active project workspaces ({name}/decisions/, {name}/notes/)
areas/          -> Ongoing responsibility areas (engineering, home-automation)
daily/          -> Daily notes
templates/      -> Frontmatter templates per note type
.skills/        -> Canonical agent skill definitions
```

## Frontmatter Spec

Every `.md` note MUST have YAML frontmatter. Required fields:

| Field | Values |
|-------|--------|
| `title` | Human-readable title |
| `type` | concept, entity, decision, pattern, guide, source, daily, project, area |
| `status` | seed, growing, evergreen, archived |
| `domain` | List from: engineering, polymath, professional, home-automation |
| `provenance` | human, extracted, synthesized, inferred |
| `confidence` | high, medium, low |
| `created` | YYYY-MM-DD |
| `modified` | YYYY-MM-DD |
| `summary` | 1-2 sentences (used for tiered retrieval — LLM reads this FIRST) |

Optional: `aliases`, `tags`, `source`, `related` (wikilinks).

See `_system/taxonomy.md` for full controlled vocabulary.

## Rules

1. **Never delete notes** — archive by setting `status: archived`
2. **Never overwrite `provenance: human` content** — only append/enrich
3. **Always set `provenance:`** on content you write (extracted, synthesized, or inferred)
4. **Always update `modified:` date** when touching a note
5. **Always update `_system/log.md`** after any vault operation
6. **Use tags from taxonomy** — propose new tags in log before using
7. **Prefer merging** into existing notes over creating near-duplicates
8. **Use `[[wikilinks]]`** to connect related concepts
9. **Git commit** after changes with format: `[llm:claude] action: summary`

## Available Skills

See `.skills/` directory for detailed instructions:
- `/vault-ingest` — Process _inbox/ content into atlas/ notes
- `/vault-query` — Search and answer questions from vault
- `/vault-lint` — Health-check for broken links, stale content
- `/vault-crosslink` — Discover and create wikilink connections
- `/vault-distill` — Extract knowledge from conversation transcripts
- `/vault-status` — Report vault metrics and graph analytics

## Retrieval Strategy

1. Read `_system/index.md` for catalog overview
2. Filter candidates by `domain:` and `type:`
3. Read `summary:` fields first (token-efficient)
4. Load full notes only for top-3 relevant matches
5. Cite with `[[wikilinks]]`
```

### `AGENTS.md`

```markdown
# Obsidian Nexus — Generic Agent Bootstrap

This file is for any AI agent (OpenAI Codex, LLaMA, Mistral, or other) operating on this vault.

## What is this vault?

A structured Obsidian knowledge base with YAML frontmatter on every note. Part of a 3-tier AI orchestration system. You are likely a Tier 1 or Tier 2 agent handling local tasks.

## Folder structure

- `_system/` — Vault metadata (index.md, taxonomy.md, log.md). Read taxonomy.md first.
- `_inbox/` — Raw staging. Process with vault-ingest skill.
- `atlas/` — Evergreen knowledge: `concepts/`, `entities/`, `patterns/`, `guides/`
- `sources/` — Source summaries: `articles/`, `papers/`, `books/`, `conversations/`
- `projects/` — Project workspaces with decisions/ and notes/
- `areas/` — Ongoing areas (engineering, home-automation)
- `daily/` — Daily notes
- `templates/` — Note templates with frontmatter
- `.skills/` — Read these for detailed operation instructions

## Required frontmatter

```yaml
---
title: "Note Title"
type: concept | entity | decision | pattern | guide | source | daily | project | area
status: seed | growing | evergreen | archived
domain: [engineering, polymath, professional, home-automation]
provenance: human | extracted | synthesized | inferred
confidence: high | medium | low
created: YYYY-MM-DD
modified: YYYY-MM-DD
summary: "1-2 sentence description for retrieval"
---
```

## Rules

1. Read `_system/taxonomy.md` before writing any content
2. Never delete notes — set `status: archived`
3. Never overwrite human-written content (`provenance: human`)
4. Always tag your output with correct `provenance:` value
5. Always update `modified:` date
6. Always append to `_system/log.md` after operations
7. Prefer merging into existing notes over creating duplicates
8. Use `[[wikilinks]]` for connections
9. Git commit with: `[llm:{your-model}] action: summary`

## Skills

Read `.skills/*.md` for available operations:
- vault-ingest, vault-query, vault-lint, vault-crosslink, vault-distill, vault-status
```

### `GEMINI.md`

```markdown
# Obsidian Nexus — Gemini Agent Bootstrap

This vault is a structured Obsidian knowledge base. See `AGENTS.md` for full schema, frontmatter spec, and rules. This file provides Gemini-specific guidance.

## Quick reference

- **Taxonomy**: `_system/taxonomy.md` — read before writing
- **Templates**: `templates/*.md` — use for new notes
- **Skills**: `.skills/*.md` — operational instructions
- **Index**: `_system/index.md` — catalog of all content
- **Log**: `_system/log.md` — append after every operation

## Key rules

1. Every note needs YAML frontmatter (see AGENTS.md for schema)
2. Set `provenance:` to `extracted`, `synthesized`, or `inferred` on your output
3. Never overwrite `provenance: human` content
4. Use `[[wikilinks]]` for connections
5. Git commit format: `[llm:gemini] action: summary`
6. Always append to `_system/log.md`
```

---

## Step 7: Environment and git config

### `.env`

```bash
# Obsidian Nexus — Environment Configuration
# Copy to .env.local for machine-specific overrides

VAULT_PATH=%UserName%/obsidian-nexus
VAULT_RAW_DIR=_inbox

# Desktop server
DESKTOP_HOST=192.168.1.XXX

# Ollama
OLLAMA_DESKTOP_URL="http://${DESKTOP_HOST}:11434"
OLLAMA_LOCAL_URL=http://localhost:11434
EMBEDDING_MODEL=mxbai-embed-large
EMBEDDING_DIM=1024

# Qdrant (desktop)
QDRANT_URL="http://${DESKTOP_HOST}:6333"

# ChromaDB (ultrabook local)
CHROMADB_URL="http://localhost:8000"

# n8n (desktop)
N8N_URL="http://${DESKTOP_HOST}:5678"
```

### `.gitignore`

```
# Obsidian
.obsidian/workspace.json
.obsidian/workspace-mobile.json
.obsidian/plugins/*/data.json
.trash/

# Environment
.env.local

# OS
.DS_Store
Thumbs.db
desktop.ini

# IDE
.idea/
.vscode/

# Temp
*.tmp
*.bak
```

### `.githooks/post-push`

```bash
#!/bin/bash
# Trigger n8n vault processing on push (LAN — instant)
# Install: git config core.hooksPath .githooks

DESKTOP_HOST="${DESKTOP_HOST:-192.168.1.XXX}"
N8N_WEBHOOK="http://$DESKTOP_HOST:5678/webhook/vault-push"

# Fire and forget — don't block the push if desktop is offline
curl -s -X POST "$N8N_WEBHOOK" \
  -H "Content-Type: application/json" \
  -d "{\"event\": \"push\", \"timestamp\": \"$(date -Iseconds)\", \"source\": \"ultrabook\"}" \
  --connect-timeout 3 \
  --max-time 5 \
  > /dev/null 2>&1 &

exit 0
```

After creating this file:

```bash
chmod +x .githooks/post-push
git config core.hooksPath .githooks
```

---

## Step 8: Obsidian configuration

### `.obsidian/core-plugins.json`

```json
{
  "file-explorer": true,
  "global-search": true,
  "switcher": true,
  "graph": true,
  "backlink": true,
  "canvas": true,
  "outgoing-link": true,
  "tag-pane": true,
  "footnotes": false,
  "properties": true,
  "page-preview": true,
  "daily-notes": true,
  "templates": true,
  "note-composer": true,
  "command-palette": true,
  "slash-command": false,
  "editor-status": true,
  "bookmarks": true,
  "markdown-importer": false,
  "zk-prefixer": false,
  "random-note": false,
  "outline": true,
  "word-count": true,
  "slides": false,
  "audio-recorder": false,
  "workspaces": false,
  "file-recovery": true,
  "publish": false,
  "sync": true,
  "bases": true,
  "webviewer": false
}
```

### `.obsidian/graph.json`

```json
{
  "collapse-filter": true,
  "search": "",
  "showTags": false,
  "showAttachments": false,
  "hideUnresolved": false,
  "showOrphans": true,
  "collapse-color-groups": true,
  "colorGroups": [],
  "collapse-display": true,
  "showArrow": false,
  "textFadeMultiplier": 0,
  "nodeSizeMultiplier": 1,
  "lineSizeMultiplier": 1,
  "collapse-forces": true,
  "centerStrength": 0.518713248970312,
  "repelStrength": 10,
  "linkStrength": 1,
  "linkDistance": 250,
  "scale": 1.252572861566976,
  "close": true
}
```

### `.obsidian/app.json`

```json
{}
```

### `.obsidian/appearance.json`

```json
{}
```

---

## Step 9: Initialize git

```bash
cd "$VAULT"
git init
git add -A
git commit -m "vault: initial scaffold — structure, templates, skills, dashboard, agent bootstraps"
```

To connect to a remote:

```bash
git remote add origin <your-repo-url>
git push -u origin main
```

---

## Step 10: Post-setup verification

Open the vault in Obsidian and confirm:

- [ ] All 16+ folders visible in file explorer
- [ ] `_system/vault-health.base` opens and renders 4 views (Knowledge Inventory, Needs Attention, LLM Provenance Audit, Recent Growth)
- [ ] Templates work: create a new note, apply a template, confirm frontmatter populates
- [ ] Graph view shows the system notes with connections
- [ ] `.env` file has correct paths for your environment

---

## Step 11: Recommended Obsidian plugins

Install via Settings > Community Plugins:

| Plugin | Purpose |
|--------|---------|
| **Templater** | Template engine (set template folder: `templates/`) |
| **Dataview** | Query vault as database via frontmatter |
| **Graph Analysis** | Betweenness centrality, clustering metrics |
| **Obsidian Git** | Auto-commit interval (10-30 min) |
| **Web Clipper** | Browser extension, saves to `_inbox/clips/` |
| **Tag Wrangler** | Rename/merge tags vault-wide |

---

## Appendix: Complete file tree

```
obsidian-nexus/
├── .env
├── .gitignore
├── .githooks/
│   └── post-push
├── .obsidian/
│   ├── app.json
│   ├── appearance.json
│   ├── core-plugins.json
│   └── graph.json
├── .skills/
│   ├── vault-crosslink.md
│   ├── vault-distill.md
│   ├── vault-ingest.md
│   ├── vault-lint.md
│   ├── vault-query.md
│   └── vault-status.md
├── AGENTS.md
├── CLAUDE.md
├── GEMINI.md
├── _inbox/
│   ├── clips/.gitkeep
│   ├── imports/.gitkeep
│   ├── screenshots/.gitkeep
│   └── voice/.gitkeep
├── _system/
│   ├── .manifest.json
│   ├── index.md
│   ├── log.md
│   ├── taxonomy.md
│   └── vault-health.base
├── areas/
│   ├── engineering/.gitkeep
│   └── home-automation/.gitkeep
├── atlas/
│   ├── concepts/.gitkeep
│   ├── entities/.gitkeep
│   ├── guides/.gitkeep
│   └── patterns/.gitkeep
├── daily/.gitkeep
├── projects/.gitkeep
├── sources/
│   ├── articles/.gitkeep
│   ├── books/.gitkeep
│   ├── conversations/.gitkeep
│   └── papers/.gitkeep
└── templates/
    ├── concept.md
    ├── daily.md
    ├── decision.md
    ├── entity.md
    ├── guide.md
    ├── pattern.md
    ├── project.md
    └── source.md
```

---

## Notes

- **Environment-specific values**: Replace `192.168.1.XXX` in `.env` and `.githooks/post-push` with your desktop server's actual LAN IP.
- **VAULT_PATH**: Adjust `%UserName%/obsidian-nexus` to match your OS path format (`$HOME/obsidian-nexus` on Linux/macOS).
- **Agent bootstraps**: Add more files (e.g., `LLAMA.md`, `COPILOT.md`) following the same pattern as `AGENTS.md` for any new AI tools.
- **The `.idea/` directory** from the original vault is IDE-specific (JetBrains) and excluded from this plan — it regenerates automatically when you open the project in IntelliJ/WebStorm.
