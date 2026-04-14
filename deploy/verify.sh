#!/bin/bash
# LAN verification — run from ULTRABOOK to test desktop services
# Usage: bash verify.sh <desktop-ip>
# Example: bash verify.sh 192.168.1.100

DESKTOP="${1:-192.168.1.XXX}"

if [ "$DESKTOP" = "192.168.1.XXX" ]; then
  echo "Usage: bash verify.sh <desktop-ip>"
  echo "Example: bash verify.sh 192.168.1.100"
  exit 1
fi

echo "=== LAN Verification: $DESKTOP ==="
echo ""

pass=0
fail=0

check() {
  local name=$1
  local url=$2
  local expect=$3
  printf "  %-10s %s ... " "$name" "$url"
  response=$(curl -s -o /dev/null -w "%{http_code}" --connect-timeout 5 "$url" 2>/dev/null)
  if [ "$response" = "$expect" ]; then
    echo "OK ($response)"
    pass=$((pass + 1))
  else
    echo "FAIL (got $response, expected $expect)"
    fail=$((fail + 1))
  fi
}

# Ollama
check "Ollama" "http://$DESKTOP:11434/api/tags" "200"

# Qdrant
check "Qdrant" "http://$DESKTOP:6333/collections" "200"

# n8n
check "n8n" "http://$DESKTOP:5678" "200"

# Gitea
check "Gitea" "http://$DESKTOP:3000" "200"

echo ""

# Detail checks
echo "--- Ollama models ---"
curl -s "http://$DESKTOP:11434/api/tags" 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for m in data.get('models', []):
    print(f\"  {m['name']}  ({m.get('size', 'unknown size')})\" if isinstance(m.get('size'), str) else f\"  {m['name']}\")
" 2>/dev/null || echo "  (could not parse)"

echo ""
echo "--- Qdrant collections ---"
curl -s "http://$DESKTOP:6333/collections" 2>/dev/null | python3 -c "
import sys, json
data = json.load(sys.stdin)
for c in data.get('result', {}).get('collections', []):
    print(f\"  {c['name']}\")
" 2>/dev/null || echo "  (could not parse)"

echo ""
echo "=== Results: $pass passed, $fail failed ==="
[ $fail -eq 0 ] && echo "All services accessible from ultrabook!" || echo "Some services unreachable — check desktop firewall."
