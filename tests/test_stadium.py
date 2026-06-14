from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from assistant.sources import stadium

FIXTURE = Path(__file__).parent / "fixtures" / "london_stadium.html"
LONDON = ZoneInfo("Europe/London")


def load_events():
    return stadium.parse_events(FIXTURE.read_text())


def test_parse_events_returns_all_cards():
    events = load_events()
    # The fixture page lists many events; the first card is a known one.
    assert len(events) > 0
    first = events[0]
    assert first.name == "Take That: The Circus Live 2026"
    assert first.day == "25"
    assert first.month == "Jun"
    assert "Thursday" in first.timestamp


def test_parse_events_dates_are_timezone_aware():
    for event in load_events():
        assert event.date.tzinfo is not None


def test_parse_events_first_date():
    first = load_events()[0]
    assert first.date.year == 2026
    assert first.date.month == 6
    assert first.date.day == 25


def test_is_event_today_matches_a_calendar_date():
    events = load_events()
    target = events[0]
    now = datetime(target.date.year, target.date.month, target.date.day, 9, 0, tzinfo=LONDON)
    assert stadium.is_event_today(events, now=now) is not None
    assert stadium.is_event_today(events, now=now).name == target.name


def test_is_event_today_scans_all_events_not_just_first():
    events = load_events()
    # Pick an event that is NOT the first card to prove we scan the whole list.
    target = events[2]
    now = datetime(target.date.year, target.date.month, target.date.day, 9, 0, tzinfo=LONDON)
    found = stadium.is_event_today(events, now=now)
    assert found is not None
    assert found.day == target.day


def test_is_event_today_returns_none_when_no_match():
    events = load_events()
    now = datetime(1990, 1, 1, 9, 0, tzinfo=LONDON)
    assert stadium.is_event_today(events, now=now) is None


def test_events_in_next_days_window_and_sorted():
    events = load_events()
    first = events[0]
    # Day before the first event, looking 7 days ahead.
    now = datetime(first.date.year, first.date.month, first.date.day, 9, 0, tzinfo=LONDON)
    now = now.replace(day=first.date.day - 1) if first.date.day > 1 else now
    upcoming = stadium.events_in_next_days(events, 7, now=now)
    assert all(e.date > now for e in upcoming)
    assert all((e.date - now).days < 7 for e in upcoming)
    assert upcoming == sorted(upcoming, key=lambda e: e.date)


def test_events_in_next_days_excludes_far_future():
    events = load_events()
    now = datetime(1990, 1, 1, 9, 0, tzinfo=LONDON)
    assert stadium.events_in_next_days(events, 7, now=now) == []
