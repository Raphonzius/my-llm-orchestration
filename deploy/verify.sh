#!/bin/bash
# LAN verification — run from ULTRABOOK (Git Bash on Windows)
# Usage: bash verify.sh <desktop-ip>
# Example: bash verify.sh 192.168.1.100

DESKTOP="${1:-}"

if [ -z "$DESKTOP" ]; then
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
  printf "  %-10s %s ... " "$name" "$url"
  if curl -s -o /dev/null --connect-timeout 5 "$url" 2>/dev/null; then
    echo "OK"
    pass=$((pass + 1))
  else
    echo "FAIL"
    fail=$((fail + 1))
  fi
}

check "Ollama" "http://$DESKTOP:11434/api/tags"
check "Qdrant" "http://$DESKTOP:6333/collections"
check "n8n" "http://$DESKTOP:5678"

echo ""

# Ollama models
echo "--- Ollama models ---"
curl -s "http://$DESKTOP:11434/api/tags" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for m in data.get('models', []):
        print(f\"  {m['name']}\")
except: print('  (could not parse)')
" 2>/dev/null || echo "  (unreachable)"

echo ""

# Qdrant collections
echo "--- Qdrant collections ---"
curl -s "http://$DESKTOP:6333/collections" 2>/dev/null | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    for c in data.get('result', {}).get('collections', []):
        print(f\"  {c['name']}\")
except: print('  (could not parse)')
" 2>/dev/null || echo "  (unreachable)"

echo ""
echo "=== Results: $pass passed, $fail failed ==="
if [ $fail -eq 0 ]; then
  echo "All services accessible from ultrabook!"
else
  echo "Some services unreachable — check desktop firewall (sudo firewall-cmd --list-all)"
fi
