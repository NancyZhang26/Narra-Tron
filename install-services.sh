#!/bin/bash
# Install and activate all Narra-Tron systemd services.
# Must be run as root: sudo ./install-services.sh
set -euo pipefail

if [[ $EUID -ne 0 ]]; then
  echo "ERROR: run this script as root (sudo ./install-services.sh)" >&2
  exit 1
fi

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SYSTEMD_SRC="$SCRIPT_DIR/systemd"
SYSTEMD_DST="/etc/systemd/system"

echo "=== Enabling nancy hotspot autoconnect ==="
nmcli con modify nancy connection.autoconnect yes
nmcli con modify nancy connection.autoconnect-priority 100
echo "    done."

echo "=== Installing systemd service files ==="
for svc in narratron-hotspot narratron-api narratron-camera; do
  cp "$SYSTEMD_SRC/$svc.service" "$SYSTEMD_DST/"
  echo "    installed $svc.service"
done

echo "=== Reloading systemd daemon ==="
systemctl daemon-reload

echo "=== Enabling services (auto-start on boot) ==="
systemctl enable narratron-hotspot.service narratron-api.service narratron-camera.service

echo "=== Starting services now ==="
systemctl start narratron-hotspot.service
systemctl start narratron-api.service
systemctl start narratron-camera.service

echo ""
echo "All done. Useful commands:"
echo "  sudo systemctl status narratron-hotspot narratron-api narratron-camera"
echo "  journalctl -fu narratron-api"
echo "  journalctl -fu narratron-camera"
echo "  sudo systemctl restart narratron-camera"
