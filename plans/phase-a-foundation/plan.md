# Phase A: Foundation

**Goal**: Initialize the Obsidian vault with the complete folder structure, frontmatter templates, taxonomy, git repo, and multi-agent bootstrap files.

**Dependencies**: None — this is the first phase.
**Delegatable to**: Any agent with filesystem access.

---

## Tasks

### A1. Create vault folder structure

Create all directories as defined in ULTRAPLAN Section 2:

```
vault/
├── _system/
├── _inbox/{clips,voice,screenshots,imports}
├── atlas/{concepts,entities,patterns,guides}
├── sources/{articles,papers,books,conversations}
├── projects/
├── areas/{engineering,home-automation}
├── daily/
├── templates/
└── .skills/
```

### A2. Create frontmatter templates

Each template in `templates/` must contain the full frontmatter schema from ULTRAPLAN Section 3, with type-appropriate defaults.

Templates to create:
- `concept.md` — type: concept, domain: [], status: seed
- `entity.md` — type: entity, domain: [], status: seed
- `decision.md` — type: decision, domain: [], status: seed
- `source.md` — type: source, domain: [], status: seed
- `daily.md` — type: daily, status: growing
- `pattern.md` — type: pattern, domain: [], status: seed
- `guide.md` — type: guide, domain: [], status: seed
- `project.md` — type: project, status: seed

### A3. Create _system/ files

- **`_system/index.md`** — Master catalog with sections for each type. Initially empty with headers.
- **`_system/taxonomy.md`** — Controlled vocabulary:
  - Domains: engineering, polymath, professional, home-automation
  - Types: concept, entity, decision, pattern, guide, source, daily, project, area
  - Status: seed, growing, evergreen, archived
  - Provenance: human, extracted, synthesized, inferred
  - Confidence: high, medium, low
  - Initial tags per domain
- **`_system/log.md`** — Append-only operation log, initialized with creation entry.
- **`_system/vault-health.base`** — Obsidian Base dashboard from ULTRAPLAN Section 11.

### A4. Create agent bootstrap files

- **`CLAUDE.md`** — Vault schema, frontmatter spec, rules, skills pointer
- **`AGENTS.md`** — Generic agent bootstrap (Codex, LLaMA, other)
- **`GEMINI.md`** — Gemini-specific bootstrap
- **`.env`** — Template with VAULT_PATH, QDRANT_URL, CHROMADB_URL, OLLAMA_URL

### A5. Create .skills/ definitions

Canonical skill definitions (see ULTRAPLAN Section 10):
- `vault-ingest.md`
- `vault-query.md`
- `vault-lint.md`
- `vault-crosslink.md`
- `vault-distill.md`
- `vault-status.md`

### A6. Initialize git repo

```bash
cd vault/
git init
git add .
git commit -m "init: vault structure, templates, taxonomy, agent bootstrap"
git remote add origin <gitea-or-github-url>
git push -u origin main
```

---

## Completion criteria

- [ ] Vault opens in Obsidian with all folders visible
- [ ] Creating a note from any template produces correct frontmatter
- [ ] `_system/taxonomy.md` lists all allowed values
- [ ] `_system/vault-health.base` renders in Obsidian (may show empty tables)
- [ ] CLAUDE.md, AGENTS.md, GEMINI.md are present and consistent
- [ ] All 6 `.skills/` definitions are present
- [ ] Git repo initialized, remote configured, initial commit pushed
