"""Shared message text builders.

Keeping formatting here means the daily summary job and the /event-day command
produce consistent output.
"""

from __future__ import annotations

from datetime import datetime

from assistant.sources.stadium import Event, events_in_next_days, is_event_today


def today_status(events: list[Event], *, now: datetime | None = None) -> str:
    event = is_event_today(events, now=now)
    if event is None:
        return "✅ No stadium event at London Stadium today."
    return (
        "\U0001f3df Today is a stadium event day:\n"
        f"{event.name}\n{event.timestamp}"
    )


def upcoming(events: list[Event], days: int, *, now: datetime | None = None) -> str:
    items = events_in_next_days(events, days, now=now)
    if not items:
        return f"No upcoming events in the next {days} days."
    lines = [f"\U0001f4c5 Upcoming events (next {days} days):"]
    lines += [f"• {e.day} {e.month}: {e.name}" for e in items]
    return "\n".join(lines)
