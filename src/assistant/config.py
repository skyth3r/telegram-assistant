"""Configuration loaded from environment variables."""

from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv

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


def _parse_chat_ids(raw: str, fallback: str) -> list[int]:
    """Parse comma-separated chat ids; fall back to [fallback] when empty."""
    ids = [int(part.strip()) for part in raw.split(",") if part.strip()]
    return ids or [int(fallback)]


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

    return Config(
        bot_token=token,
        chat_id=chat_id,
        summary_time=os.environ.get("SUMMARY_TIME", "07:00"),
        summary_tz=os.environ.get("SUMMARY_TZ", "Europe/London"),
        upcoming_days=int(os.environ.get("UPCOMING_DAYS", "14")),
        stadium_url=os.environ.get("STADIUM_URL", STADIUM_URL),
        allowed_chat_ids=_parse_chat_ids(os.environ.get("ALLOWED_CHAT_IDS", ""), chat_id),
    )
