#!/bin/bash
# CachyOS (Arch-based) — open firewall ports for LAN access
# Usage: sudo bash firewall-setup.sh
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Run with sudo: sudo bash firewall-setup.sh"
  exit 1
fi

echo "=== Opening firewall ports for LLM orchestration ==="
echo ""

# Detect which firewall is active
if command -v firewall-cmd >/dev/null 2>&1 && systemctl is-active --quiet firewalld; then
  FIREWALL="firewalld"
elif command -v ufw >/dev/null 2>&1 && ufw status | grep -q "Status: active"; then
  FIREWALL="ufw"
elif command -v iptables >/dev/null 2>&1; then
  FIREWALL="iptables"
else
  echo "No known firewall detected. Install firewalld: sudo pacman -S firewalld"
  exit 1
fi

echo "Detected firewall: $FIREWALL"
echo ""

case "$FIREWALL" in
  firewalld)
    # Ensure firewalld is enabled and running
    systemctl enable --now firewalld

    # Service ports
    firewall-cmd --permanent --add-service=ssh
    firewall-cmd --permanent --add-port=11434/tcp  # Ollama LLM API
    firewall-cmd --permanent --add-port=6333/tcp   # Qdrant REST API
    firewall-cmd --permanent --add-port=6334/tcp   # Qdrant gRPC
    firewall-cmd --permanent --add-port=5678/tcp   # n8n orchestration

    firewall-cmd --reload

    echo ""
    echo "=== Active rules ==="
    firewall-cmd --list-all
    ;;

  ufw)
    ufw allow OpenSSH comment "SSH access"
    ufw allow 11434/tcp comment "Ollama LLM API"
    ufw allow 6333/tcp comment "Qdrant REST API"
    ufw allow 6334/tcp comment "Qdrant gRPC"
    ufw allow 5678/tcp comment "n8n orchestration"

    echo ""
    echo "=== Current rules ==="
    ufw status numbered
    ;;

  iptables)
    iptables -A INPUT -p tcp --dport 22 -j ACCEPT
    iptables -A INPUT -p tcp --dport 11434 -j ACCEPT
    iptables -A INPUT -p tcp --dport 6333 -j ACCEPT
    iptables -A INPUT -p tcp --dport 6334 -j ACCEPT
    iptables -A INPUT -p tcp --dport 5678 -j ACCEPT

    # Persist rules (Arch)
    if command -v iptables-save >/dev/null 2>&1; then
      iptables-save > /etc/iptables/iptables.rules
      systemctl enable --now iptables
    fi

    echo ""
    echo "=== Current rules ==="
    iptables -L INPUT -n --line-numbers
    ;;
esac

echo ""
echo "Done. Desktop IP: $(hostname -I | awk '{print $1}')"
