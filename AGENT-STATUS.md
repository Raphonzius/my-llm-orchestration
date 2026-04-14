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

Deploy scripts prepared. Human must install Ubuntu + Docker on desktop, then run them.

| What | Status | Files |
|------|--------|-------|
| Docker Compose (Ollama+Qdrant+n8n) | Ready to deploy | [`deploy/docker-compose.yml`](deploy/docker-compose.yml) |
| Model pull + setup script | Ready to deploy | [`deploy/setup.sh`](deploy/setup.sh) |
| Qdrant collection init | Ready to deploy | [`deploy/init-qdrant.sh`](deploy/init-qdrant.sh) |
| Ubuntu firewall (ufw) | Ready to deploy | [`deploy/firewall-setup.sh`](deploy/firewall-setup.sh) |
| LAN verification | Ready to run | [`deploy/verify.sh`](deploy/verify.sh) — run from ultrabook |
| n8n polling flow docs | Ready | [`deploy/n8n-polling-flow.md`](deploy/n8n-polling-flow.md) |

**Blocked on**: Human installing Ubuntu Server + Docker + NVIDIA toolkit on desktop.

---

## Phase C: Knowledge Pipeline — NOT STARTED

Build the n8n automation flows. Can start once Phase B services are running.

| What | Status | Instructions |
|------|--------|-------------|
| n8n Router flow (tier classification) | Pending | [`agents/router/system-prompt.md`](agents/router/system-prompt.md) |
| | | [`agents/router/test-cases.md`](agents/router/test-cases.md) |
| | | [`agents/router/examples.jsonl`](agents/router/examples.jsonl) |
| n8n Ingest flow (_inbox → atlas) | Pending | [`agents/ingestor/system-prompt.md`](agents/ingestor/system-prompt.md) |
| | | [`agents/ingestor/merge-rules.md`](agents/ingestor/merge-rules.md) |
| | | [`agents/ingestor/frontmatter-spec.md`](agents/ingestor/frontmatter-spec.md) |
| n8n RAG query flow | Pending | [`plans/phase-c-pipeline/plan.md`](plans/phase-c-pipeline/plan.md) |
| Delta re-indexing flow | Pending | [`plans/phase-c-pipeline/plan.md`](plans/phase-c-pipeline/plan.md) |
| Embedding script | Pending | `scripts/embed.py` (not yet created) |
| Delta index script | Pending | `scripts/delta-index.py` (not yet created) |
| Checklist | | [`plans/phase-c-pipeline/checklist.md`](plans/phase-c-pipeline/checklist.md) |

---

## Phase D: Feedback Loops — NOT STARTED

Self-improving automation. Can start once Phase C ingest flow works.

| What | Status | Instructions |
|------|--------|-------------|
| Cross-linker (weekly cron) | Pending | [`agents/crosslinker/system-prompt.md`](agents/crosslinker/system-prompt.md) |
| | | [`agents/crosslinker/graph-analytics.md`](agents/crosslinker/graph-analytics.md) |
| Decay/lint scanner (monthly cron) | Pending | [`agents/linter/system-prompt.md`](agents/linter/system-prompt.md) |
| | | [`agents/linter/report-template.md`](agents/linter/report-template.md) |
| Conversation distiller | Pending | [`agents/distiller/system-prompt.md`](agents/distiller/system-prompt.md) |
| | | [`agents/distiller/quality-filters.md`](agents/distiller/quality-filters.md) |
| ChromaDB sync script | Pending | `scripts/sync-chromadb.py` (not yet created) |
| Vault stats script | Pending | `scripts/vault-stats.py` (not yet created) |
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
