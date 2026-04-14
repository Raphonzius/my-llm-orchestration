# Human TODO — What Rafael needs to set up

> Things only you can do: hardware, installs, accounts, network, manual configs.
> Check off as you go. Order matters within each section, not between sections.

---

## Desktop Server (Ubuntu Server 24.04 LTS)

- [ ] Install Ubuntu Server 24.04 LTS on desktop (Ryzen 5 5600x / RTX 3060)
- [ ] Install NVIDIA drivers: `sudo apt install nvidia-driver-550` (or latest)
- [ ] Install Docker Engine: [docs.docker.com/engine/install/ubuntu](https://docs.docker.com/engine/install/ubuntu/)
- [ ] Install NVIDIA Container Toolkit: [docs.nvidia.com/datacenter/cloud-native](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/latest/install-guide.html)
  - Required so Docker containers (Ollama) can use the RTX 3060
- [ ] Set a static IP or hostname for the desktop on your LAN
  - Edit `/etc/netplan/*.yaml` or assign a static lease in your router
  - Note the IP — you'll use it everywhere as `DESKTOP_HOST`
- [ ] Copy `deploy/` to desktop: `scp -r deploy/ user@desktop:~/deploy/`
- [ ] SSH into desktop and run:
  ```bash
  cd ~/deploy
  sudo bash firewall-setup.sh          # open ports 11434/6333/5678
  docker compose up -d                  # start Ollama + Qdrant + n8n
  bash setup.sh                         # pull models, init Qdrant collections
  ```
- [ ] Clone obsidian-nexus on desktop:
  ```bash
  git clone https://github.com/Raphonzius/obsidian-nexus.git ~/obsidian-nexus
  ```
  (needed for n8n polling flow — vault is mounted into n8n container)

## GitHub

- [X] Create repo for obsidian-nexus: `https://github.com/Raphonzius/obsidian-nexus`
- [ ] Push llm-orchestration: `git push -u origin master`
- [ ] Push obsidian-nexus:
  ```bash
  cd C:\Users\rafae\obsidian-nexus
  git remote add origin https://github.com/Raphonzius/obsidian-nexus.git
  git push -u origin main
  ```

## Ultrabook Configuration

- [ ] Update `DESKTOP_HOST` IP in these files:
  - `obsidian-nexus/.env` — replace `192.168.1.XXX`
  - `obsidian-nexus/.githooks/post-push` — replace `192.168.1.XXX`
- [ ] Activate git hook:
  ```bash
  cd C:\Users\rafae\obsidian-nexus
  git config core.hooksPath .githooks
  ```
- [ ] Install Ollama on ultrabook (for local tier-1 models):
  - Download from [ollama.com](https://ollama.com)
  - `ollama pull gemma4:e2b`
  - `ollama pull gemma4:e4b`
  - `ollama pull mxbai-embed-large`
- [ ] Install ChromaDB on ultrabook (for local fast-recall):
  ```bash
  pip install chromadb
  chroma run --host localhost --port 8000
  ```
  (or run via Docker: `docker run -p 8000:8000 chromadb/chroma`)
- [ ] Install Obsidian community plugins:
  - **Templater** — Settings > Template folder: `templates/`
  - **Dataview** — query vault as database
  - **Graph Analysis** — betweenness centrality, clustering
  - **Obsidian Git** — auto-commit interval (every 10-30 min)
  - **Web Clipper** — browser extension, save to `_inbox/clips/`
  - **Tag Wrangler** — rename/merge tags vault-wide

## Verification

- [ ] From ultrabook Git Bash: `bash deploy/verify.sh <desktop-ip>`
  - Should show: Ollama OK, Qdrant OK, n8n OK
- [ ] Open Obsidian vault — confirm all folders, templates, vault-health.base render
- [ ] Test git hook: make a small edit, commit+push, check n8n received webhook
- [ ] Open n8n dashboard from ultrabook: `http://<desktop-ip>:5678`

---

## Not yet (future phases)

These are handled by agents once infrastructure is running:
- n8n flow creation (Phase C) — agent builds these
- Feedback loop automation (Phase D) — agent builds these
- Prompt tuning + RAG optimization (Phase E) — collaborative
