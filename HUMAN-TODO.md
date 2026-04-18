# Human TODO — What Rafael needs to set up

> Things only you can do: hardware, installs, accounts, network, manual configs.
> Check off as you go. Order matters within each section, not between sections.

---

## Desktop Server (CachyOS — Arch-based)

> **Decision**: using existing CachyOS install instead of dual-booting Ubuntu Server.
> Reason: saves hours of setup, Docker is OS-agnostic, CachyOS has better hardware
> optimization and up-to-date NVIDIA drivers.

- [X] CachyOS installed on desktop (Ryzen 5 5600x / RTX 3060)
- [X] Limine bootloader already working
- [ ] Verify NVIDIA drivers loaded: `nvidia-smi` should show RTX 3060
  - If missing: `sudo pacman -S nvidia nvidia-utils` + reboot
- [ ] Install Docker + Compose:
  ```bash
  sudo pacman -S docker docker-compose
  sudo systemctl enable --now docker
  sudo usermod -aG docker $USER   # then logout/login
  ```
- [ ] Install NVIDIA Container Toolkit:
  ```bash
  sudo pacman -S nvidia-container-toolkit
  sudo systemctl restart docker
  ```
- [ ] Verify Docker can see the GPU:
  ```bash
  docker run --rm --gpus all nvidia/cuda:12.4.0-base-ubuntu22.04 nvidia-smi
  ```
  Should show the RTX 3060 from inside the container.
- [ ] Set a static DHCP lease on your router for the desktop IP
  - Current IP: `192.168.0.112` (confirm it stays the same after reboot)
  - Note it — you'll use it everywhere as `DESKTOP_HOST`
- [ ] Clone both repos on desktop:
  ```bash
  git clone https://github.com/Raphonzius/my-llm-orchestration.git ~/llm-orchestration
  git clone https://github.com/Raphonzius/obsidian-nexus.git ~/obsidian-nexus
  ```
- [ ] Run deploy scripts:
  ```bash
  cd ~/llm-orchestration/deploy
  sudo bash firewall-setup.sh          # auto-detects firewalld, opens 11434/6333/6334/5678
  docker compose up -d                  # start Ollama + Qdrant + n8n
  bash setup.sh                         # pull models, init Qdrant collections
  ```

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

- [ ] Update `DESKTOP_HOST` IP (current: `192.168.0.112`) in these files:
  - `obsidian-nexus/.env` — replace `192.168.1.XXX` with `192.168.0.112`
  - `obsidian-nexus/.env.local` — same
  - `obsidian-nexus/.githooks/post-push` — same
- [ ] Activate git hook:
  ```bash
  cd C:\Users\rafae\obsidian-nexus
  git config core.hooksPath .githooks
  ```
- [x] Install Ollama on ultrabook (for local tier-1 models):
  - [x] Download from [ollama.com](https://ollama.com)
  - [x] `ollama pull gemma4:e2b`
  - [x] `ollama pull gemma4:e4b`
  - [x] `ollama pull mxbai-embed-large`
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

- [ ] From ultrabook Git Bash: `bash deploy/verify.sh 192.168.0.112`
  - Should show: Ollama OK, Qdrant OK, n8n OK
- [ ] Open Obsidian vault — confirm all folders, templates, vault-health.base render
- [ ] Test git hook: make a small edit, commit+push, check n8n received webhook
- [ ] Open n8n dashboard from ultrabook: `http://192.168.0.112:5678`

---

## Not yet (future phases)

These are handled by agents once infrastructure is running:
- n8n flow creation (Phase C) — agent builds these
- Feedback loop automation (Phase D) — agent builds these
- Prompt tuning + RAG optimization (Phase E) — collaborative
