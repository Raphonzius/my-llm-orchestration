#!/bin/bash
# Desktop server setup — run AFTER docker compose up -d
# Usage: bash setup.sh
set -e

echo "=== Phase B: Desktop Server Setup ==="
echo ""

# --- B1: Wait for services ---
echo "[1/5] Waiting for services to be ready..."
for svc in "ollama:11434" "qdrant:6333" "n8n:5678" "gitea:3000"; do
  name="${svc%%:*}"
  port="${svc##*:}"
  printf "  Waiting for %-8s on port %s... " "$name" "$port"
  for i in $(seq 1 30); do
    if curl -s "http://localhost:$port" > /dev/null 2>&1; then
      echo "OK"
      break
    fi
    if [ $i -eq 30 ]; then
      echo "TIMEOUT (continue anyway)"
    fi
    sleep 2
  done
done
echo ""

# --- B2: Pull Ollama models ---
echo "[2/5] Pulling Ollama models (this may take a while)..."
models=("gemma4:e2b" "gemma4:e4b" "gemma4:27b" "mxbai-embed-large")
for model in "${models[@]}"; do
  echo "  Pulling $model..."
  docker exec ollama ollama pull "$model" 2>&1 | tail -1
done
echo ""

# --- B3: Verify Ollama ---
echo "[3/5] Verifying Ollama models..."
docker exec ollama ollama list
echo ""

# --- B4: Create Qdrant collections ---
echo "[4/5] Creating Qdrant collections..."
bash init-qdrant.sh
echo ""

# --- B5: Summary ---
echo "[5/5] Service status:"
echo "  Ollama:  http://localhost:11434"
echo "  Qdrant:  http://localhost:6333"
echo "  n8n:     http://localhost:5678"
echo "  Gitea:   http://localhost:3000"
echo ""
echo "=== Next steps ==="
echo "1. Open Gitea at http://localhost:3000 — create admin account"
echo "2. Create repo 'vault' in Gitea"
echo "3. Add Gitea remote to obsidian-nexus:"
echo "     cd /path/to/obsidian-nexus"
echo "     git remote add gitea http://localhost:3000/<user>/vault.git"
echo "     git push -u gitea main"
echo "4. In Gitea repo settings → Webhooks → Add webhook:"
echo "     URL: http://localhost:5678/webhook/vault-push"
echo "     Events: Push"
echo "5. Open n8n at http://localhost:5678 — import router flow"
echo "6. Run verify.sh from ultrabook to test LAN access"
echo ""
echo "=== Setup complete ==="
