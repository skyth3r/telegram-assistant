"""Bot entry point: registers commands, schedules the morning summary, runs polling."""

from __future__ import annotations

import asyncio
import logging
from datetime import time
from zoneinfo import ZoneInfo

from telegram.ext import Application, CommandHandler, ContextTypes, filters

from assistant.commands import COMMANDS
from assistant.config import Config, load_config
from assistant.messages import bin_reminder_text
from assistant.morning import morning_summary
from assistant.sources.bins import bins_tomorrow, fetch_bins

logging.basicConfig(
    format="%(asctime)s %(name)s %(levelname)s %(message)s", level=logging.INFO
)
logger = logging.getLogger(__name__)


async def bin_reminder(context: ContextTypes.DEFAULT_TYPE) -> None:
    """At reminder time, message the chat only when a collection is due tomorrow."""
    cfg = context.bot_data.get("bin")
    if not cfg:
        return
    chat_id = context.bot_data["chat_id"]
    try:
        collections = await asyncio.to_thread(
            fetch_bins,
            cfg["council"],
            cfg["url"],
            uprn=cfg["uprn"],
            postcode=cfg["postcode"],
            house_number=cfg["house_number"],
            web_driver=cfg["web_driver"],
            skip_get_url=cfg["skip_get_url"],
        )
    except Exception:
        logger.exception("Bin reminder failed to fetch collections")
        return
    due = bins_tomorrow(collections)
    if not due:
        return
    await context.bot.send_message(chat_id=chat_id, text=bin_reminder_text(due))


def build_application(config: Config) -> Application:
    app = Application.builder().token(config.bot_token).build()

    app.bot_data["chat_id"] = config.chat_id
    app.bot_data["stadium_url"] = config.stadium_url
    app.bot_data["upcoming_days"] = config.upcoming_days
    app.bot_data["bin"] = (
        {
            "council": config.bin_council,
            "url": config.bin_council_url,
            "uprn": config.bin_uprn,
            "postcode": config.bin_postcode,
            "house_number": config.bin_house_number,
            "web_driver": config.bin_web_driver,
            "skip_get_url": config.bin_skip_get_url,
        }
        if config.bin_enabled
        else None
    )

    # Restrict every command to allowlisted chats; unknown chats are silently ignored.
    chat_filter = filters.Chat(chat_id=config.allowed_chat_ids)
    for spec in COMMANDS:
        app.add_handler(CommandHandler(spec.name, spec.handler, filters=chat_filter))

    hour, minute = (int(part) for part in config.summary_time.split(":"))
    app.job_queue.run_daily(
        morning_summary,
        time=time(hour=hour, minute=minute, tzinfo=ZoneInfo(config.summary_tz)),
        name="morning_summary",
    )

    if config.bin_enabled:
        bin_hour, bin_minute = (int(p) for p in config.bin_reminder_time.split(":"))
        app.job_queue.run_daily(
            bin_reminder,
            time=time(hour=bin_hour, minute=bin_minute, tzinfo=ZoneInfo(config.summary_tz)),
            name="bin_reminder",
        )

    return app


def main() -> None:
    config = load_config()
    app = build_application(config)
    logger.info("Starting bot with %d command(s)", len(COMMANDS))
    app.run_polling()


if __name__ == "__main__":
    main()
