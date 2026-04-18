# ULTRAPLAN — Personal AI Orchestration + Memory Palace

## Context

Rafael is building a 3-tier AI orchestration stack across two machines (ultrabook + desktop server) with Claude as the reasoning tier. The core problem: how to structure a persistent, self-improving knowledge base in Obsidian that LLMs can both read from and write to, with full auditability via git. This plan refines the vault structure, frontmatter schema, vector store architecture, and self-improving feedback loops — synthesized from Karpathy's LLM Wiki pattern, MemPalace's hierarchical memory, obsidian-wiki's provenance tracking, and second-brain's curation model.

Future context: a separate Jarvis-style home automation project (Steam Deck + LLaMA) will also generate raw content and conversations that feed into this same knowledge base.

---

## 1. Intelligence Tiers (Refined)

```
User query → gemma4:e2b (router) → classifies complexity + domain
                                      ↓
              ┌───────────────────────┼──────────────────────┐
              ↓                       ↓                      ↓
        Simple/Fast             Medium/Local            Hard/Reasoning
      gemma4:e4b              gemma4:26b               Claude Pro API
      (ultrabook)             (desktop GPU)            (cloud)
      ~80% of tasks           local execution          planning, judgment,
      drafts, lookup,         code gen, analysis,      synthesis, final
      classification          summarization            output, complex RAG
```

**Router classification signals** (for gemma4:e2b to evaluate):
- Token estimate of expected output
- Number of knowledge domains involved
- Whether retrieval context is needed (RAG)
- Whether reasoning chain > 2 steps
- Whether output is user-facing (quality matters)

---

## 2. Vault Structure

Designed for: LLM-writable, human-navigable, graph-auditable, multi-domain.

```
vault/
│
├── _system/                        # Vault metadata (LLM-maintained)
│   ├── index.md                    # Master catalog by domain/type
│   ├── taxonomy.md                 # Controlled tag vocabulary
│   ├── log.md                      # Append-only operation log
│   ├── vault-health.base           # Live health dashboard (Obsidian Base)
│   └── .manifest.json              # Delta tracking for re-indexing
│
├── _inbox/                         # Raw capture staging
│   ├── clips/                      # Web clipper, bookmarks
│   ├── voice/                      # Transcripts
│   ├── screenshots/                # Images, whiteboard captures
│   └── imports/                    # Conversation exports, bulk data
│
├── atlas/                          # Evergreen knowledge ("the wiki")
│   ├── concepts/                   # Mental models, frameworks, theories
│   ├── entities/                   # People, orgs, tools, technologies
│   ├── patterns/                   # Reusable solutions, best practices
│   └── guides/                     # How-tos, playbooks, runbooks
│
├── sources/                        # Processed source summaries
│   ├── articles/                   # Web articles, blog posts
│   ├── papers/                     # Academic papers
│   ├── books/                      # Book notes
│   └── conversations/              # Distilled LLM conversation insights
│
├── projects/                       # Active project workspaces
│   └── {project-name}/
│       ├── _overview.md            # Goals, status, stakeholders
│       ├── decisions/              # ADRs (Architecture Decision Records)
│       └── notes/                  # Project-specific knowledge
│
├── areas/                          # Ongoing responsibility areas (PARA)
│   ├── engineering/
│   ├── home-automation/            # Future Jarvis project context
│   └── {area-name}/
│
├── daily/                          # Daily notes (date-named)
│
├── templates/                      # Frontmatter templates per type
│   ├── concept.md
│   ├── entity.md
│   ├── decision.md
│   ├── source.md
│   └── daily.md
│
├── .skills/                        # Canonical AI agent skill definitions
│   ├── vault-ingest.md             # Ingest _inbox → atlas pipeline
│   ├── vault-query.md              # RAG query against vault
│   ├── vault-lint.md               # Health check + link scan
│   ├── vault-crosslink.md          # Discover + propose wikilinks
│   ├── vault-distill.md            # Conversation → knowledge extraction
│   └── vault-status.md             # Report vault metrics
│
├── CLAUDE.md                       # Claude agent bootstrap
├── AGENTS.md                       # Generic agent bootstrap (Codex, LLaMA)
├── GEMINI.md                       # Gemini agent bootstrap
└── .env                            # Shared config (paths, URLs)
```

### Why this structure (vs. alternatives considered)

| Decision | Chosen | Why |
|----------|--------|-----|
| `atlas/` vs `knowledge/` | `atlas/` | Distinct name avoids collision with generic terms; evokes "map of knowledge" |
| `_inbox/` vs `raw/` | `_inbox/` | Clearer intent — staging, not permanent. Underscore prefix sorts first |
| `sources/` separate from `atlas/` | Yes | Sources are references TO knowledge, not knowledge itself. Keeps atlas clean |
| No `llm-output/` folder | Correct | Auto-merge with provenance tags means LLM writes directly to proper location |
| `areas/` (PARA) | Added | Captures ongoing responsibilities that aren't projects (career, health, home-automation) |
| `_system/` | Added | Karpathy pattern: index.md + log.md + taxonomy.md for LLM self-navigation |

---

## 3. Frontmatter Schema

Every note gets structured YAML frontmatter. This is the primary interface between LLMs and the vault — enables filtering before embedding search, saving tokens.

```yaml
---
title: "Note Title"
aliases: ["alt name", "acronym"]           # For wikilink resolution
type: concept | entity | decision | pattern | guide | source | daily | project | area
status: seed | growing | evergreen | archived
domain:                                     # Multi-select, from taxonomy.md
  - engineering
  - polymath
  - professional
tags: [specific-tag, another-tag]           # Freeform but prefer taxonomy.md terms
created: 2026-04-13
modified: 2026-04-13
provenance: human | extracted | synthesized | inferred
confidence: high | medium | low             # How certain is this information?
source: "URL or reference"                  # Where it came from
related:                                    # Explicit wikilinks (LLM + human maintained)
  - "[[Related Concept]]"
  - "[[Another Note]]"
summary: "1-2 sentence description"         # LLM reads this BEFORE loading full note
---
```

### Frontmatter field rationale

| Field | Purpose |
|-------|---------|
| `type` | Enables folder-less filtering. LLM asks "give me all concepts in engineering domain" |
| `status` | Knowledge lifecycle: seed (stub) → growing (being enriched) → evergreen (stable) → archived |
| `provenance` | **Critical for self-improving loop.** `human` = you wrote it. `extracted` = LLM pulled from source. `synthesized` = LLM combined multiple sources. `inferred` = LLM's own reasoning (lowest trust) |
| `confidence` | Complements provenance. An `extracted` fact can still be `low` confidence if source is dubious |
| `summary` | **Token saver.** LLM reads summaries first via frontmatter filter, only loads full notes when relevant. Inspired by obsidian-wiki's tiered retrieval |
| `domain` | Multi-domain routing. Query about "rust async patterns" → filters `domain: engineering` before vector search. Home automation context stays separate |
| `related` | Explicit graph edges. LLM cross-linker discovers implicit ones and proposes additions |

---

## 4. Vector Store Architecture (Dual-Layer)

```
┌─────────────────────────────────────────────────────────────┐
│                      ULTRABOOK (local)                      │
│                                                             │
│  ChromaDB (Python-native)                                   │
│  ├── Collection: "recent" — last 30 days of notes           │
│  ├── Collection: "conversations" — LLM interaction memory   │
│  └── Collection: "workspace" — current project context      │
│                                                             │
│  Purpose: Fast personal recall, conversation memory,        │
│           MemPalace-style L0/L1 always-loaded context        │
│  Embeddings: mxbai-embed-large via local Ollama             │
└──────────────────────────┬──────────────────────────────────┘
                           │ LAN (REST API)
┌──────────────────────────┴──────────────────────────────────┐
│                      DESKTOP (server)                       │
│                                                             │
│  Qdrant (Docker, REST API on :6333)                         │
│  ├── Collection: "atlas" — full evergreen knowledge         │
│  ├── Collection: "sources" — all processed sources          │
│  ├── Collection: "projects" — all project context           │
│  └── Collection: "areas" — ongoing areas                    │
│                                                             │
│  Purpose: Full corpus search, filtered retrieval,           │
│           powers RAG pipeline for all tiers                  │
│  Embeddings: mxbai-embed-large via Ollama (desktop GPU)     │
│  Filtering: by domain, type, status, confidence, date       │
└─────────────────────────────────────────────────────────────┘
```

### Retrieval pipeline (RAG)

```
Query → gemma4:e2b classifies domain + type
      → Frontmatter filter (domain=X, type=Y, status≠archived)
      → Qdrant vector search (top-k with score threshold)
      → Read summaries from frontmatter
      → Load full notes only for top-3 relevant
      → Distilled context → Tier-appropriate LLM
```

This mirrors MemPalace's finding: **filtered retrieval hits 94.8% recall vs 60.9% unfiltered**. Frontmatter is the filter.

---

## 5. Self-Improving Feedback Loop

This is the core innovation — the vault gets smarter with every interaction.

### 5a. Ingest cycle

```
Raw content → _inbox/
     ↓
gemma4:26b (desktop) processes:
  1. Extract entities, concepts, patterns
  2. Check atlas/ for existing notes on same topics
  3. MERGE into existing notes (update, enrich) or CREATE new ones
  4. Set provenance: extracted | synthesized
  5. Set confidence: based on source quality
  6. Update related: fields with discovered connections
  7. Append to _system/log.md
     ↓
Git commit (auto or manual)
     ↓
Webhook triggers delta re-index:
  - Diff changed files
  - Re-embed only changed notes
  - Update Qdrant collections
  - Update ChromaDB recent/workspace
```

### 5b. Cross-linking cycle (weekly or on-demand)

```
Scan all notes → find unlinked mentions
  (entity name appears in text but no [[wikilink]])
     ↓
Propose [[wikilinks]] + update related: fields
     ↓
Graph analytics:
  - Hub pages (high connectivity) — core knowledge
  - Orphan pages (zero connections) — need enrichment or archival
  - Bridge pages (removal partitions graph) — critical connectors
  - Cluster gaps — domains that should connect but don't
     ↓
Write _system/insights.md with findings
```

### 5c. Decay + quality cycle (monthly)

```
Scan notes where:
  - status: seed AND created > 30 days ago → flag for enrichment or archive
  - provenance: inferred AND confidence: low → flag for human review
  - modified > 90 days ago AND status: evergreen → verify still accurate
  - Contradictions between notes (same entity, different claims)
     ↓
Write lint report → human reviews → promotes/archives/corrects
```

### 5d. Conversation distillation

```
Every Claude/Gemma conversation that produces useful output:
  1. Extract: decisions made, patterns discovered, problems solved
  2. Write to sources/conversations/ with provenance: synthesized
  3. Cross-link to relevant atlas/ notes
  4. If novel pattern → create new atlas/patterns/ note
```

This means the Jarvis project conversations also feed back — the system learns from every interaction across all projects.

---

## 6. Orchestration (n8n)

Self-hosted on desktop. Key flows:

### Flow 1: Router
```
Webhook → gemma4:e2b classify → route to tier
  → Tier 1 (gemma4:e4b on ultrabook via LAN)
  → Tier 2 (gemma4:26b on desktop)
  → Tier 3 (Claude API)
  → Return response + log interaction
```

### Flow 2: Vault Ingest
```
Git webhook (push to vault repo)
  → Diff changed files in _inbox/
  → For each new file: extract → resolve → write to atlas/
  → Re-embed changed notes → update Qdrant + ChromaDB
  → Update _system/log.md
```

### Flow 3: RAG Query
```
Query + domain hint
  → Frontmatter pre-filter (Qdrant metadata filter)
  → Vector search (top-k)
  → Read summaries → select top-3 full notes
  → Assemble context → route to appropriate tier
  → Return answer + optionally write to sources/conversations/
```

### Flow 4: Scheduled Maintenance
```
Cron (weekly): Cross-linker + graph analytics
Cron (monthly): Decay scan + lint report
Cron (daily): Sync ChromaDB "recent" collection
```

---

## 7. Infrastructure Summary

All Docker services on the desktop are bound to `127.0.0.1` only — not exposed on LAN. The ultrabook connects exclusively via `autossh` SSH tunnels (ed25519 key auth, password auth disabled).

| Service | Runs on | Desktop bind | Ultrabook access (tunnel) | Purpose |
|---------|---------|-------------|--------------------------|---------|
| Ollama | Desktop | `127.0.0.1:11434` | `localhost:21434` | LLM inference (gemma4:26b, mxbai-embed-large) |
| Ollama | Ultrabook | `localhost:11434` | — (local, no tunnel) | LLM inference (gemma4:e2b, gemma4:e4b) |
| Qdrant | Desktop | `127.0.0.1:6333/6334` | `localhost:26333/26334` | Full-corpus vector store |
| ChromaDB | Ultrabook | `localhost:8000` | — (local, no tunnel) | Local fast-recall vector store |
| n8n | Desktop | `127.0.0.1:5678` | `localhost:25678` | Orchestration workflows |
| GitHub | Cloud | — | — | Vault git sync + webhooks |

**Network**: Desktop services inaccessible from LAN. Ultrabook reaches them only through `autossh` tunnel authenticated by ed25519 private key. No active tunnel = no access.

---

## 8. Git Audit Trail

```
vault repo:
  - Every LLM write = git commit with structured message
  - Commit message format: "[llm:{model}] {action}: {summary}"
    Example: "[llm:gemma4-27b] ingest: extracted 3 concepts from article on async Rust"
    Example: "[llm:claude] synthesize: cross-linked 5 notes on memory architectures"
  - Human edits committed normally
  - Full diff history = complete audit of what any LLM changed
  - _system/log.md = human-readable summary of all operations
```

---

## 9. MemPalace Mapping

How MemPalace's metaphor maps to this Obsidian structure:

| MemPalace | Obsidian Vault | Purpose |
|-----------|---------------|---------|
| Wings | `domain:` frontmatter field | Major knowledge areas (engineering, polymath, professional) |
| Rooms | `projects/` + `areas/` folders | Specific contexts within a domain |
| Halls | `type:` frontmatter field | Memory categories (concepts, entities, patterns, decisions) |
| Closets | `summary:` in frontmatter | Quick-access pointers without full load |
| Drawers | Full note content | Verbatim detail |
| Tunnels | `related:` + `[[wikilinks]]` | Cross-domain connections |

ChromaDB on ultrabook acts as the "palace entrance" — L0/L1 always-loaded context. Qdrant on desktop is the "deep archive."

---

## 10. Multi-Agent Skills Layer (Open Format)

The vault must be readable/writable by **any** AI model — Claude, Gemma, LLaMA, GPT, Copilot, future models. Following the Agent Skills open standard (from obsidian-wiki), each agent discovers instructions through its native config path, all pointing to the same canonical skill definitions.

### Vault-level agent config

```
vault/
├── .skills/                            # Canonical skill definitions (source of truth)
│   ├── vault-ingest.md                 # Ingest raw → atlas pipeline
│   ├── vault-query.md                  # RAG query against vault
│   ├── vault-lint.md                   # Health check + broken link scan
│   ├── vault-crosslink.md              # Discover + propose wikilinks
│   ├── vault-distill.md                # Conversation → knowledge extraction
│   └── vault-status.md                 # Report vault metrics + graph analytics
│
├── .claude/                            # Claude Code / Claude Desktop
│   └── skills/ → ../.skills/           # Symlink to canonical
├── CLAUDE.md                           # Claude bootstrap: vault schema, frontmatter spec, rules
│
├── .cursor/                            # Cursor IDE
│   └── rules/
│       └── vault-agent.mdc             # Cursor rules pointing to .skills/
│
├── .github/
│   └── copilot-instructions.md         # GitHub Copilot instructions
│
├── AGENTS.md                           # OpenAI Codex / generic agent bootstrap
├── GEMINI.md                           # Google Gemini bootstrap
│
├── .windsurf/                          # Windsurf IDE
│   └── rules/
│       └── vault-agent.md
│
└── .env                                # Shared config
    # VAULT_PATH, QDRANT_URL, CHROMADB_URL, OLLAMA_URL
```

### Skill definition format (each .skills/*.md file)

```markdown
---
name: vault-ingest
description: Process raw content from _inbox/ into structured atlas/ notes
triggers:
  - /vault-ingest
  - "ingest new content"
  - "process inbox"
---

## Context
[Vault schema, frontmatter spec, folder structure]

## Instructions
[Step-by-step for any LLM to follow]

## Rules
- Always set provenance: extracted | synthesized
- Always set confidence: high | medium | low
- Always update related: with discovered connections
- Always append to _system/log.md
- Never overwrite human-authored content (provenance: human)
- Merge into existing notes when topic overlap > 70%
```

### Bootstrap file pattern (CLAUDE.md / AGENTS.md / GEMINI.md)

Each bootstrap file contains the same core information adapted to the agent's format:
1. **Vault schema** — folder structure + purpose of each folder
2. **Frontmatter spec** — all fields, allowed values, required vs optional
3. **Rules** — provenance tagging, merge-vs-create logic, wikilink conventions
4. **Skills pointer** — "see .skills/ for available operations"
5. **Forbidden actions** — never delete notes, never overwrite provenance:human

This means any new AI tool (local LLaMA on Steam Deck, future models) just needs a single bootstrap file mapping to `.skills/`.

### LLaMA / Jarvis interop

The Steam Deck home automation agent writes to the same vault:
- Raw captures → `_inbox/imports/jarvis/`
- Processed insights → `areas/home-automation/`
- Uses same frontmatter schema, same provenance tags
- Bootstrap: `LLAMA.md` (or use `AGENTS.md` generic format)

---

## 11. Vault Health Dashboard (Obsidian Base)

An Obsidian `.base` file that provides real-time vault health metrics. Place at `_system/vault-health.base`.

```yaml
# _system/vault-health.base
# Vault Health Dashboard — monitors knowledge base quality and growth

filters:
  and:
    - 'file.ext == "md"'
    - not:
        - file.inFolder("templates")
        - file.inFolder("_system")

formulas:
  days_since_modified: '(now() - file.mtime).days'
  days_since_created: '(now() - file.ctime).days'
  is_stale: 'if((now() - file.mtime).days > 90, "STALE", "")'
  is_orphan: 'if(file.backlinks.length == 0 && file.links.length == 0, "ORPHAN", "")'
  is_seed_old: 'if(status == "seed" && (now() - file.ctime).days > 30, "NEEDS WORK", "")'
  is_low_trust: 'if(provenance == "inferred" && confidence == "low", "REVIEW", "")'
  health_flag: 'if(file.backlinks.length == 0 && file.links.length == 0, "ORPHAN", if((now() - file.mtime).days > 90, "STALE", if(status == "seed" && (now() - file.ctime).days > 30, "SEED", "OK")))'
  link_count: 'file.links.length + file.backlinks.length'

properties:
  formula.days_since_modified:
    displayName: "Days Idle"
  formula.health_flag:
    displayName: "Health"
  formula.link_count:
    displayName: "Connections"
  formula.is_stale:
    displayName: "Stale?"

views:
  # View 1: Full inventory by type and status
  - type: table
    name: "Knowledge Inventory"
    order:
      - file.name
      - type
      - status
      - domain
      - provenance
      - confidence
      - formula.link_count
      - formula.days_since_modified
    groupBy:
      property: type
      direction: ASC
    summaries:
      formula.link_count: Average
      formula.days_since_modified: Average
      type: Filled

  # View 2: Notes that need attention
  - type: table
    name: "Needs Attention"
    filters:
      or:
        - 'formula.health_flag != "OK"'
    order:
      - file.name
      - formula.health_flag
      - type
      - status
      - provenance
      - confidence
      - formula.days_since_modified
    groupBy:
      property: formula.health_flag
      direction: ASC
    summaries:
      formula.health_flag: Filled

  # View 3: LLM-generated content audit
  - type: table
    name: "LLM Provenance Audit"
    filters:
      or:
        - 'provenance == "extracted"'
        - 'provenance == "synthesized"'
        - 'provenance == "inferred"'
    order:
      - file.name
      - provenance
      - confidence
      - source
      - formula.days_since_created
    groupBy:
      property: provenance
      direction: ASC
    summaries:
      confidence: Unique
      provenance: Filled

  # View 4: Growth tracker (recent additions)
  - type: table
    name: "Recent Growth"
    limit: 30
    order:
      - file.name
      - type
      - domain
      - provenance
      - file.ctime
    summaries:
      type: Unique
      domain: Unique
```

This dashboard gives you at-a-glance visibility into:
- **Knowledge Inventory**: note counts grouped by type, average connections, average staleness
- **Needs Attention**: orphans, stale notes, old seeds, low-trust inferences — the lint report as a live view
- **LLM Provenance Audit**: everything machines wrote, grouped by trust level
- **Recent Growth**: what's been added lately, by whom (human vs LLM)

---

## 12. Implementation Phases

### Phase A: Foundation (do first)
1. Initialize Obsidian vault with folder structure above
2. Create all templates/ with frontmatter schemas
3. Create _system/taxonomy.md with initial controlled vocabulary
4. Set up git repo + remote (Gitea on desktop or GitHub)
5. Write CLAUDE.md / orchestration config for the vault

### Phase B: Desktop Server
1. Docker compose: Ollama + Qdrant + n8n + Gitea
2. Pull models: gemma4:e2b, gemma4:e4b, gemma4:26b, mxbai-embed-large
3. Configure n8n router flow (Flow 1)
4. Test LAN access from ultrabook

### Phase C: Knowledge Pipeline
1. Build n8n ingest flow (Flow 2)
2. Build n8n RAG query flow (Flow 3)
3. Set up git webhook → n8n for delta re-indexing
4. Initial bulk ingest of any existing notes/knowledge

### Phase D: Self-Improving Loops
1. Build cross-linker automation (Flow 4 weekly)
2. Build decay/lint scanner (Flow 4 monthly)
3. Conversation distillation pipeline
4. ChromaDB sync on ultrabook

### Phase E: Refinement
1. Tune router classification prompts
2. Tune RAG retrieval (top-k, score thresholds, context assembly)
3. Add Obsidian community plugins (Dataview, Graph Analysis, Templater)
4. Monitor and iterate on provenance/confidence accuracy

---

## 13. Key Principles (Carried Forward)

1. **Claude tokens only for planning, judgment, final output** — Gemma4 handles ~80% locally
2. **Git history = full audit trail** — every LLM interaction is traceable
3. **Frontmatter is the API** — LLMs filter before they embed, saving tokens and improving recall
4. **Auto-merge with provenance** — low friction, full traceability via `provenance:` + `confidence:` tags
5. **The vault compounds** — every interaction makes it smarter, not just bigger
6. **Human reviews, LLM maintains** — you curate, the LLM does bookkeeping (Karpathy's core insight)

---

## Status Update (2026-04-18)

**Phase A: Complete** ✓
- Vault initialized with full folder structure on ultrabook
- All 8 templates created with Templater syntax `<% tp.date.now("YYYY-MM-DD HH:mm") %>`
- obsidian-nexus repo on GitHub with machine-specific configs (`.env.ultrabook` / `.env.desktop`)
- Obsidian Git: auto-commit 15 min, auto-push enabled

**Phase B: Complete** ✓
- Desktop (CachyOS, Ryzen 5 5600x + RTX 3050) fully operational
- Docker stack: Ollama, Qdrant, n8n running headless
- SSH tunnel: ed25519 auth, password disabled, persistent `autossh` on Windows Startup
- Services bound to `127.0.0.1` only, ultrabook access via SSH tunnels to ports: 21434 (Ollama), 26333/26334 (Qdrant), 25678 (n8n)

**Phase E (partial): In Progress** 🔄
- Obsidian plugins installed: Templater ✓, Dataview ✓, Obsidian Git ✓
- vault-health enhanced with 5 Dataview queries (Hub Nodes, Domain Coverage, Writing Velocity, Confidence Audit, High-Value Sources)
- Graph Analysis not found in registry (skipped)
- Pending: Web Clipper, Tag Wrangler

## Verification

After Phase A:
- [X] Vault opens in Obsidian with all folders visible
- [X] Templates create notes with correct frontmatter (Templater syntax verified)
- [X] Git push/pull works between ultrabook and remote (auto-commit/push tested)

After Phase B:
- [X] `curl http://localhost:21434/api/tags` returns Ollama models (via SSH tunnel)
- [X] `curl http://localhost:26333/collections` returns Qdrant collections (via SSH tunnel)
- [X] n8n dashboard accessible at `http://localhost:25678` (via SSH tunnel)
- [ ] Router flow correctly classifies test queries into 3 tiers (pending Phase C)

After Phase C:
- [ ] Desktop clone of obsidian-nexus (on hold)
- [ ] Dropping a file in `_inbox/` → git commit → n8n processes → note appears in `atlas/`
- [ ] RAG query returns relevant context from vault
- [ ] `_system/log.md` records all operations

After Phase D:
- [ ] Cross-linker discovers unlinked mentions and proposes connections
- [ ] Lint report identifies orphan/stale notes
- [ ] Conversation insights flow back into `sources/conversations/`

---

## 14. Project Directory Structure (Divide & Conquer)

The `llm-orchestration/` repo is the **orchestration codebase** (not the vault itself). It contains development plans, configs, and automation code organized for parallel sub-agent work.

```
llm-orchestration/
│
├── ULTRAPLAN.md                         # This master plan (single source of truth)
│
├── plans/                               # Development plans (divide & conquer)
│   ├── phase-a-foundation/
│   │   ├── plan.md                      # Vault init, templates, taxonomy, git
│   │   └── checklist.md                 # Verification checklist
│   │
│   ├── phase-b-infrastructure/
│   │   ├── plan.md                      # Docker compose, Ollama, Qdrant, n8n, Gitea
│   │   ├── docker-compose.yml           # Desktop server stack definition
│   │   └── checklist.md
│   │
│   ├── phase-c-pipeline/
│   │   ├── plan.md                      # n8n flows: ingest, RAG, router
│   │   ├── n8n-flows/                   # Exported n8n flow JSON definitions
│   │   └── checklist.md
│   │
│   ├── phase-d-feedback-loops/
│   │   ├── plan.md                      # Cross-linker, decay scan, distillation
│   │   └── checklist.md
│   │
│   └── phase-e-refinement/
│       ├── plan.md                      # Tuning, plugins, iteration
│       └── checklist.md
│
├── agents/                              # Sub-agent orchestration configs
│   ├── router/
│   │   ├── system-prompt.md             # gemma4:e2b classification prompt
│   │   ├── examples.jsonl               # Few-shot classification examples
│   │   └── test-cases.md                # Validation test queries
│   │
│   ├── ingestor/
│   │   ├── system-prompt.md             # gemma4:26b extraction prompt
│   │   ├── merge-rules.md              # When to merge vs create new notes
│   │   └── frontmatter-spec.md          # Canonical frontmatter reference
│   │
│   ├── crosslinker/
│   │   ├── system-prompt.md             # Wikilink discovery prompt
│   │   └── graph-analytics.md           # Hub/orphan/bridge detection logic
│   │
│   ├── distiller/
│   │   ├── system-prompt.md             # Conversation → knowledge extraction
│   │   └── quality-filters.md           # What's worth distilling
│   │
│   └── linter/
│       ├── system-prompt.md             # Decay scan + contradiction detection
│       └── report-template.md           # Lint report format
│
├── scripts/                             # Automation scripts
│   ├── embed.py                         # Batch embedding via Ollama + Qdrant/ChromaDB
│   ├── delta-index.py                   # Git diff → selective re-embedding
│   ├── sync-chromadb.py                 # Desktop Qdrant → Ultrabook ChromaDB sync
│   └── vault-stats.py                   # CLI vault health metrics
│
├── configs/                             # Service configurations
│   ├── .env.example                     # Environment variables template
│   ├── qdrant-config.yaml               # Qdrant collection schemas
│   └── ollama-models.txt                # Models to pull on setup
│
├── vault-template/                      # Vault scaffold (copied to init new vault)
│   ├── _system/
│   ├── _inbox/
│   ├── atlas/
│   ├── sources/
│   ├── projects/
│   ├── areas/
│   ├── daily/
│   ├── templates/
│   ├── .skills/
│   ├── CLAUDE.md
│   ├── AGENTS.md
│   └── GEMINI.md
│
└── docs/                                # Internal documentation
    ├── architecture.md                  # System architecture diagram
    └── runbook.md                       # How to operate the stack
```

### Divide & Conquer — Sub-agent delegation

Each phase plan in `plans/` is self-contained enough that a sub-agent (Claude, Cursor, Codex) can pick it up and execute independently:

| Phase | Can be delegated to | Dependencies |
|-------|-------------------|--------------|
| A: Foundation | Any agent with filesystem access | None — do first |
| B: Infrastructure | Agent with Docker/CLI access | Phase A complete |
| C: Pipeline | Agent with n8n API access | Phase B running |
| D: Feedback Loops | Agent with vault + n8n access | Phase C working |
| E: Refinement | Human + Claude collaborative | Phases A-D stable |

Phases B and C can be worked in parallel once A is done (B sets up infra, C can be planned while B deploys).
