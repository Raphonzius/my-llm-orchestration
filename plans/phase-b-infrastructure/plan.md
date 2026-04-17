# Phase B: Desktop Server Infrastructure

**Goal**: Stand up the always-on desktop server with Docker services: Ollama, Qdrant, n8n. Verify LAN access from ultrabook.

**OS**: CachyOS (Arch-based). Git sync via GitHub.

**Dependencies**: Phase A complete (vault exists in git).
**Delegatable to**: Agent with Docker/CLI access on desktop.

---

## Tasks

### B1. Docker Compose stack

Create `docker-compose.yml` with all services:

```yaml
services:
  ollama:
    image: ollama/ollama:latest
    ports: ["11434:11434"]
    volumes: ["ollama_data:/root/.ollama"]
    deploy:
      resources:
        reservations:
          devices:
            - capabilities: [gpu]
    restart: unless-stopped

  qdrant:
    image: qdrant/qdrant:latest
    ports: ["6333:6333", "6334:6334"]
    volumes: ["qdrant_data:/qdrant/storage"]
    restart: unless-stopped

  n8n:
    image: n8nio/n8n:latest
    ports: ["5678:5678"]
    volumes: ["n8n_data:/home/node/.n8n"]
    environment:
      - N8N_SECURE_COOKIE=false
    restart: unless-stopped

volumes:
  ollama_data:
  qdrant_data:
  n8n_data:
```

### B2. Pull Ollama models

```bash
docker exec ollama ollama pull gemma4:e2b
docker exec ollama ollama pull gemma4:e4b
docker exec ollama ollama pull gemma4:27b
docker exec ollama ollama pull mxbai-embed-large
```

### B3. Configure Qdrant collections

Create collections with payload indexes for frontmatter filtering:
- `atlas` — vector size matching mxbai-embed-large (1024 dim)
- `sources`
- `projects`
- `areas`

Each collection needs payload indexes on: `domain`, `type`, `status`, `confidence`, `provenance`, `created`, `modified`.

### B4. Configure GitHub

- Push obsidian-nexus to GitHub (already created)
- Set up GitHub webhook → n8n (push events)
  - Note: requires desktop reachable from GitHub (port forward / ngrok / cloudflare tunnel)
  - Alternative: n8n polling via Schedule trigger → git pull → process
- Clone vault repo on desktop

### B5. Configure n8n — Router Flow (Flow 1)

Basic webhook → Ollama (gemma4:e2b) → classification → tier routing.

### B6. LAN access verification

From ultrabook, verify:
- `curl http://<desktop-ip>:11434/api/tags` — Ollama models
- `curl http://<desktop-ip>:6333/collections` — Qdrant
- `http://<desktop-ip>:5678` — n8n dashboard

### B7. Firewall / network config

- Open ports 11434, 6333, 6334, 5678 on desktop (firewalld on CachyOS)
  - `sudo bash deploy/firewall-setup.sh` (auto-detects firewalld/ufw/iptables)
- Static DHCP lease on router for desktop IP (e.g. 192.168.0.109)

---

## Completion criteria

- [ ] `docker compose up -d` starts all 4 services
- [ ] All Ollama models pulled and responding
- [ ] Qdrant collections created with payload indexes
- [ ] GitHub webhook configured (or n8n polling as fallback)
- [ ] n8n router flow classifies test queries correctly
- [ ] All services accessible from ultrabook over LAN
