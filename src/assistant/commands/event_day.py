"""/event_day command: today's stadium status plus upcoming events."""

from __future__ import annotations

import logging

from telegram import Update
from telegram.ext import ContextTypes

from assistant.messages import today_status, upcoming
from assistant.sources.stadium import fetch_events

logger = logging.getLogger(__name__)

FETCH_ERROR = "Couldn't fetch stadium events right now. Please try again later."


async def event_day(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    days = context.bot_data["upcoming_days"]
    url = context.bot_data["stadium_url"]

    try:
        events = fetch_events(url)
    except Exception:
        logger.exception("Failed to fetch stadium events for /event_day")
        await update.message.reply_text(FETCH_ERROR)
        return

    text = f"{today_status(events)}\n\n{upcoming(events, days)}"
    await update.message.reply_text(text)
