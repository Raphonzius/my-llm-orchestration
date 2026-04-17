# Human TODO — What Rafael needs to set up

> Things only you can do: hardware, installs, accounts, network, manual configs.
> Check off as you go. Order matters within each section, not between sections.

---

## Desktop Server (CachyOS — Arch-based)

> **Decision**: using existing CachyOS install instead of dual-booting Ubuntu Server.
> Reason: saves hours of setup, Docker is OS-agnostic, CachyOS has better hardware
> optimization and up-to-date NVIDIA drivers.

- [X] CachyOS installed on desktop (Ryzen 5 5600x / RTX 3050 8GB)
- [X] Limine bootloader already working
- [X] Verify NVIDIA drivers loaded: driver 595.58.03, CUDA 13.2 — confirmed RTX 3050
- [X] System updated: `sudo pacman -Syu`
- [X] Install Docker + Compose
- [X] Install NVIDIA Container Toolkit
- [X] Verify Docker can see the GPU — RTX 3050 confirmed inside container
- [X] Static IP set to `192.168.0.112` via NetworkManager (no router config needed)
- [X] Firewall configured: all Nexus ports + SSH locked to ultrabook (`192.168.0.106`) only
- [X] Clone repo on desktop: `~/Projects/my-llm-orchestration`
- [X] Run deploy scripts:
  - [X] `sudo bash firewall-setup.sh` — ports open
  - [X] `docker compose up -d` — Ollama + Qdrant + n8n running
  - [X] Ollama models pulled (gemma4:26b confirmed), Qdrant collections ready
  - [ ] `bash setup.sh` — run to pull remaining models + finalize Qdrant init
- [X] Nexus headless boot installed:
  - systemd units: `nexus.target`, `nexus-compose.service`, `nexus-gh-auth.service`
  - gh token stored at `~/.config/nexus/gh-token` (no sudo, persists headless)
  - Limine entry added: **CachyOS Nexus (Headless)**
  - At boot: select that entry → headless, Docker stack auto-starts, no KDE/SDDM
  - SSH in at `raphonzius@192.168.0.112`
- [ ] Clone obsidian-nexus on desktop:
  ```bash
  git clone https://github.com/Raphonzius/obsidian-nexus.git ~/obsidian-nexus
  ```

## GitHub

- [X] Create repo for obsidian-nexus: `https://github.com/Raphonzius/obsidian-nexus`
- [X] Push llm-orchestration to origin/main
- [ ] Push obsidian-nexus:
  ```bash
  cd C:\Users\rafae\obsidian-nexus
  git remote add origin https://github.com/Raphonzius/obsidian-nexus.git
  git push -u origin main
  ```

## Ultrabook Configuration

- [ ] Update `DESKTOP_HOST` IP in these files (new IP: `192.168.0.112`):
  - `obsidian-nexus/.env` — replace placeholder with `192.168.0.112`
  - `obsidian-nexus/.env.local` — same
  - `obsidian-nexus/.githooks/post-push` — same
- [ ] Activate git hook:
  ```bash
  cd C:\Users\rafae\obsidian-nexus
  git config core.hooksPath .githooks
  ```
- [X] Install Ollama on ultrabook (for local tier-1 models):
  - [X] Download from [ollama.com](https://ollama.com)
  - [X] `ollama pull gemma4:e2b`
  - [X] `ollama pull gemma4:e4b`
  - [X] `ollama pull mxbai-embed-large`
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

- [ ] From ultrabook: `bash deploy/verify.sh 192.168.0.112`
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
