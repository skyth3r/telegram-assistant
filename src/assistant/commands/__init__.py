"""Command registry.

Each command is described by a CommandSpec. To add a new command: create a
module with an async handler, then append its spec to COMMANDS. bot.py registers
everything listed here, so no other wiring is needed.

Note: Telegram command names allow only [a-z0-9_], so the slash command is
/event_day (hyphens are not permitted by Telegram).
"""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass

from telegram import Update
from telegram.ext import ContextTypes

from assistant.commands import event_day

Handler = Callable[[Update, ContextTypes.DEFAULT_TYPE], Awaitable[None]]


@dataclass(frozen=True)
class CommandSpec:
    name: str
    handler: Handler
    description: str


COMMANDS: list[CommandSpec] = [
    CommandSpec(
        name="event_day",
        handler=event_day.event_day,
        description="Is today a stadium event day, plus upcoming events",
    ),
]
