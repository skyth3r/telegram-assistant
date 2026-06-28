"""/bins command: upcoming bin collection days for the configured borough."""

from __future__ import annotations

import asyncio
import logging

from telegram import Update
from telegram.ext import ContextTypes

from assistant.messages import bin_summary_text
from assistant.sources.bins import fetch_bins

logger = logging.getLogger(__name__)

NOT_CONFIGURED = "Bin collections aren't configured."
FETCH_ERROR = "Couldn't fetch bin collections right now. Please try again later."


async def bins(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    cfg = context.bot_data.get("bin")
    if not cfg:
        await update.message.reply_text(NOT_CONFIGURED)
        return

    try:
        collections = await asyncio.to_thread(
            fetch_bins,
            cfg["council"],
            cfg["url"],
            uprn=cfg["uprn"],
            postcode=cfg["postcode"],
            house_number=cfg["house_number"],
            web_driver=cfg["web_driver"],
            skip_get_url=cfg["skip_get_url"],
        )
    except Exception:
        logger.exception("Failed to fetch bins for /bins")
        await update.message.reply_text(FETCH_ERROR)
        return

    await update.message.reply_text(bin_summary_text(collections))
