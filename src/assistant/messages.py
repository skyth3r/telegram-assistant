"""Shared message text builders.

Keeping formatting here means the daily summary job and the /event-day command
produce consistent output.
"""

from __future__ import annotations

from datetime import date, datetime

from assistant.sources.bins import BinCollection
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


def bin_reminder_text(due: list[BinCollection]) -> str:
    """The reminder the night before, listing bins to put out for tomorrow's collection."""
    lines = ["\U0001f5d1️ Bins out tonight - collection tomorrow:"]
    lines += [f"• {c.bin_type}" for c in due]
    return "\n".join(lines)


def bin_summary_text(collections: list[BinCollection]) -> str:
    """Upcoming collections, sorted by date with bins sharing a date grouped."""
    if not collections:
        return "No upcoming bin collections found."
    by_date: dict[date, list[str]] = {}
    for c in sorted(collections, key=lambda c: c.date):
        types = by_date.setdefault(c.date, [])
        if c.bin_type not in types:
            types.append(c.bin_type)
    lines = ["\U0001f5d1️ Upcoming bin collections:"]
    lines += [f"• {d.strftime('%a %d %b')}: {', '.join(by_date[d])}" for d in sorted(by_date)]
    return "\n".join(lines)
