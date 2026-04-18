# ADR-005 — Templater syntax standardization

**Status:** Accepted
**Date:** 2026-04-18

## Context

Vault templates were authored with two inconsistent date syntaxes:

- `{{date:YYYY-MM-DD}}` — Obsidian core template syntax (limited)
- `<% tp.date.now %>` — Templater syntax (but called without format argument — throws runtime error)

Neither worked reliably. `{{date}}` is processed only at initial template insert and has no format flexibility. `tp.date.now()` without arguments threw an exception complaining about missing reference format.

Templates affected: all 8 in `templates/` (concept, entity, decision, pattern, guide, source, project, daily).

## Decision

Standardize on Templater with an explicit format string everywhere:

```
<% tp.date.now("YYYY-MM-DD HH:mm") %>
```

For frontmatter `title` field in `daily.md` (where we want just the date):

```
<% tp.date.now("YYYY-MM-DD") %>
```

Rule: **always pass a format string to `tp.date.now`.** Never call it bare.

## Consequences

**Good:**
- One syntax across all templates — no confusion about which to use
- Templater evaluates on every insert, not just template creation — always fresh values
- Format string is explicit: reader sees exactly what the output will look like
- Works with all Templater features (user scripts, file creation hooks, etc.)

**Trade-offs accepted:**
- Requires Templater plugin to be installed + configured (folder: `templates/`) — acceptable, already a hard dependency
- Slightly more verbose than `{{date:YYYY-MM-DD}}` — negligible

## Alternatives considered

| Option | Why not |
|--------|---------|
| Obsidian core `{{date:FORMAT}}` | Only fires at template insertion; no access to `tp.file.*`, `tp.user.*`, etc. |
| Dataview inline DQL (`= dateformat(date(now), "yyyy-MM-dd")`) | Runtime-rendered, not written to file — frontmatter schemas need actual values |
| Shell-hooked dates via Obsidian plugins | Fragile, cross-platform issues on Windows |

## Standard formats used

| Purpose | Format | Example |
|---------|--------|---------|
| `title` in daily note | `YYYY-MM-DD` | 2026-04-18 |
| `created` / `modified` in all notes | `YYYY-MM-DD HH:mm` | 2026-04-18 04:47 |
| Future: log timestamps | `YYYY-MM-DDTHH:mm:ssZ` | ISO 8601 for machine parsing |
