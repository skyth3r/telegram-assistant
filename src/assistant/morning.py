"""Morning summary job.

A section-provider pattern: each section is an async function returning the text
to include, or None when it has nothing to report. The job runs every section,
drops the empty ones, and only messages the chat if something is worth saying.
Add future sections (weather, TfL, ...) by writing a function and appending it
to MORNING_SECTIONS.
"""

from __future__ import annotations

import logging
from typing import Awaitable, Callable

from telegram.ext import ContextTypes

from assistant.messages import event_day_text
from assistant.sources.stadium import fetch_events, is_event_today

logger = logging.getLogger(__name__)

Section = Callable[[ContextTypes.DEFAULT_TYPE], Awaitable[str | None]]


async def stadium_section(context: ContextTypes.DEFAULT_TYPE) -> str | None:
    """Stadium event details for today, or None when there is no event."""
    url = context.bot_data["stadium_url"]
    try:
        events = fetch_events(url)
    except Exception:
        logger.exception("Morning summary failed to fetch stadium events")
        return None
    event = is_event_today(events)
    if event is None:
        return None
    return event_day_text(event)


MORNING_SECTIONS: list[Section] = [stadium_section]


async def morning_summary(context: ContextTypes.DEFAULT_TYPE) -> None:
    """Compose the morning summary, messaging the chat only if a section has content."""
    parts = [text for section in MORNING_SECTIONS if (text := await section(context))]
    if not parts:
        return
    await context.bot.send_message(
        chat_id=context.bot_data["chat_id"], text="\n\n".join(parts)
    )
