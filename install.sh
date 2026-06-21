#!/usr/bin/env bash
#
# Installer for the telegram-assistant bot. Run as root INSIDE a Debian/Ubuntu LXC
# (or any Debian-based host). Idempotent: safe to re-run to update.
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyth3r/telegram-assistant/main/install.sh)"
#
# Secrets: prompts for TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID, or reads them from the
# environment if already set (for non-interactive installs). An existing .env is never
# overwritten.

set -euo pipefail

APP_USER="${APP_USER:-telegram}"
APP_DIR="${APP_DIR:-/opt/telegram-assistant}"
REPO_URL="${REPO_URL:-https://github.com/skyth3r/telegram-assistant.git}"
BRANCH="${BRANCH:-main}"
UV_BIN="/usr/local/bin/uv"
SERVICE="telegram-assistant"

msg()  { echo -e "\033[1;34m[*]\033[0m $*"; }
ok()   { echo -e "\033[1;32m[✓]\033[0m $*"; }
die()  { echo -e "\033[1;31m[✗]\033[0m $*" >&2; exit 1; }

[ "$(id -u)" -eq 0 ] || die "Run this script as root."

# Run a command as the service user with HOME pointing at the app dir (so uv's cache
# and venv land in a writable, correctly-owned location).
as_app() { runuser -u "$APP_USER" -- env HOME="$APP_DIR" "$@"; }

msg "Installing system packages"
export DEBIAN_FRONTEND=noninteractive
apt-get update -qq
apt-get install -y -qq git curl ca-certificates >/dev/null
ok "Packages ready"

if ! id -u "$APP_USER" >/dev/null 2>&1; then
    msg "Creating service user '$APP_USER'"
    # No --create-home: the repo clone creates and populates the directory.
    useradd --system --home-dir "$APP_DIR" --shell /usr/sbin/nologin "$APP_USER"
    ok "User created"
fi

if [ -d "$APP_DIR/.git" ]; then
    msg "Updating existing checkout in $APP_DIR"
    git -C "$APP_DIR" fetch --quiet origin "$BRANCH"
    git -C "$APP_DIR" checkout --quiet "$BRANCH"
    git -C "$APP_DIR" reset --hard --quiet "origin/$BRANCH"
else
    msg "Cloning $REPO_URL into $APP_DIR"
    git clone --quiet --branch "$BRANCH" "$REPO_URL" "$APP_DIR"
fi
chown -R "$APP_USER:$APP_USER" "$APP_DIR"
ok "Code in place"

if [ ! -x "$UV_BIN" ]; then
    msg "Installing uv to /usr/local/bin"
    curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh >/dev/null
    ok "uv installed"
fi

msg "Installing dependencies (uv sync --frozen)"
( cd "$APP_DIR" && as_app "$UV_BIN" sync --frozen --no-dev >/dev/null )
ok "Dependencies installed"

# --- Environment file -------------------------------------------------------
if [ -f "$APP_DIR/.env" ]; then
    ok "Existing .env left untouched"
else
    msg "Configuring environment"
    : "${TELEGRAM_BOT_TOKEN:=}"
    : "${TELEGRAM_CHAT_ID:=}"

    if [ -z "$TELEGRAM_BOT_TOKEN" ]; then
        [ -t 0 ] || die "TELEGRAM_BOT_TOKEN not set and no terminal to prompt on."
        read -rsp "Telegram bot token: " TELEGRAM_BOT_TOKEN; echo
    fi
    if [ -z "$TELEGRAM_CHAT_ID" ]; then
        [ -t 0 ] || die "TELEGRAM_CHAT_ID not set and no terminal to prompt on."
        read -rp  "Your chat id: " TELEGRAM_CHAT_ID
    fi
    [ -n "$TELEGRAM_BOT_TOKEN" ] && [ -n "$TELEGRAM_CHAT_ID" ] || die "Token and chat id are required."

    umask 077
    cat > "$APP_DIR/.env" <<EOF
TELEGRAM_BOT_TOKEN=$TELEGRAM_BOT_TOKEN
TELEGRAM_CHAT_ID=$TELEGRAM_CHAT_ID
# Optional overrides (see .env.example):
# SUMMARY_TIME=07:00
# SUMMARY_TZ=Europe/London
# UPCOMING_DAYS=14
# ALLOWED_CHAT_IDS=
EOF
    chown "$APP_USER:$APP_USER" "$APP_DIR/.env"
    chmod 600 "$APP_DIR/.env"
    ok ".env written (chmod 600)"
fi

msg "Installing systemd service"
install -m 644 "$APP_DIR/deploy/$SERVICE.service" "/etc/systemd/system/$SERVICE.service"
systemctl daemon-reload
systemctl enable --quiet "$SERVICE"
systemctl restart "$SERVICE"
ok "Service enabled and (re)started"

msg "Installing update command"
install -m 755 "$APP_DIR/update.sh" /usr/local/bin/update
ok "update command installed — type 'update' to update the bot"

echo
ok "Done. Useful commands:"
echo "    update                          — pull latest code and restart"
echo "    systemctl status $SERVICE"
echo "    journalctl -u $SERVICE -f"
echo "    edit secrets: nano $APP_DIR/.env && systemctl restart $SERVICE"
