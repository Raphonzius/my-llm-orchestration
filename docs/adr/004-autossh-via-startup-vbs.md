# ADR-004 — Auto-reconnecting SSH tunnel via Windows Startup folder

**Status:** Accepted
**Date:** 2026-04-18

## Context

ADR-002 made every vault operation depend on an active SSH tunnel from ultrabook to desktop. If the tunnel dies (laptop sleep, network drop, desktop reboot), the vault stops working until Rafael manually reopens it — including Obsidian Git auto-push, which would silently fail.

Need:
1. Tunnel starts automatically on user logon
2. Tunnel auto-reconnects when network blips
3. No visible console window (ultrabook is primary daily driver)
4. No elevated permissions required

## Decision

Three-file setup:

1. **`~/.ssh/config`** — defines the `nexus` Host alias with all LocalForward rules and keep-alive settings. One canonical source of truth.
2. **`~/.ssh/start_tunnel.sh`** — bash self-healing loop: kill stale processes → `ssh -N -T nexus` → sleep 5 on exit → retry forever. Uses config-driven SSH so no credentials in the script.
3. **`%APPDATA%\Microsoft\Windows\Start Menu\Programs\Startup\nexus-tunnel.vbs`** — VBScript wrapper that invokes Git Bash to run `start_tunnel.sh` with `WindowStyle = 0` (hidden). Placed in the Startup folder so Windows auto-runs it at logon.

No Windows Task Scheduler. No services. No autossh package dependency — plain bash retry loop is sufficient.

## Consequences

**Good:**
- User logs in → tunnel is up within seconds, no interaction needed
- Tunnel survives network drops, laptop sleep/wake, brief SSH timeouts
- No console window flashing or lingering in taskbar
- All three files are local files the user can edit — no admin/registry hacks
- Script is ~15 lines — easy to debug, easy to audit

**Trade-offs accepted:**
- Requires Git Bash installed (acceptable: already a dev prerequisite)
- Startup folder scripts run per-user, not per-machine (fine: single-user laptop)
- 5-second reconnect delay means brief unavailability after drops (negligible for vault sync cadence)

## Alternatives considered

| Option | Why not |
|--------|---------|
| autossh via Scoop | Extra dependency; bash retry loop does the same job in 15 lines |
| Windows Task Scheduler "At logon" | More complex XML config, harder to inspect, historically flaky with UAC |
| Windows Service (nssm wrapping autossh) | Requires admin rights; overkill for per-user tunnel |
| Manual tunnel via MobaXterm session | Works but requires user to click; defeats "automatic" requirement |
| WSL + systemd user unit | Adds WSL dependency for one bash script |

## Key snippet — self-healing loop

```bash
#!/bin/bash
HOST="nexus"
export HOME="/c/Users/rafae"

# Cleanup old sessions
pgrep -f "ssh.*$HOST" | xargs -r kill 2>/dev/null

# Self-healing loop
while true; do
    ssh -N -T "$HOST"   # config-driven, no credentials inline
    sleep 5             # breathe before retry
done
```

See `configs/start_tunnel.sh` for the committed version.
