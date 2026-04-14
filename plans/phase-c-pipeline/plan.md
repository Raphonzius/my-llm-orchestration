# Phase C: Knowledge Pipeline

**Goal**: Build the n8n automation flows for vault ingest, RAG query, and delta re-indexing. Connect git webhooks to trigger processing.

**Dependencies**: Phase B running (services up and accessible).
**Delegatable to**: Agent with n8n API access and vault filesystem.

---

## Tasks

### C1. Build n8n Ingest Flow (Flow 2)

```
Gitea webhook (push event)
  → Parse git diff (identify new/changed files in _inbox/)
  → For each new file:
    → Read file content
    → Call Ollama gemma4:27b with ingestor system prompt
    → Extract: entities, concepts, patterns, key claims
    → Check existing atlas/ notes (via Qdrant similarity search)
    → Decision: MERGE into existing note OR CREATE new note
    → Write note to vault with frontmatter (provenance, confidence, etc.)
    → Git commit with structured message: "[llm:gemma4-27b] ingest: ..."
    → Git push to Gitea
  → Update _system/log.md
```

Key sub-components:
- Git diff parser (n8n Execute Command node)
- Ollama API call node (HTTP Request to localhost:11434)
- Qdrant similarity check node (HTTP Request to localhost:6333)
- File write node (Execute Command — write markdown)
- Git commit/push node

### C2. Build delta re-indexing

On every git push (after ingest or manual human edit):
- Parse git diff for changed .md files
- For each changed file:
  - Read frontmatter (parse YAML)
  - Generate embedding via Ollama mxbai-embed-large
  - Upsert to appropriate Qdrant collection (based on folder/type)
  - Store frontmatter fields as Qdrant payload (for filtering)

### C3. Build n8n RAG Query Flow (Flow 3)

```
Webhook receives query + optional domain hint
  → Call Ollama gemma4:e2b to classify domain + type
  → Build Qdrant filter (domain, type, status != archived)
  → Generate query embedding via mxbai-embed-large
  → Qdrant vector search (top-k=10, score threshold=0.7)
  → Read summaries from results (frontmatter.summary field)
  → Select top-3 most relevant based on summary match
  → Read full note content for top-3
  → Assemble context block
  → Route to appropriate tier (based on router classification)
  → Return response
  → Optionally: distill response to sources/conversations/
```

### C4. Initial bulk ingest

- Embed all existing vault notes
- Populate Qdrant collections
- Verify search returns relevant results

### C5. Testing

- Drop test article in `_inbox/clips/`
- Verify: git push → n8n triggers → note appears in `atlas/`
- Query against ingested content
- Verify `_system/log.md` updated

---

## n8n-flows/ directory

Export all flows as JSON for version control:
- `flow-1-router.json`
- `flow-2-ingest.json`
- `flow-3-rag-query.json`
- `flow-4-delta-index.json`

---

## Completion criteria

- [ ] Dropping file in `_inbox/` → auto-processing → note in `atlas/`
- [ ] Changed notes auto-embedded in Qdrant
- [ ] RAG query returns relevant context from vault
- [ ] `_system/log.md` records all operations
- [ ] All flows exported to `n8n-flows/` directory
