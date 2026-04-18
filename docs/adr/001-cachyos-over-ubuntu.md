# ADR-001 — CachyOS instead of Ubuntu Server

**Status:** Accepted
**Date:** 2026-04-15

## Context

Desktop hardware: Ryzen 5 5600X + RTX 3050 8GB. Original plan called for dual-booting Ubuntu Server next to the existing CachyOS install to serve as the Nexus headless Docker host. Ubuntu Server is the conventional choice for long-running home servers.

Existing CachyOS install was already working, with up-to-date NVIDIA drivers (595.58.03, CUDA 13.2), Limine bootloader, and familiar pacman tooling.

## Decision

Use the existing CachyOS install as the Nexus host. No dual-boot. Run headless via a dedicated Limine boot entry (`CachyOS Nexus (Headless)`) that starts the Docker stack and skips KDE/SDDM.

## Consequences

**Good:**
- Saved hours of OS installation, driver setup, partition management
- Docker is OS-agnostic — stack identical on any distro
- CachyOS has better hardware optimization for Ryzen + RTX GPUs
- Arch rolling-release keeps NVIDIA Container Toolkit current
- Bootloader entry makes "server mode" vs "desktop mode" a one-click choice

**Trade-offs accepted:**
- Rolling release means occasional breakage windows (mitigated: only update when desktop is free)
- Arch community is smaller than Ubuntu for server-specific tutorials
- systemd units for Nexus services written by us (no pre-packaged ubuntu equivalents)

## Alternatives considered

| Option | Why not |
|--------|---------|
| Ubuntu Server (dual-boot) | 4+ hours setup, driver mismatches on RTX 3050, redundant with working CachyOS |
| Proxmox + VMs | Overkill for single-user lab, GPU passthrough complexity |
| Bare-metal Docker on CachyOS desktop KDE | No resource isolation when using desktop, manual start each reboot |
