# Operational Runbook

Infrastructure: desktop server (Ubuntu 24.04, Docker) + ultrabook (Windows 11).
Vault: `obsidian-nexus` git repo, synced via GitHub.

## 1. Starting and Stopping the Stack

All commands run on the desktop server unless noted otherwise.

```bash
# Start all services (detached)
cd ~/llm-orchestration/deploy
docker compose up -d

# Stop all services (preserves volumes)
docker compose down

# Restart a single service
docker compose restart ollama

# Check health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"
curl -s http://localhost:11434/api/tags | python3 -c "import sys,json; [print(m['name']) for m in json.load(sys.stdin)['models']]"
curl -s http://localhost:6333/collections | python3 -c "import sys,json; [print(c['name']) for c in json.load(sys.stdin)['result']['collections']]"
curl -s -o /dev/null -w '%{http_code}' http://localhost:5678
```

From the ultrabook, verify LAN connectivity:

```bash
bash ~/llm-orchestration/deploy/verify.sh <desktop-ip>
```

## 2. Adding a New Ollama Model

```bash
# Pull on desktop
docker exec ollama ollama pull <model-name>

# Verify
docker exec ollama ollama list

# Pull on ultrabook (native Ollama install)
ollama pull <model-name>
```

Update `configs/ollama-models.txt` to keep the manifest current. Current desktop models: `gemma4:e2b`, `gemma4:e4b`, `gemma4:27b`, `mxbai-embed-large`.

To remove an unused model: `docker exec ollama ollama rm <model-name>`.

## 3. Rebuilding Qdrant Collections

**When to rebuild:**
- After changing the embedding model or vector dimensions
- If a collection is corrupted or returns inconsistent results
- After a bulk vault restructure (renaming top-level folders)

**How:**

```bash
# Step 1: Delete and recreate collections (from desktop)
bash ~/llm-orchestration/deploy/init-qdrant.sh

# Step 2: Full re-embed from vault
python3 ~/llm-orchestration/scripts/embed.py \
    --vault-path ~/obsidian-nexus \
    --qdrant-url http://localhost:6333 \
    --ollama-url http://localhost:11434

# Or use delta-index with --full flag
python3 ~/llm-orchestration/scripts/delta-index.py \
    --vault-path ~/obsidian-nexus --full
```

Collections created by init-qdrant.sh: `atlas`, `sources`, `projects`, `areas`. Each has payload indexes on: domain, type, status, provenance, confidence, created, modified, tags.

For incremental updates after normal edits, delta-index.py without `--full` uses git diff + mtime to re-embed only changed files.

## 4. Vault Maintenance

### Manual ingest (files dropped in _inbox/)

Files in `_inbox/` are not indexed by the embedding scripts (skipped by design). To process them:

1. Review the file, add frontmatter (title, type, domain, tags, status, provenance).
2. Move it to the correct top-level folder (`atlas/`, `sources/`, `projects/`, or `areas/`).
3. Commit and push.
4. Run delta-index to pick up the new file:
   ```bash
   python3 ~/llm-orchestration/scripts/delta-index.py --vault-path ~/obsidian-nexus
   ```

### Cross-linking

Trigger cross-linking when:
- A batch of new notes has been ingested (5+ notes at once)
- Vault structure feels siloed (notes in one domain not referencing related notes)

### Lint (monthly)

Run the linter agent against the vault to catch:
- Missing frontmatter fields
- Orphaned notes (no inbound links)
- Stale status values
- Broken wikilinks

### Vault stats (quick health check)

Check `_system/vault-health.base` in Obsidian for an at-a-glance view. For a CLI check:

```bash
cd ~/obsidian-nexus
echo "Total notes: $(find atlas sources projects areas -name '*.md' | wc -l)"
echo "Inbox pending: $(ls _inbox/ 2>/dev/null | wc -l)"
echo "Last commit: $(git log -1 --format='%cd (%s)' --date=short)"
```

## 5. Troubleshooting

### Ollama OOM (model too large for VRAM)

Symptoms: Ollama returns 500 or the container restarts. `docker logs ollama` shows CUDA OOM.

Fix:
```bash
# Check which model is loaded
curl -s http://localhost:11434/api/ps | python3 -m json.tool

# Unload all models
curl -X DELETE http://localhost:11434/api/generate -d '{"model":"<loaded-model>","keep_alive":0}'

# Use a smaller model, or set OLLAMA_MAX_LOADED_MODELS=1 in docker-compose env
```

For the desktop GPU (NVIDIA), `gemma4:27b` is the largest model that fits. If it OOMs, ensure no other model is loaded concurrently.

### Qdrant collection corruption

Symptoms: search returns empty results or errors for a collection that should have data.

Fix: rebuild from vault (vault is source of truth, vectors are derived data).
```bash
# Delete the broken collection
curl -X DELETE http://localhost:6333/collections/<name>

# Recreate and re-embed
bash ~/llm-orchestration/deploy/init-qdrant.sh
python3 ~/llm-orchestration/scripts/embed.py --vault-path ~/obsidian-nexus
```

### n8n flow errors

```bash
# Check container logs
docker logs n8n --tail 100

# Access the n8n UI for execution history
# http://<desktop-ip>:5678 -> Executions tab
```

Common issues:
- Webhook not reachable from GitHub: check firewall (`sudo ufw status`) and port forwarding.
- Vault mount stale: `docker compose restart n8n` to remount.

### Git sync conflicts (vault edited on two machines)

```bash
# On the machine with the conflict
cd ~/obsidian-nexus    # or C:\Users\rafae\obsidian-nexus on ultrabook
git status
git diff

# For simple conflicts: edit the file, pick the right version
git add <file>
git commit -m "resolve sync conflict in <file>"
git push

# Nuclear option (if vault is a mess): reset to remote
git fetch origin
git reset --hard origin/main
```

Prevention: always pull before editing. Obsidian Git plugin should auto-pull on open.

### ChromaDB sync stale (ultrabook)

Symptoms: local queries return outdated results, or ChromaDB is missing recent notes.

```bash
# From ultrabook
python3 ~/llm-orchestration/scripts/sync-chromadb.py \
    --qdrant-url http://<desktop-ip>:6333 \
    --chromadb-url http://localhost:8000 \
    --days 30

# Dry run first to see what would sync
python3 ~/llm-orchestration/scripts/sync-chromadb.py \
    --qdrant-url http://<desktop-ip>:6333 \
    --chromadb-url http://localhost:8000 \
    --days 30 --dry-run
```

## 6. Backup and Recovery

| Asset | Strategy | Recovery |
|-------|----------|----------|
| Vault (obsidian-nexus) | Git history IS the backup. Push regularly. | `git clone` from GitHub. |
| Qdrant vectors | Derived data. No separate backup needed. | Re-embed from vault: `embed.py --vault-path ...` |
| ChromaDB (ultrabook) | Derived data synced from Qdrant. | Re-run `sync-chromadb.py`. |
| n8n flows | Export as JSON. | Import JSON in n8n UI. |
| Ollama models | Pulled from registry. | `docker exec ollama ollama pull <model>` or re-run `setup.sh`. |
| Docker volumes | Persist across restarts. Lost on `docker compose down -v`. | Re-run setup.sh for full rebuild. |

n8n flow backup:
```bash
# Export all workflows (run on desktop)
mkdir -p ~/llm-orchestration/plans/phase-c-pipeline/n8n-flows
docker exec n8n n8n export:workflow --all --output=/tmp/flows.json
docker cp n8n:/tmp/flows.json ~/llm-orchestration/plans/phase-c-pipeline/n8n-flows/
```

Key principle: the vault is the single source of truth. Everything else (vectors, ChromaDB, indexes) is derived and can be rebuilt from it.

## 7. Common Commands Cheat Sheet

| Operation | Command |
|-----------|---------|
| Start stack | `cd ~/llm-orchestration/deploy && docker compose up -d` |
| Stop stack | `cd ~/llm-orchestration/deploy && docker compose down` |
| Service status | `docker ps --format "table {{.Names}}\t{{.Status}}"` |
| LAN verify (from ultrabook) | `bash verify.sh <desktop-ip>` |
| Pull model | `docker exec ollama ollama pull <model>` |
| List models | `docker exec ollama ollama list` |
| Remove model | `docker exec ollama ollama rm <model>` |
| Init Qdrant collections | `bash deploy/init-qdrant.sh` |
| Full re-embed | `python3 scripts/embed.py --vault-path ~/obsidian-nexus` |
| Delta re-index | `python3 scripts/delta-index.py --vault-path ~/obsidian-nexus` |
| Sync ChromaDB (ultrabook) | `python3 scripts/sync-chromadb.py --qdrant-url http://desktop:6333 --chromadb-url http://localhost:8000 --days 30` |
| Vault note count | `find atlas sources projects areas -name '*.md' \| wc -l` |
| Inbox pending | `ls _inbox/ \| wc -l` |
| n8n logs | `docker logs n8n --tail 100` |
| Export n8n flows | `docker exec n8n n8n export:workflow --all --output=/tmp/flows.json` |
| Vault pull (desktop) | `cd ~/obsidian-nexus && git pull` |
| Vault push (ultrabook) | `cd obsidian-nexus && git add -A && git commit -m "sync" && git push` |
