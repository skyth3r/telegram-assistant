# telegram-assistant

A personal Telegram assistant that sends daily summaries and responds to commands.

Currently it tracks **London Stadium event days** (useful as a parking heads-up):

- A daily summary at 07:00 Europe/London saying whether today is a stadium event day.
- An `/event_day` command returning today's status plus upcoming events.

## Setup

Requires [uv](https://docs.astral.sh/uv/) and Python 3.12+.

```sh
uv sync
cp .env.example .env   # then fill in your values
```

### Environment variables

| Variable              | Required | Default                                          | Description                          |
| --------------------- | -------- | ------------------------------------------------ | ------------------------------------ |
| `TELEGRAM_BOT_TOKEN`  | yes      | —                                                | Bot token from @BotFather            |
| `TELEGRAM_CHAT_ID`    | yes      | —                                                | Chat to send the daily summary to    |
| `SUMMARY_TIME`        | no       | `07:00`                                          | Daily summary time (HH:MM)           |
| `SUMMARY_TZ`          | no       | `Europe/London`                                  | Timezone for the summary time        |
| `UPCOMING_DAYS`       | no       | `14`                                             | Window for upcoming events           |
| `STADIUM_URL`         | no       | `https://www.london-stadium.com/events/all.html` | Source page                          |
| `ALLOWED_CHAT_IDS`    | no       | `TELEGRAM_CHAT_ID`                               | Comma-separated chat ids allowed to use commands |
| `BIN_COUNCIL`         | no       | —                                                | uk-bin-collection module for a London borough; blank disables bins |
| `BIN_COUNCIL_URL`     | no       | —                                                | Council bin-lookup URL for the module |
| `BIN_UPRN`            | no       | —                                                | Property UPRN (or use postcode + house number) |
| `BIN_POSTCODE`        | no       | —                                                | Property postcode, for boroughs that need it |
| `BIN_HOUSE_NUMBER`    | no       | —                                                | House number, for boroughs that need it |
| `BIN_WEB_DRIVER`      | no       | —                                                | Remote Selenium URL, for boroughs that need a browser |
| `BIN_SKIP_GET_URL`    | no       | `true`                                           | Pass `-s` to the council module |
| `BIN_REMINDER_TIME`   | no       | `20:00`                                          | Time (HH:MM, `SUMMARY_TZ`) to remind the night before |

Get your chat id by messaging the bot and checking
`https://api.telegram.org/bot<TOKEN>/getUpdates`.

### Bin collection reminder

When `BIN_COUNCIL` is set, the bot checks collections nightly at `BIN_REMINDER_TIME`
and messages the chat only when something is out the next day. `/bins` shows the
upcoming schedule on demand. Lookups use the
[uk-bin-collection](https://pypi.org/project/uk-bin-collection/) package; supported
boroughs are the London ones in `LONDON_BOROUGHS`
(`src/assistant/sources/bins.py`). Find your UPRN at
[findmyaddress.co.uk](https://www.findmyaddress.co.uk/search).

### Privacy / access

Commands are restricted to the chat ids in `ALLOWED_CHAT_IDS` (defaults to
`TELEGRAM_CHAT_ID`). Messages from any other chat are silently ignored, so the bot's
contents stay private even though its `@username` is publicly reachable.

## Run

```sh
uv run python -m assistant.bot
```

## Test

```sh
uv run pytest
```

## Deploy

The bot uses long-polling (outbound-only, no public URL needed) and must run as a
single always-on instance. For a homelab setup (Proxmox LXC + systemd):

```sh
# On the Proxmox host — creates the LXC, then drops you in to finish setup:
bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyth3r/telegram-assistant/main/proxmox-create.sh)"

# Or, inside an existing Debian/Ubuntu LXC:
bash -c "$(curl -fsSL https://raw.githubusercontent.com/skyth3r/telegram-assistant/main/install.sh)"
```

See [docs/deploy-homelab.md](docs/deploy-homelab.md) for details and manual steps.
