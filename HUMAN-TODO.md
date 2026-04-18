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
  - [X] `bash setup.sh` — models pulled, Qdrant collections initialized
  - [X] `bash verify.sh 192.168.0.112` — Ollama OK, Qdrant OK, n8n OK
- [X] Nexus headless boot installed:
  - systemd units: `nexus.target`, `nexus-compose.service`, `nexus-gh-auth.service`
  - gh token stored at `~/.config/nexus/gh-token` (no sudo, persists headless)
  - Limine entry added: **CachyOS Nexus (Headless)**
  - At boot: select that entry → headless, Docker stack auto-starts, no KDE/SDDM
  - SSH in at `raphonzius@192.168.0.112`
- [X] SSH hardened:
  - ed25519 key pair generated on ultrabook (`~/.ssh/id_ed25519`)
  - Public key copied to desktop `~/.ssh/authorized_keys`
  - Password auth disabled via `/etc/ssh/sshd_config.d/10-nexus-hardening.conf`
  - MobaXterm configured with private key — working
  - `ssh nexus` alias + LocalForward tunnels configured in `~/.ssh/config`
  - Docker services bound to `127.0.0.1` only — inaccessible from LAN
  - Tunnel ports on ultrabook: `21434` (Ollama), `26333/26334` (Qdrant), `25678` (n8n)
- [X] Set up autossh persistent tunnel (auto-reconnects on network drop):
  - [X] SSH key config: `C:\Users\rafae\.ssh\config`
  - [X] Tunnel startup script: `C:\Users\rafae\.ssh\start_tunnel.sh`
  - [X] Windows Startup VBS wrapper: `C:\Users\rafae\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup\nexus-tunnel.vbs`
  - Runs at user logon via Startup folder (no Task Scheduler needed)
- [ ] Clone obsidian-nexus on desktop:
  ```bash
  git clone https://github.com/Raphonzius/obsidian-nexus.git ~/obsidian-nexus
  ```

## GitHub

- [X] Create repo for obsidian-nexus: `https://github.com/Raphonzius/obsidian-nexus`
- [X] Push llm-orchestration to origin/main
- [X] Push obsidian-nexus with machine-specific configs:
  - [X] `.env.ultrabook` — tunnel ports (21434, 26333, 25678)
  - [X] `.env.desktop` — direct localhost access (11434, 6333, 5678)
  - [X] Removed generic `.env` (redundant)
  - [X] All templates fixed for Templater syntax
  - [X] vault-health enhanced with 5 Dataview queries
  - Latest: `e9c7adf` — vault-health improvements

## Ultrabook Configuration

- [X] Update `DESKTOP_HOST` IP and configure environment:
  - [X] `.env.ultrabook` — uses tunnel ports (via `ssh nexus` alias)
  - [X] `.githooks/post-push` — updated to `192.168.0.112`
  - [X] Removed `.env.local` (now using machine-specific `.env.*` files)
- [X] Activate git hook:
  ```bash
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
- [X] Install Obsidian community plugins:
  - [X] **Templater** — template folder: `templates/` (all templates fixed for `<% tp.date.now("YYYY-MM-DD HH:mm") %>`)
  - [X] **Dataview** — vault database queries active
  - [ ] **Graph Analysis** — not found in community registry (optional, skip)
  - [X] **Obsidian Git** — auto-commit: 15 min, auto-push enabled
  - [ ] **Web Clipper** — browser extension, save to `_inbox/clips/`
  - [ ] **Tag Wrangler** — rename/merge tags vault-wide

## Verification

- [X] From ultrabook: `bash deploy/verify.sh 192.168.0.112` — all passed
- [X] Open Obsidian vault — all folders, templates, vault-health.base render confirmed
  - Templater variables working (`<% tp.date.now("YYYY-MM-DD HH:mm") %>`)
  - vault-health queries active: Knowledge Inventory, Needs Attention, Provenance Audit, Recent Growth, Hub Nodes, Domain Coverage, Writing Velocity, Confidence Audit, High-Value Sources
  - Obsidian Git: auto-commit 15 min, auto-push enabled
- [X] Test Obsidian Git: small edits committed and pushed successfully
- [ ] Test webhook: push from ultrabook, verify n8n receives vault-push webhook
- [ ] Open n8n dashboard: `http://localhost:25678` via SSH tunnel (requires desktop clone)

## Desktop — Next Session

- [ ] Clone obsidian-nexus on desktop:
  ```bash
  git clone https://github.com/Raphonzius/obsidian-nexus.git ~/obsidian-nexus
  cp ~/obsidian-nexus/.env.desktop ~/obsidian-nexus/.env.local
  ```
- [ ] Verify webhook infrastructure (post-push hook):
  - Push from ultrabook vault
  - Monitor n8n for incoming `vault-push` webhook at `/webhook/vault-push`
- [ ] Install remaining Obsidian plugins (optional for ultrabook):
  - Web Clipper + Tag Wrangler

---

## Not yet (future phases)

These are handled by agents once infrastructure is running:
- n8n flow creation (Phase C) — agent builds these
- Feedback loop automation (Phase D) — agent builds these
- Prompt tuning + RAG optimization (Phase E) — collaborative
