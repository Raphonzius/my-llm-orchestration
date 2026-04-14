# Phase E: Refinement

**Goal**: Tune prompts, retrieval quality, and add Obsidian community plugins for the best human experience. This phase is iterative and collaborative.

**Dependencies**: Phases A-D stable and operational.
**Delegatable to**: Human + Claude collaborative (requires judgment).

---

## Tasks

### E1. Tune router classification prompts

- Collect real queries from usage logs
- Build test suite of 50+ queries with expected tier classification
- Iterate on gemma4:e2b system prompt until >90% accuracy
- Store final prompt + test cases in `agents/router/`

### E2. Tune RAG retrieval

- Experiment with top-k values (5, 10, 20)
- Tune score threshold (0.6, 0.7, 0.8)
- Test context assembly strategies:
  - Summary-only vs summary + first paragraph vs full note
  - How many full notes to include (2, 3, 5)
- Measure: answer relevance, token usage, latency

### E3. Obsidian community plugins

Recommended plugins to install:
- **Templater** — Advanced template engine (for templates/ with dynamic dates, prompts)
- **Dataview** — Query vault as database (complement to Base)
- **Graph Analysis** — Betweenness centrality, clustering coefficients
- **Obsidian Git** — Auto-commit on interval from ultrabook
- **Web Clipper** — Save articles directly to `_inbox/clips/`
- **Tag Wrangler** — Rename/merge tags vault-wide

### E4. Monitor provenance/confidence accuracy

- Periodically review LLM-tagged provenance and confidence
- Are "extracted" facts actually extracted? Are "high" confidence notes reliable?
- Adjust ingestor/distiller prompts based on findings

### E5. Performance monitoring

- Track: ingest latency, embedding time, query latency, n8n flow duration
- Set up n8n error notifications (Slack/email/webhook)
- Monitor Qdrant collection sizes and query performance

---

## Completion criteria

- [ ] Router classifies >90% of test queries correctly
- [ ] RAG returns relevant answers with acceptable latency
- [ ] Obsidian plugins installed and configured
- [ ] Provenance tags are accurate (spot-check 20 notes)
- [ ] Monitoring/alerting in place for flow failures
