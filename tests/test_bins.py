import json
from datetime import date, datetime
from zoneinfo import ZoneInfo

import pytest

from assistant.messages import bin_reminder_text, bin_summary_text
from assistant.sources import bins as binsrc
from assistant.sources.bins import BinCollection

LONDON = ZoneInfo("Europe/London")

# uk-bin-collection always normalises dates to dd/mm/yyyy.
SAMPLE = {
    "bins": [
        {"type": "Domestic", "collectionDate": "02/07/2026"},
        {"type": "Recycling", "collectionDate": "02/07/2026"},
        {"type": "Food Waste", "collectionDate": "09/07/2026"},
        {"type": "Garden", "collectionDate": "not-a-date"},
    ]
}


@pytest.fixture
def fake_app(monkeypatch):
    class FakeApp:
        def set_args(self, args):
            self.args = args

        def run(self):
            return json.dumps(SAMPLE)

    monkeypatch.setattr(
        "uk_bin_collection.uk_bin_collection.collect_data.UKBinCollectionApp",
        FakeApp,
    )


def test_fetch_bins_maps_and_skips_bad_dates(fake_app):
    out = binsrc.fetch_bins("ExampleBoroughCouncil", "https://example", uprn="x")
    assert [(c.bin_type, c.date) for c in out] == [
        ("Domestic", date(2026, 7, 2)),
        ("Recycling", date(2026, 7, 2)),
        ("Food Waste", date(2026, 7, 9)),
    ]


def test_bins_tomorrow_filters_to_next_day(fake_app):
    out = binsrc.fetch_bins("ExampleBoroughCouncil", "https://example", uprn="x")
    now = datetime(2026, 7, 1, 20, 0, tzinfo=LONDON)
    due = binsrc.bins_tomorrow(out, now=now)
    assert {c.bin_type for c in due} == {"Domestic", "Recycling"}


def test_bins_tomorrow_empty_when_no_collection(fake_app):
    out = binsrc.fetch_bins("ExampleBoroughCouncil", "https://example", uprn="x")
    now = datetime(2026, 7, 5, 20, 0, tzinfo=LONDON)
    assert binsrc.bins_tomorrow(out, now=now) == []


def test_summary_groups_bins_sharing_a_date():
    cols = [
        BinCollection("Recycling", date(2026, 7, 2)),
        BinCollection("Domestic", date(2026, 7, 2)),
        BinCollection("Food Waste", date(2026, 7, 9)),
    ]
    text = bin_summary_text(cols)
    assert "Recycling, Domestic" in text
    assert "Food Waste" in text


def test_reminder_lists_due_bins():
    text = bin_reminder_text([BinCollection("Domestic", date(2026, 7, 2))])
    assert "Domestic" in text


TODAY = date(2026, 6, 28)


def test_repair_swaps_past_date_to_future():
    # Upstream read 02/07 (2 Jul) as m/d -> 7 Feb (past); swap recovers 2 Jul.
    assert binsrc._repair_transposed_date(date(2026, 2, 7), today=TODAY) == date(2026, 7, 2)


def test_repair_leaves_future_date_untouched():
    assert binsrc._repair_transposed_date(date(2026, 7, 2), today=TODAY) == date(2026, 7, 2)


def test_repair_keeps_past_date_when_swap_also_past():
    # 05/03 -> swap 03/05 (3 May) still before today, so no confident repair.
    assert binsrc._repair_transposed_date(date(2026, 3, 5), today=TODAY) == date(2026, 3, 5)


def test_repair_ignores_non_transposable_day():
    # day 25 can't be a month; leave as-is rather than guess.
    assert binsrc._repair_transposed_date(date(2026, 1, 25), today=TODAY) == date(2026, 1, 25)
