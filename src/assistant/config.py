"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

from assistant.sources.bins import LONDON_BOROUGHS
from assistant.sources.stadium import STADIUM_URL

load_dotenv()


@dataclass
class Config:
    bot_token: str
    chat_id: str
    summary_time: str
    summary_tz: str
    upcoming_days: int
    stadium_url: str
    allowed_chat_ids: list[int]
    bin_council: str | None = None
    bin_council_url: str | None = None
    bin_uprn: str | None = None
    bin_postcode: str | None = None
    bin_house_number: str | None = None
    bin_web_driver: str | None = None
    bin_skip_get_url: bool = True
    bin_reminder_time: str = "20:00"

    @property
    def bin_enabled(self) -> bool:
        """The bin feature needs a council, its URL, and an identifier."""
        return bool(
            self.bin_council
            and self.bin_council_url
            and (self.bin_uprn or self.bin_postcode)
        )


def _parse_chat_ids(raw: str, fallback: str) -> list[int]:
    """Parse comma-separated chat ids; fall back to [fallback] when empty."""
    ids = [int(part.strip()) for part in raw.split(",") if part.strip()]
    return ids or [int(fallback)]


def _bool_env(name: str, default: bool) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def load_config() -> Config:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    missing = [
        name
        for name, value in (("TELEGRAM_BOT_TOKEN", token), ("TELEGRAM_CHAT_ID", chat_id))
        if not value
    ]
    if missing:
        raise RuntimeError(f"Missing required environment variables: {', '.join(missing)}")

    bin_council = os.environ.get("BIN_COUNCIL") or None
    if bin_council and bin_council not in LONDON_BOROUGHS:
        raise RuntimeError(
            f"BIN_COUNCIL '{bin_council}' is not a supported London borough module"
        )

    return Config(
        bot_token=token,
        chat_id=chat_id,
        summary_time=os.environ.get("SUMMARY_TIME", "07:00"),
        summary_tz=os.environ.get("SUMMARY_TZ", "Europe/London"),
        upcoming_days=int(os.environ.get("UPCOMING_DAYS", "14")),
        stadium_url=os.environ.get("STADIUM_URL", STADIUM_URL),
        allowed_chat_ids=_parse_chat_ids(os.environ.get("ALLOWED_CHAT_IDS", ""), chat_id),
        bin_council=bin_council,
        bin_council_url=os.environ.get("BIN_COUNCIL_URL") or None,
        bin_uprn=os.environ.get("BIN_UPRN") or None,
        bin_postcode=os.environ.get("BIN_POSTCODE") or None,
        bin_house_number=os.environ.get("BIN_HOUSE_NUMBER") or None,
        bin_web_driver=os.environ.get("BIN_WEB_DRIVER") or None,
        bin_skip_get_url=_bool_env("BIN_SKIP_GET_URL", True),
        bin_reminder_time=os.environ.get("BIN_REMINDER_TIME", "20:00"),
    )
