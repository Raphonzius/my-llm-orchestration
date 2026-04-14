# n8n Polling Flow — Catch-all fallback

Complements the git hook (instant/LAN) by polling GitHub every 5 minutes.
Catches pushes from any source: phone clipper, Jarvis/Steam Deck, GitHub web edits.

## Flow: Vault Poll

```
Schedule Trigger (every 5 min)
  → Execute Command: cd /path/to/vault && git pull --ff-only origin main
  → IF: exit code 0 AND output contains "files changed"
    → Execute Command: git diff --name-only HEAD~1 HEAD
    → Filter: only files in _inbox/
    → For each new file:
      → Trigger Ingest subflow (same as webhook-triggered ingest)
  → ELSE: no changes, do nothing
```

## n8n nodes to create

1. **Schedule Trigger**
   - Interval: 5 minutes

2. **Execute Command** (git pull)
   - Command: `cd /home/<user>/obsidian-nexus && git pull --ff-only origin main 2>&1`
   - Working Directory: `/home/<user>/obsidian-nexus`

3. **IF** (has changes)
   - Condition: `{{ $json.stdout }}` contains `"files changed"`

4. **Execute Command** (diff)
   - Command: `cd /home/<user>/obsidian-nexus && git diff --name-only HEAD~1 HEAD`

5. **Split In Batches** → process each changed file

## Setup requirements

- Clone obsidian-nexus on desktop: `git clone https://github.com/<user>/obsidian-nexus.git`
- Configure git credentials on desktop for pull access
- n8n container needs access to the vault directory:
  Add to docker-compose.yml n8n service:
  ```yaml
  volumes:
    - n8n_data:/home/node/.n8n
    - /home/<user>/obsidian-nexus:/vault
  ```

## Deduplication

Both the git hook and polling may fire for the same push. The ingest flow should check
`_system/.manifest.json` (file paths + timestamps) to skip already-processed files.
This makes the system idempotent — safe to trigger twice.
