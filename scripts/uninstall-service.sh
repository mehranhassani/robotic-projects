#!/usr/bin/env bash
# Remove the fnk0043 systemd user service.
set -euo pipefail

SERVICE_NAME="fnk0043"
UNIT_DEST="${HOME}/.config/systemd/user/${SERVICE_NAME}.service"

systemctl --user stop "${SERVICE_NAME}.service" 2>/dev/null || true
systemctl --user disable "${SERVICE_NAME}.service" 2>/dev/null || true
rm -f "${UNIT_DEST}"
systemctl --user daemon-reload

echo "Removed ${SERVICE_NAME} user service."
