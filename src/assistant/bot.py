"""Bot entry point: registers commands, schedules the daily summary, runs polling."""

from __future__ import annotations

import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, CommandHandler, ContextTypes, filters

from assistant.commands import COMMANDS
from assistant.config import Config, load_config
from assistant.messages import today_status
from assistant.sources.stadium import fetch_events

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def daily_summary(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Send the today-only stadium status to the configured chat."""
    chat_id = context.bot_data["chat_id"]
    url = context.bot_data["stadium_url"]
    try:
        events = fetch_events(url)
    except Exception:
        logger.exception("Daily summary failed to fetch stadium events")
        return
    await context.bot.send_message(chat_id=chat_id, text=today_status(events))


def build_application(config: Config) -> Application:
    app = Application.builder().token(config.bot_token).build()

    app.bot_data["chat_id"] = config.chat_id
    app.bot_data["stadium_url"] = config.stadium_url
    app.bot_data["upcoming_days"] = config.upcoming_days

    # Restrict every command to allowlisted chats; unknown chats are silently ignored.
    chat_filter = filters.Chat(chat_id=config.allowed_chat_ids)
    for spec in COMMANDS:
        app.add_handler(CommandHandler(spec.name, spec.handler, filters=chat_filter))

    hour, minute = (int(part) for part in config.summary_time.split(":"))
    app.job_queue.run_daily(
        daily_summary,
        time=time(hour=hour, minute=minute, tzinfo=ZoneInfo(config.summary_tz)),
        name="daily_summary",
    )

    return app


def main() -> None:
    config = load_config()
    app = build_application(config)
    logger.info("Starting bot with %d command(s)", len(COMMANDS))
    app.run_polling()


if __name__ == "__main__":
    main()
