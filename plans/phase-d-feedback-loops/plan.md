# Phase D: Self-Improving Feedback Loops

**Goal**: Build the automated maintenance cycles that make the vault continuously improve: cross-linking, decay detection, conversation distillation, and ChromaDB sync.

**Dependencies**: Phase C working (ingest + RAG pipeline operational).
**Delegatable to**: Agent with vault + n8n access.

---

## Tasks

### D1. Cross-linker automation (weekly cron)

n8n flow triggered on cron schedule (weekly):

```
Scan all atlas/ notes
  → For each note:
    → Extract entity/concept names from title + aliases
    → Search all other notes for unlinked mentions of these names
    → If mention found without [[wikilink]]:
      → Add [[wikilink]] around mention
      → Update related: field in both notes' frontmatter
  → Git commit: "[llm:gemma4-27b] crosslink: discovered N new connections"
  → Update _system/log.md
```

### D2. Graph analytics (weekly, after cross-linker)

```
Read all notes' frontmatter (related: fields + wikilinks)
  → Build adjacency graph
  → Compute:
    → Hub pages: top-10 by connection count
    → Orphan pages: zero incoming + outgoing links
    → Bridge pages: nodes whose removal partitions the graph
    → Cluster analysis: domain groupings, cross-domain bridges
    → Density metrics per domain
  → Write _system/insights.md with findings
  → Flag orphans for review (update their status or enrich them)
```

### D3. Decay + quality scanner (monthly cron)

```
Scan all notes and flag:
  → status: seed AND created > 30 days ago → "STALE SEED"
  → provenance: inferred AND confidence: low → "LOW TRUST"
  → modified > 90 days AND status: evergreen → "VERIFY"
  → Contradictions: same entity in multiple notes with conflicting claims
     (use embeddings to find similar notes, then LLM to detect contradictions)
  → Write lint report to _system/lint-report-YYYY-MM.md
  → Update _system/log.md
```

### D4. Conversation distillation pipeline

n8n flow (triggered on-demand or on conversation export):

```
New conversation export lands in _inbox/imports/
  → Read conversation transcript
  → Call gemma4:27b with distiller system prompt:
    → Extract: decisions made, patterns discovered, problems solved
    → Extract: new entities, concepts, tools mentioned
    → Filter: skip small talk, trivial Q&A, debugging noise
  → Write distilled insights to sources/conversations/
  → Cross-link to relevant atlas/ notes
  → If novel pattern → create new atlas/patterns/ note
  → Git commit: "[llm:gemma4-27b] distill: extracted N insights from conversation"
```

### D5. ChromaDB sync (daily cron on ultrabook)

```
Ultrabook cron job:
  → Query Qdrant for notes modified in last 24 hours
  → For each changed note:
    → Pull embedding from Qdrant
    → Upsert to ChromaDB "recent" collection
  → Trim ChromaDB "recent" to last 30 days
  → Update ChromaDB "workspace" with current project notes
```

This keeps the ultrabook's local fast-recall up to date without re-embedding.

---

## Completion criteria

- [ ] Cross-linker discovers unlinked mentions and adds wikilinks
- [ ] Graph analytics writes meaningful insights to _system/insights.md
- [ ] Lint report identifies orphan/stale/low-trust notes
- [ ] Conversation distillation extracts useful patterns from transcripts
- [ ] ChromaDB on ultrabook stays synced with desktop Qdrant
