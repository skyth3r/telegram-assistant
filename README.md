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

Get your chat id by messaging the bot and checking
`https://api.telegram.org/bot<TOKEN>/getUpdates`.

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
