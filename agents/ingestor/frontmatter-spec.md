# Frontmatter Specification (Canonical Reference)

This is the single source of truth for frontmatter fields. All agents must produce frontmatter conforming to this spec.

## Required fields

| Field | Type | Allowed values |
|-------|------|---------------|
| `title` | string | Human-readable title |
| `type` | enum | concept, entity, decision, pattern, guide, source, daily, project, area |
| `status` | enum | seed, growing, evergreen, archived |
| `domain` | list[enum] | engineering, polymath, professional, home-automation |
| `provenance` | enum | human, extracted, synthesized, inferred |
| `confidence` | enum | high, medium, low |
| `created` | date | YYYY-MM-DD |
| `modified` | date | YYYY-MM-DD |
| `summary` | string | 1-2 sentences, used for tiered retrieval |

## Optional fields

| Field | Type | Purpose |
|-------|------|---------|
| `aliases` | list[string] | Alternative names for wikilink resolution |
| `tags` | list[string] | From taxonomy.md preferred, freeform allowed |
| `source` | string | URL or reference to origin |
| `related` | list[string] | Wikilinks: `"[[Note Title]]"` |

## Rules
- `modified` must be updated on every edit
- `provenance` reflects who wrote THIS version of the content
- `confidence` reflects reliability of the information, not the quality of writing
- `summary` is what the LLM reads FIRST to decide if the full note is relevant
- Lists in YAML use bracket syntax: `[item1, item2]` or block syntax with `-`
