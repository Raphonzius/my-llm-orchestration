#!/bin/bash
# Ubuntu Server 24.04 LTS — open firewall ports for LAN access
# Usage: sudo bash firewall-setup.sh
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Run with sudo: sudo bash firewall-setup.sh"
  exit 1
fi

echo "=== Opening UFW ports for LLM orchestration ==="
echo ""

# Enable ufw if not already
if ! ufw status | grep -q "Status: active"; then
  echo "Enabling UFW..."
  ufw --force enable
fi

# Allow SSH first (don't lock yourself out)
ufw allow OpenSSH comment "SSH access"

# Service ports
ufw allow 11434/tcp comment "Ollama LLM API"
ufw allow 6333/tcp comment "Qdrant REST API"
ufw allow 6334/tcp comment "Qdrant gRPC"
ufw allow 5678/tcp comment "n8n orchestration"

echo ""
echo "=== Current rules ==="
ufw status numbered

echo ""
echo "Done. Desktop IP: $(hostname -I | awk '{print $1}')"
