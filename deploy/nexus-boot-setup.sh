#!/bin/bash
# Install Nexus headless boot mode:
#   - systemd units (nexus.target, nexus-compose, nexus-gh-auth)
#   - /etc/nexus/gh-token for non-interactive gh auth
#   - Limine boot entry: boots headless Nexus instead of KDE
# Usage: sudo bash nexus-boot-setup.sh
set -e

DEPLOY_DIR="$(cd "$(dirname "$0")" && pwd)"
LIMINE_CONF="/boot/limine.conf"
NEXUS_CONF_DIR="/home/raphonzius/.config/nexus"
SYSTEMD_DIR="/etc/systemd/system"

if [ "$EUID" -ne 0 ]; then
  echo "Run with sudo: sudo bash nexus-boot-setup.sh"
  exit 1
fi

echo "=== Installing Nexus systemd units ==="
cp "$DEPLOY_DIR/systemd/nexus.target"            "$SYSTEMD_DIR/"
cp "$DEPLOY_DIR/systemd/nexus-compose.service"   "$SYSTEMD_DIR/"
cp "$DEPLOY_DIR/systemd/nexus-gh-auth.service"   "$SYSTEMD_DIR/"
systemctl daemon-reload
systemctl enable nexus-compose.service nexus-gh-auth.service
echo "Units installed and enabled."

echo ""
echo "=== Setting up GitHub token ==="
mkdir -p "$NEXUS_CONF_DIR"
if [ -f "$NEXUS_CONF_DIR/gh-token" ]; then
  echo "Token already exists at $NEXUS_CONF_DIR/gh-token — skipping."
  echo "To replace: sudo bash -c 'gh auth token > /etc/nexus/gh-token && chmod 600 /etc/nexus/gh-token'"
else
  # Try to extract from active gh session first
  GH_TOKEN=$(sudo -u raphonzius gh auth token 2>/dev/null || true)
  if [ -n "$GH_TOKEN" ]; then
    echo "Extracted token from active gh session."
  else
    echo "No active gh session found. Paste your GitHub personal access token"
    echo "(needs repo + read:org scopes), then press Enter:"
    read -r GH_TOKEN
  fi
  echo "$GH_TOKEN" > "$NEXUS_CONF_DIR/gh-token"
  chmod 600 "$NEXUS_CONF_DIR/gh-token"
  chown raphonzius:raphonzius "$NEXUS_CONF_DIR/gh-token"
  echo "Token saved to $NEXUS_CONF_DIR/gh-token (root-readable only)."
fi

echo ""
echo "=== Adding Nexus Limine boot entry ==="

# Extract kernel + initramfs paths from the existing main linux-cachyos entry
# (the top-level one, not a snapshot — identified by being under /+CachyOS at depth 2)
KERNEL_PATH=$(awk '/^\/\+CachyOS$/,0 { if (/^  \/\/linux-cachyos$/) found=1; if (found && /^  path:/) { sub(/^  path: /, ""); print; exit } }' "$LIMINE_CONF")
MODULE_PATH=$(awk '/^\/\+CachyOS$/,0 { if (/^  \/\/linux-cachyos$/) found=1; if (found && /^  module_path:/) { sub(/^  module_path: /, ""); print; exit } }' "$LIMINE_CONF")
CMDLINE_BASE="quiet nowatchdog rw rootflags=subvol=/@ root=UUID=f30151b5-7b29-4fb6-b667-5a2d15b27fc9"

if [ -z "$KERNEL_PATH" ] || [ -z "$MODULE_PATH" ]; then
  echo "ERROR: Could not extract kernel paths from $LIMINE_CONF"
  echo "Add the Nexus entry manually (see deploy/systemd/README below)."
  exit 1
fi

# Check if entry already exists
if grep -q "CachyOS Nexus" "$LIMINE_CONF"; then
  echo "Nexus Limine entry already present — skipping."
else
  # Insert the new entry right after the /+CachyOS block's closing line
  # (before /+Other systems and bootloaders)
  NEXUS_ENTRY="\n/+CachyOS Nexus (Headless)\n  //linux-cachyos\n  comment: Nexus headless server — no KDE, no SDDM\n  protocol: linux\n  module_path: $MODULE_PATH\n  path: $KERNEL_PATH\n  cmdline: $CMDLINE_BASE systemd.unit=nexus.target"

  # Insert before the Windows/EFI section
  sed -i "s|^/+Other systems and bootloaders|${NEXUS_ENTRY}\n\n/+Other systems and bootloaders|" "$LIMINE_CONF"
  echo "Limine entry added."
fi

echo ""
echo "=== Done ==="
echo "At next boot, select 'CachyOS Nexus (Headless)' in the Limine menu."
echo "KDE will NOT start. SSH in at: ssh raphonzius@$(ip route get 1 2>/dev/null | awk '{print $NF; exit}')"
echo "Services: Ollama :11434 | Qdrant :6333 | n8n :5678"
