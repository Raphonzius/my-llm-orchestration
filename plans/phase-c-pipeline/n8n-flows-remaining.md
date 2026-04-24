# Remaining n8n Flows Plan

> Template: `n8n-flows/vault-push-pipeline.json`
> Lessons from flows 2+4 embedded throughout.

---

## Lessons Learned (apply to all flows)

- No Execute Command node in n8n v1 — always use HTTP Request → nexus-api
- Ollama from Docker: use `ollama:11434` (same Docker network, service name)
- nexus-api from Docker: use `http://host.docker.internal:8001` + ufw rule for 172.18.0.0/16
- Two workflows can't share webhook path — merge or use distinct paths
- Structured Output Parser wraps schema wrong — use Code node to parse LLM JSON
- Code node "Run Once for Each Item": return plain object, not array. Use `.item` for node refs
- Code node "Run Once for All Items": use `$input.all()`, return `[{json:{...}}]`
- Trailing spaces in URLs break requests silently
- Model names use colon: `gemma4:e4b`, `gemma4:26b`, `gemma4:e2b`
- Always `git pull` before reading vault files
- threading.Lock mutex for any write that checks-then-creates files
- LLM chain outputs `$json.text` — parse last code fence for JSON

---

## New API Endpoints Required

Add to `api/main.py` before building flows:

### RAG (Flow 3)
```python
POST /rag-embed          # embed query text → {vector: [...]}
POST /rag-search         # vector search with optional domain filter → {results: [...]}
```

### Curation (Flow 5)
```python
GET  /curate-list        # find atlas notes with status:seed → {files: [...]}
POST /curate-read        # read note ?path=X → {path, content, frontmatter}
POST /curate-write       # write curated note back (updates status seed→active)
POST /curate-commit      # git add atlas/ + commit + push
```

### Purge (Flow 6)
```python
GET  /purge-candidates   # find low-quality notes → {files: [...], criteria: {...}}
POST /purge-embed        # embed note for duplicate check
POST /purge-archive      # move note to _inbox/archived/ (never delete)
POST /purge-write-report # write _system/purge-candidates.md for human review
POST /purge-commit       # git commit + push
```

### Router (Flow 1)
```python
# No new API endpoints — router calls Ollama + Claude directly from n8n
```

---

## Flow 3 — RAG Query

**Webhook:** `POST /rag-query`
**Payload:** `{query: string, domain?: string, collection?: string, tier_hint?: 1|2|3}`

### Node sequence

```
Webhook
  ↓
normalize-rag-payload (Set)
  → query, domain (default: ""), collection (default: "atlas"), tier_hint (default: 0)
  ↓
embed-query (HTTP POST http://ollama:11434/api/embed)
  body: {model: "mxbai-embed-large", input: {{ $json.query }}}
  ↓
search-qdrant (HTTP POST host.docker.internal:8001/rag-search)
  body: {vector: {{ $json.embeddings[0] }}, collection, domain, limit: 10, threshold: 0.70}
  ↓
format-context (Code — Run Once for All Items)
  → build context block from top results
  → carry original query forward
  ↓
check-has-results (IF)
  true:  → route to LLM
  false: → respond-no-results (200, {status:"ok", answer:"No relevant context found."})
  ↓
llm-gemma4-e4b (Ollama model node, same credentials as vault-push-pipeline)
  ↓
rag-chain (Basic LLM Chain)
  system: "Answer the question using ONLY the provided context. Cite sources by file_path."
  user:   {{ $json.context_block + "\n\nQuestion: " + $json.query }}
  ↓
parse-answer (Code — Run Once for Each Item)
  → extract answer text from $json.text
  → attach sources list
  ↓
respond-success (Respond to Webhook 200)
```

### API endpoint specs

**POST /rag-embed** (wrapper, or call Ollama directly from n8n — prefer direct)

**POST /rag-search**
```python
class RagSearchRequest(BaseModel):
    vector: list[float]
    collection: str = "atlas"
    domain: str = ""          # empty = no filter
    limit: int = 10
    threshold: float = 0.70

class RagResult(BaseModel):
    file_path: str
    title: str
    summary: str
    score: float
    domain: str

class RagSearchResponse(BaseModel):
    status: str
    results: list[RagResult]
    total: int
```

Qdrant filter when domain non-empty:
```python
filter = {"must": [{"key": "domain", "match": {"value": domain}}]}
```

### format-context Code
```js
// Run Once for All Items
const items = $input.all();
const query = items[0]?.json.query || '';
const results = items[0]?.json.results || [];

const context_block = results.slice(0, 5).map((r, i) =>
  `[${i+1}] ${r.title} (${r.file_path})\n${r.summary}`
).join('\n\n');

const sources = results.slice(0, 5).map(r => ({
  title: r.title,
  path: r.file_path,
  score: r.score
}));

return [{json: {query, context_block, sources, result_count: results.length}}];
```

### parse-answer Code
```js
// Run Once for Each Item
const raw = $json.text || '';
return {
  answer: raw.trim(),
  query: $('format-context').first().json.query,
  sources: $('format-context').first().json.sources,
  model: 'gemma4:e4b'
};
```

---

## Flow 5 — Curation (Nightly)

**Trigger:** n8n Cron — `0 2 * * *` (2am daily)
**Purpose:** Rewrite `status: seed` atlas notes into clean structured notes via gemma4:26b

### Node sequence

```
Cron (2am daily)
  ↓
list-seed-notes (HTTP GET host.docker.internal:8001/curate-list)
  → {files: ["atlas/test-clip.md", ...]}
  ↓
check-has-seeds (IF files.length > 0)
  false: → respond-nothing-to-curate (n8n manual execution response or log)
  true:  ↓
split-seed-notes (Code — Run Once for All Items)
  → files.map(f => ({json: {path: f}}))
  ↓
read-seed-note (HTTP POST host.docker.internal:8001/curate-read?path={{ $json.path }})
  ↓
llm-gemma4-26b (Ollama model node — new credential pointing to gemma4:26b)
  ↓
curate-chain (Basic LLM Chain)
  system: [curation system prompt — see below]
  user:   {{ $json.content }}
  ↓
parse-curated (Code — Run Once for Each Item)
  ↓
write-curated (HTTP POST host.docker.internal:8001/curate-write)
  ↓
curate-aggregator (Code — Run Once for All Items)
  ↓
curate-commit (HTTP POST host.docker.internal:8001/curate-commit)
```

### Curation system prompt
```
You are a knowledge curator. Rewrite the given raw atlas note into a clean, well-structured note.

Rules:
- Preserve all factual content and key claims
- Write in clear, concise prose (not bullet soup)
- Add [[wikilinks]] around concepts, entities, and tools that deserve their own notes
- Keep frontmatter intact — only change: status: seed → status: active, modified: <now>
- Remove web clutter (ads, nav text, boilerplate)
- Add a "## See Also" section with related concept suggestions
- Never invent information not present in the source
- Output ONLY the complete rewritten markdown file (frontmatter + body)
```

### parse-curated Code
```js
// Run Once for Each Item
const raw = $json.text || '';
// curated note starts with ---
const noteMatch = raw.match(/(---[\s\S]*)/);
const note = noteMatch ? noteMatch[1] : raw;
return {
  path: $('read-seed-note').item.json.path,
  content: note.trim()
};
```

### API endpoint specs

**GET /curate-list**
```python
@app.get("/curate-list")
def curate_list() -> dict:
    """Find atlas notes with status: seed."""
    seeds = []
    for f in (VAULT_PATH / "atlas").rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        if "status: seed" in text or 'status: "seed"' in text:
            seeds.append(f.relative_to(VAULT_PATH).as_posix())
    return {"status": "ok", "files": seeds, "total": len(seeds)}
```

**POST /curate-write**
```python
class CurateWriteRequest(BaseModel):
    path: str        # vault-relative path
    content: str     # full rewritten markdown

@app.post("/curate-write")
def curate_write(req: CurateWriteRequest) -> dict:
    target = VAULT_PATH / req.path
    if not target.exists():
        raise HTTPException(404, f"Note not found: {req.path}")
    with _write_lock:
        target.write_text(req.content, encoding="utf-8")
    return {"status": "ok", "path": req.path, "action": "curated"}
```

---

## Flow 6 — Purge (Weekly)

**Trigger:** n8n Cron — `0 3 * * 0` (Sunday 3am)
**Purpose:** Find low-quality / duplicate atlas notes, archive or flag for human review

**NEVER hard-delete. Only archive to `_inbox/archived/` or write to purge-candidates.md.**

### Quality criteria (all must be true to archive automatically)
1. `status: seed` (never curated)
2. `confidence: low` OR no `key_claims` field
3. Created > 30 days ago (stale seed)
4. NOT `provenance: human`

### Duplicate criteria (flag only, never auto-archive)
- Qdrant score > 0.95 with another atlas note = near-duplicate

### Node sequence

```
Cron (Sunday 3am)
  ↓
list-purge-candidates (HTTP GET host.docker.internal:8001/purge-candidates)
  → {stale: [...], to_check_dups: [...]}
  ↓
Code: split stale → archive path
  ↓
archive-stale (HTTP POST host.docker.internal:8001/purge-archive loop per item)
  ↓
(separate branch) embed-for-dup-check (HTTP POST ollama:11434/api/embed loop)
  ↓
search-for-dups (HTTP POST host.docker.internal:8001/rag-search, threshold 0.95)
  ↓
Code: flag duplicates
  ↓
write-purge-report (HTTP POST host.docker.internal:8001/purge-write-report)
  ↓
purge-commit (HTTP POST host.docker.internal:8001/purge-commit)
```

### API endpoint specs

**GET /purge-candidates**
```python
@app.get("/purge-candidates")
def purge_candidates() -> dict:
    from datetime import datetime, timezone, timedelta
    stale_threshold = datetime.now(timezone.utc) - timedelta(days=30)
    stale, to_check = [], []
    for f in (VAULT_PATH / "atlas").rglob("*.md"):
        text = f.read_text(encoding="utf-8")
        if "provenance: human" in text:
            continue
        is_seed = "status: seed" in text
        is_low = "confidence: low" in text or "key_claims: []" in text
        mtime = datetime.fromtimestamp(f.stat().st_mtime, tz=timezone.utc)
        if is_seed and is_low and mtime < stale_threshold:
            stale.append(f.relative_to(VAULT_PATH).as_posix())
        elif is_seed:
            to_check.append(f.relative_to(VAULT_PATH).as_posix())
    return {"status": "ok", "stale": stale, "to_check_dups": to_check}
```

**POST /purge-archive**
```python
class PurgeArchiveRequest(BaseModel):
    path: str   # vault-relative

@app.post("/purge-archive")
def purge_archive(req: PurgeArchiveRequest) -> dict:
    src = VAULT_PATH / req.path
    archived_dir = VAULT_PATH / "_inbox" / "archived"
    archived_dir.mkdir(parents=True, exist_ok=True)
    dest = archived_dir / src.name
    with _write_lock:
        src.rename(dest)
    return {"status": "ok", "archived_to": dest.relative_to(VAULT_PATH).as_posix()}
```

---

## Flow 1 — Router (Tier Dispatch)

**Webhook:** `POST /route`
**Payload:** `{query: string, context?: string, force_tier?: 1|2|3}`
**Purpose:** Classify query tier via gemma4:e2b, dispatch to correct model

### Tier definitions (from ULTRAPLAN)
| Tier | Model | When |
|------|-------|------|
| 1 | `gemma4:e4b` (ultrabook) | drafts, lookup, classification |
| 2 | `gemma4:26b` (desktop GPU) | code gen, analysis, RAG synthesis |
| 3 | `claude-opus-4-7` (API) | planning, judgment, final output |

### Node sequence

```
Webhook
  ↓
normalize-route-payload (Set)
  → query, context (default ""), force_tier (default 0)
  ↓
check-force-tier (IF force_tier > 0)
  true:  → skip-to-dispatch (Set: tier = force_tier)
  false: ↓
llm-gemma4-e2b (Ollama model node — ultrabook at localhost:11434 when Tailscale done)
  ↓
classify-chain (Basic LLM Chain)
  system: [router system prompt]
  user:   {{ $json.query }}
  ↓
parse-classification (Code — Run Once for Each Item)
  ↓
dispatch (Switch node on tier value)
  tier 1: → call-tier1 (HTTP POST ollama:11434/api/generate, model gemma4:e4b)
  tier 2: → call-tier2 (HTTP POST ollama:11434/api/generate, model gemma4:26b)
  tier 3: → call-tier3 (HTTP POST Claude API)
  ↓ (merge branches)
format-response (Code)
  ↓
log-to-vault (HTTP POST host.docker.internal:8001/router-log)
  ↓
respond-success (Respond to Webhook 200)
```

### Router system prompt
```
You are a query router. Classify the query into exactly one tier.
Return ONLY JSON: {"tier": 1|2|3, "domain": ["tag1"], "reason": "one sentence"}

Tier 1 — simple/fast (gemma4:e4b): lookup, classification, yes/no, draft, template fill
Tier 2 — medium (gemma4:26b): code generation, summarization, analysis, RAG synthesis
Tier 3 — complex (claude): multi-step reasoning, planning, judgment, final user-facing output

Never route to tier 3 for anything a local model can handle.
```

### parse-classification Code
```js
// Run Once for Each Item
const raw = $json.text || '';
const fenceMatches = [...raw.matchAll(/```(?:json)?\s*([\s\S]*?)```/g)];
let jsonStr = fenceMatches.length > 0
  ? fenceMatches[fenceMatches.length - 1][1]
  : (raw.match(/(\{[\s\S]*?\})/) || ['', '{}'])[1];

let cls = {};
try { cls = JSON.parse(jsonStr.trim()); } catch(e) { cls = {}; }

const forceTier = $('normalize-route-payload').first().json.force_tier || 0;
return {
  query: $('normalize-route-payload').first().json.query,
  context: $('normalize-route-payload').first().json.context,
  tier: forceTier > 0 ? forceTier : (cls.tier || 2),
  domain: cls.domain || [],
  reason: cls.reason || ''
};
```

### call-tier3 (Claude API)
```
HTTP POST https://api.anthropic.com/v1/messages
Headers:
  x-api-key: {{ $env.ANTHROPIC_API_KEY }}
  anthropic-version: 2023-06-01
Body:
  {
    "model": "claude-opus-4-7",
    "max_tokens": 2048,
    "messages": [{"role": "user", "content": "{{ $json.query }}"}]
  }
```

### New API endpoint: /router-log
```python
class RouterLogRequest(BaseModel):
    query: str
    tier: int
    model: str
    tokens_estimate: int = 0
    reason: str = ""

@app.post("/router-log")
def router_log(req: RouterLogRequest) -> dict:
    log_file = VAULT_PATH / "_system" / "log.md"
    log_file.parent.mkdir(exist_ok=True)
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    entry = f"- {now} | tier:{req.tier} | {req.model} | {req.reason} | `{req.query[:80]}`\n"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(entry)
    return {"status": "ok"}
```

---

## Build Order

1. **Flow 3 (RAG)** — add `/rag-search` to API, build n8n flow, test with real query
2. **Flow 5 (Curation)** — add `/curate-*` to API, build n8n cron flow, test on seed notes
3. **Flow 6 (Purge)** — add `/purge-*` to API, build n8n cron flow, test with dummy stale notes
4. **Flow 1 (Router)** — build last, depends on all other flows being stable

## Critical Risks

- gemma4:26b curation quality: raw clips → clean notes requires good prompting. Test on 5 clips manually before enabling cron.
- Purge archive is one-way: archived notes not auto-restored. Write purge-candidates.md first, let human review before archiving.
- Router tier 3 = Claude API cost: add budget guard (daily token counter) before enabling in production.
- Cron flows run headless: no Respond to Webhook node needed, but errors must be logged to `_system/log.md`.
- gemma4:e2b not yet pulled on desktop: pull before building Flow 1 (`ollama pull gemma4:e2b` via ssh nexus).
