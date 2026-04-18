# Architecture Decision Records (ADRs)

Non-trivial decisions made during the build. Each ADR captures **context**, **decision**, **consequences**, and **alternatives considered**.

## Index

| # | Title | Date | Status |
|---|-------|------|--------|
| 001 | [CachyOS instead of Ubuntu Server](001-cachyos-over-ubuntu.md) | 2026-04-15 | Accepted |
| 002 | [Docker services bound to localhost + SSH tunnel access](002-ssh-tunnel-over-lan.md) | 2026-04-17 | Accepted |
| 003 | [Machine-specific .env files](003-env-per-machine.md) | 2026-04-18 | Accepted |
| 004 | [Auto-reconnecting SSH tunnel via Startup folder](004-autossh-via-startup-vbs.md) | 2026-04-18 | Accepted |
| 005 | [Templater syntax standardization](005-templater-syntax.md) | 2026-04-18 | Accepted |

## Referenced code snippets (non-sensitive)

Non-sensitive code excerpts that illustrate decisions live in `configs/`:

| File | Referenced by |
|------|---------------|
| `configs/start_tunnel.sh` | ADR-004 |
| `configs/ssh-config.example` | ADR-002, ADR-004 |
| `configs/nexus-tunnel.vbs.example` | ADR-004 |
| `configs/post-push.example` | ADR-002 (webhook trigger) |
| `configs/.env.example` | ADR-003 |

## Format

Each ADR follows [Michael Nygard's template](https://cognitect.com/blog/2011/11/15/documenting-architecture-decisions):

```
# ADR-NNN — Title

**Status:** Proposed | Accepted | Superseded | Deprecated
**Date:** YYYY-MM-DD

## Context
What problem? What constraints?

## Decision
What did we choose? What ruled alternatives out?

## Consequences
What becomes easier? Harder? What tradeoffs accepted?

## Alternatives considered
What else was on the table and why not?
```
