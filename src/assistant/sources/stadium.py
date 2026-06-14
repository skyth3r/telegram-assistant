"""Scraper for London Stadium event days.

Python port of the reference Go program. Fetches the stadium's public events
page, parses the event cards, and answers two questions: is today an event day,
and what is coming up.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

STADIUM_URL = "https://www.london-stadium.com/events/all.html"
LONDON = ZoneInfo("Europe/London")
_USER_AGENT = "Mozilla/5.0 (compatible; telegram-assistant/0.1)"


@dataclass
class Event:
    name: str
    date: datetime  # timezone-aware
    day: str
    month: str
    timestamp: str


def _text(card, class_name: str) -> str:
    el = card.find(class_=class_name)
    return el.get_text(" ", strip=True) if el else ""


def parse_events(html: str) -> list[Event]:
    """Parse event cards out of the stadium events page HTML."""
    soup = BeautifulSoup(html, "html.parser")
    events: list[Event] = []

    for card in soup.find_all("div", class_="event-card"):
        name = _text(card, "event-card__name")
        if not name:
            continue

        date_el = card.find("div", class_="event-card__date")
        date_str = date_el.get("content", "") if date_el else ""
        if not date_str:
            continue
        try:
            date = datetime.fromisoformat(date_str)
        except ValueError:
            continue

        events.append(
            Event(
                name=name,
                date=date,
                day=_text(card, "event-card__date-day"),
                month=_text(card, "event-card__date-month"),
                timestamp=_text(card, "event-card__timestamp"),
            )
        )

    return events


def fetch_events(url: str = STADIUM_URL, *, timeout: float = 15.0) -> list[Event]:
    """Fetch and parse events from the live stadium page."""
    resp = requests.get(url, headers={"User-Agent": _USER_AGENT}, timeout=timeout)
    resp.raise_for_status()
    return parse_events(resp.text)


def _now(now: datetime | None) -> datetime:
    return now if now is not None else datetime.now(LONDON)


def is_event_today(events: list[Event], *, now: datetime | None = None) -> Event | None:
    """Return the event happening today (London calendar date), or None.

    Unlike the Go reference (which only checked the first card), this scans the
    whole list, so it is robust to ordering.
    """
    today = _now(now).astimezone(LONDON).date()
    for event in events:
        if event.date.astimezone(LONDON).date() == today:
            return event
    return None


def events_in_next_days(
    events: list[Event], days: int, *, now: datetime | None = None
) -> list[Event]:
    """Events strictly after now and within `days` days, sorted by date."""
    current = _now(now)
    horizon = current + timedelta(days=days)
    upcoming = [e for e in events if current < e.date < horizon]
    return sorted(upcoming, key=lambda e: e.date)
