# Phase B: Desktop Server Infrastructure

**Goal**: Stand up the always-on desktop server with Docker services: Ollama, Qdrant, n8n, and Gitea. Verify LAN access from ultrabook.

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

  gitea:
    image: gitea/gitea:latest
    ports: ["3000:3000", "2222:22"]
    volumes: ["gitea_data:/data"]
    restart: unless-stopped

volumes:
  ollama_data:
  qdrant_data:
  n8n_data:
  gitea_data:
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

### B4. Configure Gitea

- Create vault repository
- Set up webhook → n8n (push events)
- Clone vault repo on desktop

### B5. Configure n8n — Router Flow (Flow 1)

Basic webhook → Ollama (gemma4:e2b) → classification → tier routing.

### B6. LAN access verification

From ultrabook, verify:
- `curl http://<desktop-ip>:11434/api/tags` — Ollama models
- `curl http://<desktop-ip>:6333/collections` — Qdrant
- `http://<desktop-ip>:5678` — n8n dashboard
- `http://<desktop-ip>:3000` — Gitea

### B7. Firewall / network config

- Open ports 11434, 6333, 5678, 3000 on desktop
- Consider static IP or hostname for desktop on LAN

---

## Completion criteria

- [ ] `docker compose up -d` starts all 4 services
- [ ] All Ollama models pulled and responding
- [ ] Qdrant collections created with payload indexes
- [ ] Gitea repo created, webhook configured
- [ ] n8n router flow classifies test queries correctly
- [ ] All services accessible from ultrabook over LAN
