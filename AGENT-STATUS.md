# Agent Status — What's done, what's pending, where to find instructions

> For any AI agent picking up work on this project.
> Each section links to the relevant instruction files.

---

## Project overview

3-tier AI orchestration (gemma4 local → gemma4 desktop → Claude cloud) with an Obsidian vault (`obsidian-nexus`) as persistent knowledge layer. Two repos:

| Repo | Path | Purpose |
|------|------|---------|
| `llm-orchestration` | `C:\Users\rafae\llm-orchestration` | Orchestration code, plans, agent configs, deploy scripts |
| `obsidian-nexus` | `C:\Users\rafae\obsidian-nexus` | The Obsidian vault — knowledge base that LLMs read/write |

Master plan: [`ULTRAPLAN.md`](ULTRAPLAN.md)

---

## Phase A: Foundation — COMPLETE

Vault fully scaffolded and committed.

| What | Status | Files |
|------|--------|-------|
| Vault folder structure | Done | 16 directories in obsidian-nexus |
| Frontmatter templates (8) | Done | `obsidian-nexus/templates/*.md` |
| System files | Done | `obsidian-nexus/_system/{index,taxonomy,log}.md` |
| Vault health dashboard | Done | `obsidian-nexus/_system/vault-health.base` |
| Agent skills (6) | Done | `obsidian-nexus/.skills/vault-{ingest,query,lint,crosslink,distill,status}.md` |
| Agent bootstraps | Done | `obsidian-nexus/{CLAUDE,AGENTS,GEMINI}.md` |
| Git hook (LAN trigger) | Done | `obsidian-nexus/.githooks/post-push` |
| Ingest manifest | Done | `obsidian-nexus/_system/.manifest.json` |

---

## Phase B: Infrastructure — SCRIPTS READY, AWAITING DEPLOY

Deploy scripts prepared. OS **changed from Ubuntu Server → CachyOS** (2026-04-17)
after repeated Ubuntu installer failures on dual-boot layout. CachyOS is already
running on desktop with Limine bootloader. Scripts updated for firewalld/pacman.

| What | Status | Files |
|------|--------|-------|
| Docker Compose (Ollama+Qdrant+n8n) | Ready to deploy | [`deploy/docker-compose.yml`](deploy/docker-compose.yml) |
| Model pull + setup script | Ready to deploy | [`deploy/setup.sh`](deploy/setup.sh) |
| Qdrant collection init | Ready to deploy | [`deploy/init-qdrant.sh`](deploy/init-qdrant.sh) |
| Firewall (firewalld / ufw / iptables auto-detect) | Ready to deploy | [`deploy/firewall-setup.sh`](deploy/firewall-setup.sh) |
| LAN verification | Ready to run | [`deploy/verify.sh`](deploy/verify.sh) — run from ultrabook |
| n8n polling flow docs | Ready | [`deploy/n8n-polling-flow.md`](deploy/n8n-polling-flow.md) |

**Blocked on**: Human installing Docker + NVIDIA Container Toolkit on CachyOS desktop.
Desktop IP: `192.168.0.109`.

---

## Phase C: Knowledge Pipeline — SCRIPTS DONE, FLOWS PENDING

Scripts ready. n8n flows need desktop running to build.

| What | Status | Instructions |
|------|--------|-------------|
| n8n Router flow (tier classification) | Pending (needs desktop) | [`agents/router/system-prompt.md`](agents/router/system-prompt.md) |
| | | [`agents/router/test-cases.md`](agents/router/test-cases.md) |
| | | [`agents/router/examples.jsonl`](agents/router/examples.jsonl) |
| n8n Ingest flow (_inbox → atlas) | Pending (needs desktop) | [`agents/ingestor/system-prompt.md`](agents/ingestor/system-prompt.md) |
| | | [`agents/ingestor/merge-rules.md`](agents/ingestor/merge-rules.md) |
| | | [`agents/ingestor/frontmatter-spec.md`](agents/ingestor/frontmatter-spec.md) |
| n8n RAG query flow | Pending (needs desktop) | [`plans/phase-c-pipeline/plan.md`](plans/phase-c-pipeline/plan.md) |
| Delta re-indexing flow | Pending (needs desktop) | [`plans/phase-c-pipeline/plan.md`](plans/phase-c-pipeline/plan.md) |
| Embedding script | **Done** | [`scripts/embed.py`](scripts/embed.py) — batch Ollama → Qdrant with frontmatter payload |
| Delta index script | **Done** | [`scripts/delta-index.py`](scripts/delta-index.py) — git-diff selective re-embedding + manifest |
| Checklist | | [`plans/phase-c-pipeline/checklist.md`](plans/phase-c-pipeline/checklist.md) |

---

## Phase D: Feedback Loops — SCRIPTS DONE, AUTOMATION PENDING

Scripts ready. n8n cron flows and cross-linker need desktop running.

| What | Status | Instructions |
|------|--------|-------------|
| Cross-linker (weekly cron) | Pending (needs desktop) | [`agents/crosslinker/system-prompt.md`](agents/crosslinker/system-prompt.md) |
| | | [`agents/crosslinker/graph-analytics.md`](agents/crosslinker/graph-analytics.md) |
| Decay/lint scanner (monthly cron) | Pending (needs desktop) | [`agents/linter/system-prompt.md`](agents/linter/system-prompt.md) |
| | | [`agents/linter/report-template.md`](agents/linter/report-template.md) |
| Conversation distiller | Pending (needs desktop) | [`agents/distiller/system-prompt.md`](agents/distiller/system-prompt.md) |
| | | [`agents/distiller/quality-filters.md`](agents/distiller/quality-filters.md) |
| ChromaDB sync script | **Done** | [`scripts/sync-chromadb.py`](scripts/sync-chromadb.py) — Qdrant → ChromaDB with recent/workspace collections |
| Vault stats script | **Done** | [`scripts/vault-stats.py`](scripts/vault-stats.py) — CLI health metrics, zero deps, tested |
| Checklist | | [`plans/phase-d-feedback-loops/checklist.md`](plans/phase-d-feedback-loops/checklist.md) |

---

## Phase E: Refinement — NOT STARTED

Tuning and optimization. Requires Phases A-D stable.

| What | Status | Instructions |
|------|--------|-------------|
| Router prompt tuning | Pending | [`plans/phase-e-refinement/plan.md`](plans/phase-e-refinement/plan.md) |
| RAG retrieval tuning | Pending | [`plans/phase-e-refinement/plan.md`](plans/phase-e-refinement/plan.md) |
| Obsidian plugin config | Pending (human) | [`HUMAN-TODO.md`](HUMAN-TODO.md) |
| Checklist | | [`plans/phase-e-refinement/checklist.md`](plans/phase-e-refinement/checklist.md) |

---

## Documentation — COMPLETE

| What | Status | File |
|------|--------|------|
| System architecture (ASCII diagrams) | **Done** | [`docs/architecture.md`](docs/architecture.md) |
| Operational runbook (17-command cheat sheet) | **Done** | [`docs/runbook.md`](docs/runbook.md) |

---

## Config reference

| File | Purpose |
|------|---------|
| [`configs/.env.example`](configs/.env.example) | Environment variables template |
| [`configs/qdrant-config.yaml`](configs/qdrant-config.yaml) | Qdrant collection schemas |
| [`configs/ollama-models.txt`](configs/ollama-models.txt) | Models to pull per machine |
| [`obsidian-nexus/_system/taxonomy.md`](../obsidian-nexus/_system/taxonomy.md) | Frontmatter controlled vocabulary |
| [`obsidian-nexus/CLAUDE.md`](../obsidian-nexus/CLAUDE.md) | Claude agent bootstrap for vault ops |

---

## How to pick up work

1. Read `ULTRAPLAN.md` for full architecture context
2. Check this file for what's done vs pending
3. Read the phase plan: `plans/phase-{x}/plan.md`
4. Read the agent configs: `agents/{role}/system-prompt.md`
5. Execute, then check off items in `plans/phase-{x}/checklist.md`
6. Update this file when completing work
