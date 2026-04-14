# Phase D: Feedback Loops — Verification Checklist

- [ ] Cross-linker: finds unlinked entity mentions
- [ ] Cross-linker: adds [[wikilinks]] correctly
- [ ] Cross-linker: updates related: fields bidirectionally
- [ ] Graph analytics: identifies hub pages
- [ ] Graph analytics: identifies orphan pages
- [ ] Graph analytics: identifies bridge pages
- [ ] Graph analytics: writes _system/insights.md
- [ ] Decay scanner: flags old seeds (>30 days)
- [ ] Decay scanner: flags stale evergreens (>90 days)
- [ ] Decay scanner: flags low-trust inferred content
- [ ] Decay scanner: writes lint report to _system/
- [ ] Distiller: extracts decisions from conversation transcript
- [ ] Distiller: extracts patterns from conversation transcript
- [ ] Distiller: filters noise correctly (skips debugging chatter)
- [ ] Distiller: writes to sources/conversations/ with cross-links
- [ ] ChromaDB sync: ultrabook "recent" collection updated daily
- [ ] ChromaDB sync: trims to last 30 days
- [ ] All cron schedules configured in n8n
