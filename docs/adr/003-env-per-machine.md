# ADR-003 — Machine-specific .env files

**Status:** Accepted
**Date:** 2026-04-18

## Context

After ADR-002, ultrabook and desktop need different service URLs for the same obsidian-nexus vault code:

- Ultrabook reaches Ollama via tunnel: `http://localhost:21434`
- Desktop reaches its own Ollama directly: `http://localhost:11434`

The original `.env` + `.env.local` pattern (shared committed template, gitignored local override) meant every fresh clone required manual edits. .env contained no secrets — just URLs, ports, model names. So gitignoring it was doing nothing except creating setup friction.

## Decision

Commit two machine-specific files to the obsidian-nexus repo:

- `.env.ultrabook` — tunnel ports (21434, 26333, 25678)
- `.env.desktop` — direct localhost (11434, 6333, 5678)

On each machine, the relevant tool reads the matching file (or it's copied to `.env.local` at clone time). No generic `.env` template — both machines know which one they are.

## Consequences

**Good:**
- Fresh clone on either machine → one `cp` command and you're configured
- Both configs reviewable in git history — easier to spot drift
- No "which value should this placeholder have" confusion
- ChromaDB reference lives only in `.env.ultrabook` (desktop doesn't run it)

**Trade-offs accepted:**
- Two files to keep in sync when adding new service URLs (mitigated: small number of URLs, changes rare)
- Doesn't scale to N machines (mitigated: we have 2; if a third appears, re-evaluate)

## Alternatives considered

| Option | Why not |
|--------|---------|
| Single `.env` with both sets, toggled by `$MACHINE` var | Fragile; silently reads wrong values if env var unset |
| `.env.template` + manual `.env.local` | Original approach — creates friction every clone |
| Env vars injected by systemd / shell profile | Couples app config to system config; harder to audit |
| Config in code (`config.ts` with `if (hostname === ...)`) | Code changes for config changes; hostile to non-code tools (n8n, shell scripts) |

## Rule of thumb

> If the file contains no secrets, commit it. Gitignore is for secrets, not for "things that vary by machine."
