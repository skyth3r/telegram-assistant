#!/usr/bin/env bash
#
# Host-side creator for the telegram-assistant bot. Run as root ON THE PROXMOX HOST.
# Creates a Debian LXC, then runs install.sh inside it (which prompts for your bot
# token and chat id and sets up the systemd service).
#
#   bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyth3r/telegram-assistant/main/proxmox-create.sh)"
#
# This script does NOT handle secrets; install.sh prompts for them inside the container.

set -euo pipefail

REPO_RAW="${REPO_RAW:-https://raw.githubusercontent.com/skyth3r/telegram-assistant}"
BRANCH="${BRANCH:-main}"
TEMPLATE_STORAGE="${TEMPLATE_STORAGE:-local}"
INSTALL_URL="$REPO_RAW/$BRANCH/install.sh"

msg()  { echo -e "\033[1;34m[*]\033[0m $*"; }
ok()   { echo -e "\033[1;32m[✓]\033[0m $*"; }
die()  { echo -e "\033[1;31m[✗]\033[0m $*" >&2; exit 1; }

# Prompt with a default; echoes the chosen value.
ask() {
    local prompt="$1" default="$2" reply
    read -rp "$prompt [$default]: " reply </dev/tty
    echo "${reply:-$default}"
}

# --- Preflight --------------------------------------------------------------
[ "$(id -u)" -eq 0 ] || die "Run this script as root on the Proxmox host."
command -v pct >/dev/null 2>&1 || die "'pct' not found — this must run on a Proxmox VE host."
command -v pveam >/dev/null 2>&1 || die "'pveam' not found — this must run on a Proxmox VE host."

# --- Settings ---------------------------------------------------------------
DEFAULT_CTID="$(pvesh get /cluster/nextid 2>/dev/null || echo 100)"
CTID="$(ask 'Container ID' "$DEFAULT_CTID")"
pct status "$CTID" >/dev/null 2>&1 && die "Container $CTID already exists."

HOSTNAME="$(ask 'Hostname' 'telegram-assistant')"
CORES="$(ask 'CPU cores' '1')"
MEMORY="$(ask 'Memory (MB)' '512')"
DISK="$(ask 'Disk (GB)' '4')"
BRIDGE="$(ask 'Network bridge' 'vmbr0')"

# Storage pool: list pools that can hold a container rootfs, default to the first.
msg "Detecting storage pools for container rootfs"
mapfile -t POOLS < <(pvesm status -content rootdir 2>/dev/null | awk 'NR>1 {print $1}')
[ "${#POOLS[@]}" -gt 0 ] || die "No storage with content type 'rootdir' found."
echo "    Available: ${POOLS[*]}"
STORAGE="$(ask 'Storage pool' "${POOLS[0]}")"

# --- Template ---------------------------------------------------------------
msg "Resolving Debian 12 template"
pveam update >/dev/null 2>&1 || true
TEMPLATE="$(pveam available --section system 2>/dev/null | awk '/debian-12-standard/ {print $2}' | sort -V | tail -n1)"
[ -n "$TEMPLATE" ] || die "Could not find a debian-12-standard template via pveam."

if ! pveam list "$TEMPLATE_STORAGE" 2>/dev/null | grep -q "$TEMPLATE"; then
    msg "Downloading template $TEMPLATE to $TEMPLATE_STORAGE"
    pveam download "$TEMPLATE_STORAGE" "$TEMPLATE" >/dev/null
fi
ok "Template ready: $TEMPLATE"

# --- Create + start ---------------------------------------------------------
msg "Creating container $CTID ($HOSTNAME)"
pct create "$CTID" "$TEMPLATE_STORAGE:vztmpl/$TEMPLATE" \
    --hostname "$HOSTNAME" \
    --cores "$CORES" \
    --memory "$MEMORY" \
    --rootfs "$STORAGE:$DISK" \
    --net0 "name=eth0,bridge=$BRIDGE,ip=dhcp" \
    --unprivileged 1 \
    --features nesting=0 \
    --onboot 1 \
    --start 1 >/dev/null
ok "Container created and started"

# Wait for network inside the container.
msg "Waiting for container network"
for _ in $(seq 1 30); do
    if pct exec "$CTID" -- getent hosts raw.githubusercontent.com >/dev/null 2>&1; then
        ok "Network is up"
        break
    fi
    sleep 2
done

# --- Stage install.sh inside the container ----------------------------------
# Note: we don't run install.sh over `pct exec` because it has no TTY, so its
# secret prompts can't read input. Instead we stage it and drop you into an
# interactive shell (`pct enter`), where the prompts work.
msg "Bootstrapping curl inside the container"
pct exec "$CTID" -- bash -c "export DEBIAN_FRONTEND=noninteractive; apt-get update -qq && apt-get install -y -qq curl ca-certificates >/dev/null"

msg "Fetching install.sh into the container"
pct exec "$CTID" -- bash -c "curl -fsSL '$INSTALL_URL' -o /root/install.sh && chmod +x /root/install.sh"
[ "$BRANCH" != "main" ] && pct exec "$CTID" -- bash -c "echo 'export BRANCH=$BRANCH' >> /root/.bashrc"

echo
ok "Container $CTID ($HOSTNAME) is ready."
echo "Finish setup by running install.sh inside it (it prompts for your token + chat id):"
echo
echo "    bash /root/install.sh"
echo
echo "Dropping you into the container now (type the command above; 'exit' when done)."
echo "Later management:"
echo "    pct enter $CTID"
echo "    pct exec $CTID -- systemctl status telegram-assistant"
echo "    pct exec $CTID -- journalctl -u telegram-assistant -f"
echo
pct enter "$CTID"
