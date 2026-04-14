# Phase C: Pipeline — Verification Checklist

- [ ] n8n: Ingest flow (Flow 2) imported and active
- [ ] n8n: RAG query flow (Flow 3) imported and active
- [ ] n8n: Delta indexing flow imported and active
- [ ] Test: drop article in `_inbox/clips/` → git push
- [ ] Test: n8n triggers on push webhook
- [ ] Test: ingestor extracts concepts/entities from article
- [ ] Test: note appears in `atlas/` with correct frontmatter
- [ ] Test: `_system/log.md` records the ingest operation
- [ ] Test: new note is embedded and searchable in Qdrant
- [ ] Test: RAG query returns the ingested content as context
- [ ] Test: RAG query routes to correct tier
- [ ] Bulk: existing notes embedded in Qdrant
- [ ] All n8n flows exported to `plans/phase-c-pipeline/n8n-flows/`
