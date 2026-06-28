"""Bin collection lookup for London boroughs via the uk-bin-collection package.

The borough and property identifiers come entirely from configuration, so this
module names no specific borough: it only knows "a London borough".
"""

from __future__ import annotations

import json
import warnings
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from zoneinfo import ZoneInfo

from urllib3.exceptions import InsecureRequestWarning

LONDON = ZoneInfo("Europe/London")

# uk-bin-collection council module names for London boroughs. Configuring any one
# of these reveals only that the user is in London, not which borough.
LONDON_BOROUGHS: frozenset[str] = frozenset(
    {
        "BarkingDagenham",
        "BarnetCouncil",
        "BexleyCouncil",
        "BrentCouncil",
        "BromleyBoroughCouncil",
        "CroydonCouncil",
        "EalingCouncil",
        "EnfieldCouncil",
        "HackneyCouncil",
        "HaringeyCouncil",
        "Hillingdon",
        "IslingtonCouncil",
        "KingstonUponThamesCouncil",
        "LondonBoroughCamdenCouncil",
        "LondonBoroughEaling",
        "LondonBoroughHammersmithandFulham",
        "LondonBoroughHarrow",
        "LondonBoroughHavering",
        "LondonBoroughHounslow",
        "LondonBoroughLambeth",
        "LondonBoroughLewisham",
        "LondonBoroughOfRichmondUponThames",
        "LondonBoroughRedbridge",
        "LondonBoroughSutton",
        "MertonCouncil",
        "NewhamCouncil",
        "RoyalBoroughofGreenwich",
        "SouthwarkCouncil",
        "TowerHamletsCouncil",
        "WalthamForest",
        "WandsworthCouncil",
        "WestminsterCityCouncil",
    }
)

_DATE_FMT = "%d/%m/%Y"  # uk-bin-collection normalises every council to this


@dataclass
class BinCollection:
    bin_type: str
    date: date


def _repair_transposed_date(value: date, *, today: date, horizon_days: int = 90) -> date:
    """Undo an upstream day/month transposition.

    Some councils render dates as d/m while uk-bin-collection reads them as m/d
    (or vice versa), so the parsed date can land in the past. A real "next
    collection" is never in the past, so when swapping day<->month produces a
    near-future date, use that instead.
    """
    if value >= today:
        return value
    try:
        swapped = value.replace(month=value.day, day=value.month)
    except ValueError:
        return value  # day > 12 can't be a month, so not a transposition
    if today <= swapped <= today + timedelta(days=horizon_days):
        return swapped
    return value


def fetch_bins(
    council: str,
    url: str,
    *,
    uprn: str | None = None,
    postcode: str | None = None,
    house_number: str | None = None,
    web_driver: str | None = None,
    skip_get_url: bool = True,
) -> list[BinCollection]:
    """Look up bin collections for the configured borough/property.

    Blocking (network, plus an optional Selenium driver for some boroughs); call
    via asyncio.to_thread from async handlers.
    """
    # lazy import keeps the heavy package out of startup when bins is unused.
    from uk_bin_collection.uk_bin_collection.collect_data import UKBinCollectionApp

    args = [council, url]
    if skip_get_url:
        args.append("-s")
    if uprn:
        args += ["-u", uprn]
    if postcode:
        args += ["-p", postcode]
    if house_number:
        args += ["-n", house_number]
    if web_driver:
        args += ["-w", web_driver]

    app = UKBinCollectionApp()
    app.set_args(args)
    # Some council sites (e.g. Newham) serve a broken TLS cert, so the upstream
    # collector requests with verify=False. Silence the resulting urllib3 warning
    # just for this lookup rather than process-wide.
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", InsecureRequestWarning)
        payload = json.loads(app.run())

    today = datetime.now(LONDON).date()
    collections: list[BinCollection] = []
    for item in payload.get("bins", []):
        try:
            when = datetime.strptime(item.get("collectionDate", ""), _DATE_FMT).date()
        except ValueError:
            continue
        when = _repair_transposed_date(when, today=today)
        collections.append(BinCollection(bin_type=item.get("type", "Bin"), date=when))
    return collections


def _now(now: datetime | None) -> datetime:
    return now if now is not None else datetime.now(LONDON)


def bins_tomorrow(
    collections: list[BinCollection], *, now: datetime | None = None
) -> list[BinCollection]:
    """Collections due tomorrow (London calendar date)."""
    tomorrow = _now(now).astimezone(LONDON).date() + timedelta(days=1)
    return [c for c in collections if c.date == tomorrow]
