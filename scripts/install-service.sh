#!/usr/bin/env bash
# Install fnk0043-server as a systemd user service (starts on boot).
set -euo pipefail

REPO_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SERVICE_NAME="fnk0043"
UNIT_SRC="${REPO_DIR}/deploy/fnk0043.service"
UNIT_DEST="${HOME}/.config/systemd/user/${SERVICE_NAME}.service"
VENV_SERVER="${REPO_DIR}/.venv/bin/fnk0043-server"

if [[ ! -x "${VENV_SERVER}" ]]; then
  echo "error: ${VENV_SERVER} not found. Create the venv and run: pip install -e . --no-deps"
  exit 1
fi

mkdir -p "${HOME}/.config/systemd/user"

sed \
  -e "s|%i|${USER}|g" \
  -e "s|%h|${HOME}|g" \
  "${UNIT_SRC}" > "${UNIT_DEST}"

systemctl --user daemon-reload
systemctl --user enable "${SERVICE_NAME}.service"
systemctl --user restart "${SERVICE_NAME}.service"

# Allow user services to start at boot (without an active login session)
if command -v loginctl >/dev/null 2>&1; then
  sudo loginctl enable-linger "${USER}" 2>/dev/null || true
fi

echo ""
echo "Installed ${SERVICE_NAME} user service."
echo "  Status:  systemctl --user status ${SERVICE_NAME}"
echo "  Logs:    journalctl --user -u ${SERVICE_NAME} -f"
echo "  Stop:    systemctl --user stop ${SERVICE_NAME}"
echo "  Disable: systemctl --user disable ${SERVICE_NAME}"
echo ""
systemctl --user --no-pager status "${SERVICE_NAME}.service" || true
