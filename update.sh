#!/usr/bin/env bash
#
# Update the telegram-assistant bot in-place. Run as root inside the LXC.
# Installed to /usr/local/bin/update by install.sh so you can just type: update

set -euo pipefail

APP_USER="${APP_USER:-telegram}"
APP_DIR="${APP_DIR:-/opt/telegram-assistant}"
BRANCH="${BRANCH:-main}"
UV_BIN="/usr/local/bin/uv"
SERVICE="telegram-assistant"

msg()  { echo -e "\033[1;34m[*]\033[0m $*"; }
ok()   { echo -e "\033[1;32m[✓]\033[0m $*"; }
die()  { echo -e "\033[1;31m[✗]\033[0m $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run this script as root."
[ -d "$APP_DIR/.git" ] || die "$APP_DIR is not a git checkout. Run install.sh first."

as_app() { runuser -u "$APP_USER" -- env HOME="$APP_DIR" "$@"; }

msg "Updating system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get upgrade -y -qq >/dev/null
ok "System packages up to date"

msg "Pulling latest code (branch: $BRANCH)"
git -C "$APP_DIR" fetch --quiet origin "$BRANCH"
git -C "$APP_DIR" checkout --quiet "$BRANCH"
git -C "$APP_DIR" reset --hard --quiet "origin/$BRANCH"
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
ok "Code updated to $(git -C "$APP_DIR" rev-parse --short HEAD)"

msg "Updating systemd service file"
install -m 644 "$APP_DIR/deploy/$SERVICE.service" "/etc/systemd/system/$SERVICE.service"
systemctl daemon-reload
ok "Service file reloaded"

msg "Syncing dependencies"
( cd "$APP_DIR" && as_app "$UV_BIN" sync --frozen --no-dev >/dev/null )
ok "Dependencies synced"

msg "Installing update command"
install -m 755 "$APP_DIR/update.sh" /usr/local/bin/update
ok "update command refreshed"

systemctl restart "$SERVICE"
ok "Service restarted"
echo
systemctl status "$SERVICE" --no-pager
