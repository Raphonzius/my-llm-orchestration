# Human TODO — What Rafael needs to set up

> Things only you can do: hardware, installs, accounts, network, manual configs.
> Check off as you go. Order matters within each section, not between sections.

---

## 🔥 BIG HUNT — SAVE CLAUDE TOKEN, USE LOCAL FIRE

> Caveman say: Claude token expensive. Small brain run on ultrabook, big brain run on
> desktop. Claude only for hard thing. This the tier strat. Build NOW to stop burn.

**Goal:** route ~80% of work to local gemma4 models. Only hard reasoning hits Claude API.

### Step 1 — Ultrabook Ollama talks to desktop Ollama

- [ ] Verify desktop Ollama reachable via tunnel: `curl http://localhost:21434/api/tags`
- [ ] Pull big brain on desktop: `ollama pull gemma4:26b` (via `ssh nexus`)
- [ ] Ultrabook already has: `gemma4:e2b`, `gemma4:e4b`, `mxbai-embed-large` ✓
- [ ] Write small client helper — pick endpoint by model name:
  - `gemma4:e2b` / `gemma4:e4b` → `http://localhost:11434` (ultrabook)
  - `gemma4:26b` / embeddings for big corpus → `http://localhost:21434` (desktop tunnel)
  - `claude-*` → Anthropic API
- [ ] Put helper in `agents/router/` (to be created)

### Step 2 — Router model = gemma4:e2b as classifier

- [ ] Write router prompt (ultrabook, `gemma4:e2b`): input = user query, output = `{tier: 1|2|3, domain: [...], reason: "..."}`
- [ ] Classification signals (from ULTRAPLAN §1):
  - Token estimate of expected output
  - Number of knowledge domains involved
  - Whether RAG retrieval needed
  - Whether reasoning chain > 2 steps
  - Whether output is user-facing (quality matters)
- [ ] Test router on 20 sample queries — measure accuracy before wiring to n8n

### Step 3 — Three-tier execution path

| Tier | Model | Host | When |
|------|-------|------|------|
| 1 | `gemma4:e4b` | ultrabook (local) | drafts, lookup, classification, ~80% of work |
| 2 | `gemma4:26b` | desktop (GPU) | code gen, analysis, summarization, RAG synthesis |
| 3 | `claude-opus-4-7` | Anthropic API | planning, judgment, final output, complex RAG |

- [ ] Wire router → tier dispatch in n8n Flow 1 (Phase C work)
- [ ] Add budget guard: if daily Claude token usage > threshold, force tier 2 fallback
- [ ] Log every routed call to `_system/log.md` in vault with tier + token count

### Step 4 — Measure burn rate

- [ ] Baseline: count Claude tokens used today (before routing live)
- [ ] After routing live: compare — target 80%+ reduction for routine work
- [ ] Weekly review: which queries leaked to tier 3 that could've been tier 2? Tune router.

### Why this matter (caveman explain)

- Claude = good hunt tool, but each hunt cost mammoth
- Gemma4 = small spear, many mammoth free in own cave
- Without router, every query = mammoth hunt. Tribe go broke fast
- Router = smart shaman decide which spear for which beast

---

## 🪨 BIG HUNT 2 — ONE SKILL CAVE, ALL TRIBE SHARE

> Caveman say: every model tribe (Claude, Gemma, Ollama, future LLaMA) must read same
> stone tablet. One cave of skills. One cave of knowledge. No repeat work. No
> contradiction. Obsidian = human eye see. Qdrant = model brain smell.

**Goal:** single canonical skills + hooks repo that all agents consume. Vault (Obsidian) is human-navigable truth. Qdrant is vector-searchable projection of same truth. No model maintains its own private knowledge store.

### Step 1 — Canonical skill definitions in vault `.skills/`

Skill files already scaffolded in `obsidian-nexus/.skills/` (from Phase A):

- [ ] Flesh out `.skills/vault-ingest.md` — _inbox → atlas pipeline with provenance tags
- [ ] Flesh out `.skills/vault-query.md` — RAG against Qdrant with frontmatter pre-filter
- [ ] Flesh out `.skills/vault-lint.md` — orphan/stale/contradiction scan
- [ ] Flesh out `.skills/vault-crosslink.md` — discover unlinked mentions → propose `[[wikilinks]]`
- [ ] Flesh out `.skills/vault-distill.md` — conversation → atlas note extraction
- [ ] Flesh out `.skills/vault-status.md` — vault metrics + graph analytics report

Each skill file = frontmatter (name/description/triggers) + Context + Instructions + Rules.
Any LLM reads same file, gets same behavior.

### Step 2 — Bootstrap files per agent (thin pointers, fat skills)

- [X] `CLAUDE.md` — Claude Code / Desktop bootstrap (scaffolded)
- [X] `AGENTS.md` — generic agent bootstrap: Codex, LLaMA, future (scaffolded)
- [X] `GEMINI.md` — Gemini bootstrap (scaffolded)
- [ ] `OLLAMA.md` — modelfile template + system prompt pointing to `.skills/`
- [ ] Add `.cursor/rules/vault-agent.mdc` → reference `.skills/`
- [ ] Add `.windsurf/rules/vault-agent.md` → reference `.skills/`
- [ ] Add `.github/copilot-instructions.md` → reference `.skills/`

Pattern: each bootstrap is ~30 lines. All heavy content lives once in `.skills/`.

### Step 3 — Hooks: agents trigger skills automatically

- [ ] Claude Code hooks (`.claude/settings.json`):
  - `UserPromptSubmit` → if prompt matches vault skill trigger, auto-invoke
  - `PostToolUse` (on vault Write) → append to `_system/log.md` with provenance
  - `SessionStart` → load `_system/taxonomy.md` + recent `_system/insights.md`
- [ ] Ollama side — use Modelfile `SYSTEM` blocks that reference skill triggers
- [ ] n8n → receives `/webhook/vault-push` → dispatches to appropriate skill flow

### Step 4 — Two-layer knowledge: Obsidian (source) + Qdrant (index)

- [ ] **Obsidian** = source of truth. All writes go here first. Git = audit trail.
- [ ] **Qdrant** = derived index. Every vault change triggers re-embed → upsert to Qdrant.
  - Collections: `atlas`, `sources`, `projects`, `areas`
  - Filter before search: `domain`, `type`, `status != archived`, `confidence >= medium`
  - Embeddings: `mxbai-embed-large` (ultrabook + desktop, same model, same dim = 1024)
- [ ] **ChromaDB** = ultrabook-local L0/L1 cache: last 30 days + current workspace + conversations
- [ ] Never let Qdrant become primary — if it desyncs, nuke + rebuild from Obsidian

### Step 5 — Cross-agent rules (enforced by bootstrap files)

- [ ] Every LLM write must set: `provenance: extracted | synthesized | inferred`
- [ ] Every LLM write must set: `confidence: high | medium | low`
- [ ] Never overwrite `provenance: human` notes — merge or create variant
- [ ] Every skill invocation logged to `_system/log.md` with model + tier + tokens
- [ ] Commit message format: `[llm:{model}] {action}: {summary}` (ULTRAPLAN §8)

### Why this matter (caveman explain)

- Many agent tribe visit cave. Each read same wall paintings. Same rule. Same story.
- Knowledge in one place — Obsidian. Model see through smell — Qdrant.
- No model keep own secret scroll. Bad tribe. Cause fight. Cause drift.
- Hook = agent wake up, sniff air, know which skill to use. Not guess. Not ask shaman every time.

---

## 🛡️ BIG HUNT 3 — TAILSCALE MESH, REACH CAVE FROM ANY FOREST

> Caveman say: SSH tunnel only work when ultrabook in own cave (same wifi). Hunt far
> from home? Cave unreachable. Tailscale = magic rope between cave and ultrabook,
> work any forest, any coffee shop, any hotel. No open port on desktop = no bad
> tribe sniff around.

**Goal:** replace LAN-only SSH tunnel with Tailscale WireGuard mesh. Desktop reachable from anywhere without port forwarding or public exposure.

### Why Tailscale (vs current setup)

- Current: `ssh nexus` works only on `192.168.0.x` LAN — breaks when ultrabook leaves home
- Current: firewall locks Nexus ports to `192.168.0.106` (ultrabook IP) — useless off-LAN
- Tailscale: free solo tier (100 devices), WireGuard kernel module = <1% desktop CPU
- Tailscale: zero open ports on desktop, NAT traversal automatic, MagicDNS hostnames
- Tradeoff accepted: Tailscale Inc holds auth metadata (not traffic — P2P encrypted)

### Step 1 — Install + enroll both machines

- [ ] Create Tailscale account with Google SSO (rafael.informa@gmail.com)
- [ ] Desktop (CachyOS): `sudo pacman -S tailscale && sudo systemctl enable --now tailscaled`
- [ ] Desktop: `sudo tailscale up --ssh --hostname=nexus`
- [ ] Ultrabook (Windows): install Tailscale from tailscale.com/download
- [ ] Enable MagicDNS in admin console → desktop reachable as `nexus` (or `nexus.tailnet-name.ts.net`)
- [ ] Verify: `ping nexus` works from ultrabook while on mobile hotspot

### Step 2 — Harden with ACLs + key expiry

- [ ] Admin console → ACLs: restrict tailnet to only own two devices
- [ ] Enable tagged nodes: `tag:server` (desktop), `tag:client` (ultrabook)
- [ ] ACL rule: only `tag:client` can reach `tag:server` on ports `22, 11434, 6333, 6334, 5678`
- [ ] Enable key expiry (90 days default) — forces periodic re-auth
- [ ] Disable key expiry ONLY on desktop (headless, can't interactively re-auth)
- [ ] Enable Tailscale SSH on desktop — replaces OpenSSH key mgmt with Tailscale identity

### Step 3 — Migrate tunnel ports to direct Tailscale access

- [ ] Update `~/.ssh/config`: replace `HostName 192.168.0.112` with `HostName nexus`
- [ ] Remove `LocalForward` lines — no tunnel needed, hit desktop ports directly
- [ ] Update `.env.ultrabook`:
  - `OLLAMA_HOST=http://nexus:11434` (was `localhost:21434`)
  - `QDRANT_HOST=nexus`, `QDRANT_PORT=6333`, `QDRANT_GRPC_PORT=6334`
  - `N8N_HOST=http://nexus:5678`
- [ ] Update `.githooks/post-push` — replace `192.168.0.112` with `nexus`
- [ ] Update Docker bind: keep services on `127.0.0.1` + add Tailscale IP `100.x.x.x` (NOT `0.0.0.0`)
  - Better: use Tailscale Serve to expose only over tailnet: `tailscale serve --bg http://localhost:11434`
- [ ] Firewall: drop LAN-IP allowlist rules, only allow Tailscale interface `tailscale0`
- [ ] Decommission autossh + Windows Startup VBS wrapper — no longer needed

### Step 4 — Exit node + DNS for public wifi safety

- [ ] Configure desktop as exit node: `sudo tailscale up --advertise-exit-node`
- [ ] Approve exit node in admin console
- [ ] Ultrabook: toggle "use exit node" when on untrusted wifi (airport, cafe)
- [ ] All ultrabook traffic routes through home desktop when enabled — no public wifi sniffing

### Step 5 — Optional: Headscale self-host (if ever distrust Tailscale Inc)

- [ ] **SKIP unless needed.** Free tier + trust model fine for solo dev.
- [ ] If triggered: deploy Headscale on cheapest VPS (~$4/mo Hetzner)
- [ ] Point all clients at self-hosted control plane
- [ ] Keep WireGuard data plane (still <1% CPU on desktop)

### Why this matter (caveman explain)

- Cave in forest only reach when stand in own forest = bad. Tribe need travel.
- Magic rope (WireGuard) stretch any distance, bad tribe no see rope because encrypted
- No hole in cave wall (no port forward) = no wolf sneak in
- Small brain (ultrabook) always talk big brain (desktop) even at coffee shop
- Exit node = ultrabook hide true location behind cave when in hostile forest

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
- [ ] Install ChromaDB on ultrabook (for local fast-recall, Docker — keeps cave clean):
  ```bash
  docker volume create chromadb-data
  docker run -d --name chromadb \
    -p 8000:8000 \
    -v chromadb-data:/chroma/chroma \
    chromadb/chroma
  ```
  L0/L1 cache only — ephemeral, rebuilt from Qdrant. No git-sync needed.
- [ ] Qdrant: use gRPC (port `6334` desktop / `26334` tunnel) — faster, binary protocol:
  ```python
  from qdrant_client import QdrantClient
  client = QdrantClient(host="localhost", port=26334, prefer_grpc=True)
  ```
  REST (`26333`) kept as fallback only. See `configs/qdrant-config.yaml`.
- [X] Install Obsidian community plugins:
  - [X] **Templater** — template folder: `templates/` (all templates fixed for `<% tp.date.now("YYYY-MM-DD HH:mm") %>`)
  - [X] **Dataview** — vault database queries active
  - [ ] **Graph Analysis** — not found in community registry (optional, skip)
  - [X] **Obsidian Git** — auto-commit: 15 min, auto-push enabled
  - [X] **Web Clipper** — browser extension, configured to `_inbox/clips/`
  - [X] **Tag Wrangler** — installed

## Verification

- [X] From ultrabook: `bash deploy/verify.sh 192.168.0.112` — all passed
- [X] Open Obsidian vault — all folders, templates, vault-health.base render confirmed
  - Templater variables working (`<% tp.date.now("YYYY-MM-DD HH:mm") %>`)
  - vault-health queries active: Knowledge Inventory, Needs Attention, Provenance Audit, Recent Growth, Hub Nodes, Domain Coverage, Writing Velocity, Confidence Audit, High-Value Sources
  - Obsidian Git: auto-commit 15 min, auto-push enabled
- [X] Test Obsidian Git: small edits committed and pushed successfully
- [X] Open n8n dashboard: `http://localhost:25678` via SSH tunnel — owner account created
- [X] Webhook receiver flow created: `POST /webhook/vault-push` (active)
- [X] Webhook tested via curl — `{"message":"Workflow was started"}` confirmed
- [ ] Test post-push hook end-to-end: push from Obsidian Git → n8n receives automatically
- [ ] Clone obsidian-nexus on desktop + activate webhook processing logic

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
