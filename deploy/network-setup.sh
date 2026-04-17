#!/bin/bash
# Set static IP on desktop and lock Nexus ports to ultrabook only.
# Usage: sudo bash network-setup.sh
set -e

STATIC_IP="192.168.0.112"
GATEWAY="192.168.0.1"
DNS="1.1.1.1,8.8.8.8"
ULTRABOOK_IP="192.168.0.106"
IFACE="enp8s0"

if [ "$EUID" -ne 0 ]; then
  echo "Run with sudo: sudo bash network-setup.sh"
  exit 1
fi

echo "=== Setting static IP $STATIC_IP on $IFACE ==="
CONN=$(nmcli -g NAME,DEVICE con show --active | grep "$IFACE" | cut -d: -f1)
if [ -z "$CONN" ]; then
  echo "ERROR: No active connection found on $IFACE"
  exit 1
fi
echo "Connection: $CONN"
nmcli con mod "$CONN" \
  ipv4.method manual \
  ipv4.addresses "$STATIC_IP/24" \
  ipv4.gateway "$GATEWAY" \
  ipv4.dns "$DNS"
nmcli con up "$CONN"
echo "Static IP set."

echo ""
echo "=== Locking Nexus ports to ultrabook ($ULTRABOOK_IP) only ==="

# Remove existing broad rules for Nexus ports
for PORT in 11434 6333 6334 5678; do
  ufw delete allow ${PORT}/tcp 2>/dev/null || true
done

# Allow only from ultrabook
ufw allow from "$ULTRABOOK_IP" to any port 11434 proto tcp comment "Ollama — ultrabook only"
ufw allow from "$ULTRABOOK_IP" to any port 6333  proto tcp comment "Qdrant REST — ultrabook only"
ufw allow from "$ULTRABOOK_IP" to any port 6334  proto tcp comment "Qdrant gRPC — ultrabook only"
ufw allow from "$ULTRABOOK_IP" to any port 5678  proto tcp comment "n8n — ultrabook only"

ufw reload

echo ""
echo "=== Current rules ==="
ufw status numbered

echo ""
echo "Done. Desktop is now $STATIC_IP, ports locked to $ULTRABOOK_IP."
