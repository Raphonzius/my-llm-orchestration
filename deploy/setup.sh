#!/bin/bash
# Desktop server setup (Ubuntu Server 24.04 LTS)
# Run AFTER docker compose up -d
# Usage: bash setup.sh
set -e

echo "=== Phase B: Desktop Server Setup ==="
echo ""

# --- B1: Wait for services ---
echo "[1/4] Waiting for services to be ready..."
for svc in "ollama:11434" "qdrant:6333" "n8n:5678"; do
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
echo "[2/4] Pulling Ollama models (this may take a while)..."
models=("gemma4:e2b" "gemma4:e4b" "gemma4:27b" "mxbai-embed-large")
for model in "${models[@]}"; do
  echo "  Pulling $model..."
  docker exec ollama ollama pull "$model" 2>&1 | tail -1
done
echo ""

# --- B3: Verify Ollama ---
echo "[3/4] Verifying Ollama models..."
docker exec ollama ollama list
echo ""

# --- B4: Create Qdrant collections ---
echo "[4/4] Creating Qdrant collections..."
bash init-qdrant.sh
echo ""

# --- Summary ---
DESKTOP_IP=$(hostname -I | awk '{print $1}')
echo "=== Service status ==="
echo "  Ollama:  http://localhost:11434  (LAN: http://$DESKTOP_IP:11434)"
echo "  Qdrant:  http://localhost:6333   (LAN: http://$DESKTOP_IP:6333)"
echo "  n8n:     http://localhost:5678   (LAN: http://$DESKTOP_IP:5678)"
echo ""
echo "=== Next steps ==="
echo "1. If not done yet, open firewall: sudo bash firewall-setup.sh"
echo "2. Push obsidian-nexus to GitHub (if not already):"
echo "     cd /path/to/obsidian-nexus"
echo "     git remote add origin https://github.com/<user>/obsidian-nexus.git"
echo "     git push -u origin main"
echo "3. Set up GitHub webhook → n8n:"
echo "     Repo Settings → Webhooks → Add webhook"
echo "     URL: http://$DESKTOP_IP:5678/webhook/vault-push"
echo "     Content type: application/json"
echo "     Events: Just the push event"
echo "   NOTE: requires desktop to be reachable from GitHub (port forward or tunnel)"
echo "   Alternative: use n8n polling (Schedule trigger → git pull → process)"
echo "4. Open n8n at http://localhost:5678 — import router flow"
echo "5. From ultrabook (Git Bash): bash verify.sh $DESKTOP_IP"
echo ""
echo "=== Setup complete ==="
