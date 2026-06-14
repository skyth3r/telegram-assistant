from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from assistant import messages
from assistant.sources import stadium

FIXTURE = Path(__file__).parent / "fixtures" / "london_stadium.html"
LONDON = ZoneInfo("Europe/London")


def load_events():
    return stadium.parse_events(FIXTURE.read_text())


def test_today_status_event_day():
    events = load_events()
    target = events[0]
    now = datetime(target.date.year, target.date.month, target.date.day, 9, 0, tzinfo=LONDON)
    text = messages.today_status(events, now=now)
    assert "Today is a stadium event day" in text
    assert target.name in text


def test_today_status_no_event():
    events = load_events()
    now = datetime(1990, 1, 1, 9, 0, tzinfo=LONDON)
    text = messages.today_status(events, now=now)
    assert "No stadium event" in text


def test_upcoming_lists_events():
    events = load_events()
    first = events[0]
    now = datetime(first.date.year, first.date.month, first.date.day, 9, 0, tzinfo=LONDON)
    text = messages.upcoming(events, 30, now=now)
    assert "Upcoming events" in text
    assert "•" in text


def test_upcoming_empty_window():
    events = load_events()
    now = datetime(1990, 1, 1, 9, 0, tzinfo=LONDON)
    text = messages.upcoming(events, 7, now=now)
    assert "No upcoming events in the next 7 days" in text
