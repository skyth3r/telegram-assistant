# Deploy on a homelab (Proxmox LXC + systemd)

Runs the bot as an always-on systemd service in a Debian/Ubuntu LXC container. The
bot uses Telegram long-polling, so it only makes **outbound** connections — no port
forwarding, reverse proxy, or public URL is needed.

> Run it in exactly one place. If this service is active, do not also run the bot on
> your laptop or a cloud host: two pollers cause a Telegram `409 Conflict`.

## 1. Create the LXC

On the Proxmox host, create an unprivileged Debian 12 container (256 MB RAM is plenty).
Start it and open a root shell (`pct enter <vmid>`), then:

```sh
apt update && apt install -y git ca-certificates
```

Debian already ships system tz data, so `ZoneInfo("Europe/London")` works out of the box.

## 2. Create a service user and fetch the code

```sh
useradd --system --create-home --home-dir /opt/telegram-assistant --shell /usr/sbin/nologin telegram
git clone https://github.com/skyth3r/telegram-assistant.git /opt/telegram-assistant
chown -R telegram:telegram /opt/telegram-assistant
```

## 3. Install uv and sync dependencies

Install uv to a system location so the service user can use it:

```sh
curl -LsSf https://astral.sh/uv/install.sh | env UV_INSTALL_DIR=/usr/local/bin sh
cd /opt/telegram-assistant
sudo -u telegram /usr/local/bin/uv sync --frozen
```

This creates `/opt/telegram-assistant/.venv` with the project installed, so the service
can run `.venv/bin/python -m assistant.bot` directly (no sync at start time).

## 4. Configure environment

```sh
sudo -u telegram cp /opt/telegram-assistant/.env.example /opt/telegram-assistant/.env
# edit it: set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID (and optionally ALLOWED_CHAT_IDS)
chmod 600 /opt/telegram-assistant/.env
chown telegram:telegram /opt/telegram-assistant/.env
```

systemd reads this file via `EnvironmentFile`. The format is plain `KEY=value` lines
(the committed `.env.example` is already compatible).

## 5. Install and start the service

```sh
cp /opt/telegram-assistant/deploy/telegram-assistant.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now telegram-assistant
```

Check it:

```sh
systemctl status telegram-assistant
journalctl -u telegram-assistant -f
```

You should see the "Starting bot" log line. Send `/event_day` to your bot to confirm
it responds. The daily summary fires at `SUMMARY_TIME` (07:00 Europe/London by default).

## Updating

```sh
cd /opt/telegram-assistant
sudo -u telegram git pull
sudo -u telegram /usr/local/bin/uv sync --frozen
systemctl restart telegram-assistant
```

## Troubleshooting

- **`409 Conflict` in the logs** — the bot is running somewhere else too. Stop the other instance.
- **Service exits immediately** — check `journalctl`. A missing `TELEGRAM_BOT_TOKEN`/`TELEGRAM_CHAT_ID`
  raises a clear startup error; confirm `.env` is populated and readable by the `telegram` user.
- **Commands ignored** — your chat id must be in `ALLOWED_CHAT_IDS` (defaults to `TELEGRAM_CHAT_ID`).
