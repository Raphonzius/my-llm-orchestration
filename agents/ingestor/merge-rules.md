# Merge Rules

## When to MERGE vs CREATE

### MERGE into existing note when:
- An atlas/ note already covers the same entity/concept (>70% topic overlap)
- The new information adds detail, updates, or contradicts existing content
- The entity name or aliases match an existing note title

### CREATE new note when:
- No existing note covers this topic
- The topic is distinct enough to warrant its own page
- The concept is a sub-topic that deserves dedicated treatment

## Merge behavior
1. Read existing note fully
2. Identify sections that overlap with new content
3. Append new information (don't reorganize existing structure)
4. If new info contradicts existing: add both with provenance markers
5. Update `modified:` date
6. Update `summary:` if meaning changed
7. Add new `related:` links
8. Keep `provenance: human` content untouched — only append/enrich
9. If merging LLM content into LLM content, keep the higher-confidence version

## Contradiction handling
When new information contradicts an existing claim:
```markdown
> [!note] Conflicting information
> **Previous**: [existing claim] (source: X, provenance: extracted)
> **New**: [new claim] (source: Y, provenance: extracted)
> **Status**: Needs human review
```
Set `confidence: low` on the note until resolved.
