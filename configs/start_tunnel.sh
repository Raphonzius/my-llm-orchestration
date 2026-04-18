#!/bin/bash
# SSH Tunnel Auto-Reconnect Loop
# Maintains persistent SSH tunnel with auto-recovery on network drops

# --- CONFIG ---
HOST="nexus"
export HOME="/c/Users/rafae"

# 1. Cleanup old sessions
pgrep -f "ssh.*$HOST" | xargs -r kill 2>/dev/null

# 2. Self-Healing Loop
while true; do
    # Everything is now pulled from ~/.ssh/config automatically
    ssh -N -T "$HOST"

    # Wait before reconnecting to be kind to the network/CPU
    sleep 5
done
