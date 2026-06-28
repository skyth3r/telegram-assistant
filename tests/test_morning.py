import asyncio
from datetime import datetime
from pathlib import Path
from types import SimpleNamespace
from zoneinfo import ZoneInfo

import assistant.morning as morning
from assistant.sources import stadium

FIXTURE = Path(__file__).parent / "fixtures" / "london_stadium.html"
LONDON = ZoneInfo("Europe/London")


def load_events():
    return stadium.parse_events(FIXTURE.read_text())


def make_context(sent):
    async def send_message(*, chat_id, text):
        sent.append((chat_id, text))

    return SimpleNamespace(
        bot_data={"chat_id": "42", "stadium_url": "https://example.com"},
        bot=SimpleNamespace(send_message=send_message),
    )


def test_morning_summary_silent_when_nothing_to_report(monkeypatch):
    monkeypatch.setattr(morning, "fetch_events", lambda url: [])
    sent = []
    asyncio.run(morning.morning_summary(make_context(sent)))
    assert sent == []


def test_morning_summary_posts_on_event_day(monkeypatch):
    events = load_events()
    monkeypatch.setattr(morning, "fetch_events", lambda url: events)
    target = events[0]
    fixed = datetime(target.date.year, target.date.month, target.date.day, 9, 0, tzinfo=LONDON)

    class _DateTime(datetime):
        @classmethod
        def now(cls, tz=None):
            return fixed

    monkeypatch.setattr(stadium, "datetime", _DateTime)
    sent = []
    asyncio.run(morning.morning_summary(make_context(sent)))
    assert len(sent) == 1
    assert target.name in sent[0][1]
