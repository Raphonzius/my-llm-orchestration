# ADR-002 — Docker services bound to localhost + SSH tunnel access

**Status:** Accepted
**Date:** 2026-04-17

## Context

Desktop Docker stack (Ollama, Qdrant, n8n) originally exposed on LAN IP `192.168.0.112`. Even with UFW restricting traffic to ultrabook IP `192.168.0.106`, this meant:

- Any DHCP reshuffle (ultrabook gets a new IP) breaks access or opens services to whoever grabs `.106`
- ARP spoofing on the LAN can impersonate the ultrabook
- Services were listening on a publicly-addressable interface, trusting firewall alone
- Credentials (n8n login, Ollama API) traveled in plaintext over the local network

## Decision

Bind all Docker services to `127.0.0.1` on the desktop. Access only via SSH tunnel from the ultrabook using ed25519 key auth (password auth disabled entirely). Each service gets a distinct tunnel port on the ultrabook:

| Service | Desktop bind | Ultrabook port (tunnel) |
|---------|-------------|------------------------|
| Ollama | `127.0.0.1:11434` | `localhost:21434` |
| Qdrant REST | `127.0.0.1:6333` | `localhost:26333` |
| Qdrant gRPC | `127.0.0.1:6334` | `localhost:26334` |
| n8n | `127.0.0.1:5678` | `localhost:25678` |

LocalForward rules live in `~/.ssh/config` under the `nexus` Host alias. Active tunnel = access. No tunnel = no access.

## Consequences

**Good:**
- Services invisible to LAN — no scanning, no direct TCP contact possible
- All traffic encrypted end-to-end (SSH transport)
- Auth is single choke point: ed25519 private key on ultrabook
- Service ports on ultrabook use 2xxxx prefix (21434, 26333) so they don't conflict with local services using the standard port (11434, 6333)
- Firewall rules simplified — only port 22 from ultrabook IP

**Trade-offs accepted:**
- Tunnel must be running for anything to work (mitigated by ADR-004: autossh + Windows Startup)
- `.env` config differs between ultrabook and desktop (see ADR-003)
- Slightly more latency than raw TCP on LAN (negligible for our workloads)

## Alternatives considered

| Option | Why not |
|--------|---------|
| LAN binding + UFW restricting by IP | DHCP/ARP fragility; plaintext credentials on LAN |
| WireGuard mesh | Overkill for 2 machines; SSH is already there and battle-tested |
| Tailscale | External dependency; SSH suffices for point-to-point |
| mTLS on each service | N different cert setups (Ollama, Qdrant, n8n); SSH unifies auth |
