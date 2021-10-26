import asyncio
import datetime
import traceback
from typing import List, Optional

import discord
import tabulate
from redbot.core.utils.chat_formatting import box, pagify
from sentry_sdk import Hub

from .consts import CHECK, CROSS


class VexLoop:
    """
    A class with some utilities for logging the state of a loop.

    Note iter_count increases at the start of an iteration.

    This does not log anything itself.
    """

    def __init__(self, friendly_name: str, expected_interval: float) -> None:
        self.friendly_name = friendly_name
        self.expected_interval = datetime.timedelta(seconds=expected_interval)

        self.iter_count: int = 0
        self.currently_running: bool = False  # whether the loop is running or sleeping
        self.last_exc: str = "No exception has occurred yet."
        self.last_exc_raw: Optional[BaseException] = None

        self.last_iter: Optional[datetime.datetime] = None
        self.next_iter: Optional[datetime.datetime] = None

    def __repr__(self) -> str:
        return (
            f"<friendly_name={self.friendly_name} iter_count={self.iter_count} "
            f"currently_running={self.currently_running} last_iter={self.last_iter} "
            f"next_iter={self.next_iter} integrity={self.integrity}>"
        )

    @property
    def integrity(self) -> bool:
        """
        If the loop is running on time (whether or not next expected iteration is in the future)
        """
        if self.next_iter is None:  # not started yet
            return False
        return self.next_iter > datetime.datetime.utcnow()

    @property
    def until_next(self) -> float:
        """
        Positive float with the seconds until the next iteration, based off the last
        iteration and the interval.

        If the expected time of the next iteration is in the past, this will return `0.0`
        """
        if self.next_iter is None:  # not started yet
            return 0.0

        raw_until_next = (self.next_iter - datetime.datetime.utcnow()).total_seconds()
        if raw_until_next > self.expected_interval.total_seconds():  # should never happen
            return self.expected_interval.total_seconds()
        elif raw_until_next > 0.0:
            return raw_until_next
        else:
            return 0.0

    async def sleep_until_next(self) -> None:
        """Sleep until the next iteration. Basically an "all-in-one" version of `until_next`."""
        await asyncio.sleep(self.until_next)

    def iter_start(self) -> None:
        """Register an iteration as starting."""
        self.iter_count += 1
        self.currently_running = True
        self.last_iter = datetime.datetime.utcnow()
        self.next_iter = datetime.datetime.utcnow() + self.expected_interval
        # this isn't accurate, it will be "corrected" when finishing is called

    def iter_finish(self) -> None:
        """Register an iteration as finished successfully."""
        self.currently_running = False
        # now this is accurate. imo its better to have something than nothing

    def iter_error(self, error: BaseException, sentry_hub: Optional[Hub] = None) -> None:
        """Register an iteration's exception. If enabled, will report to Sentry."""
        self.currently_running = False
        self.last_exc_raw = error
        self.last_exc = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

        if sentry_hub is None:
            return

        with sentry_hub:
            sentry_hub.capture_exception(error)

    def get_debug_embed(self) -> discord.Embed:
        """Get an embed with infomation on this loop."""
        raw_data: List[list] = [
            ["expected_interval", self.expected_interval],
            ["iter_count", self.iter_count],
            ["currently_running", self.currently_running],
            ["last_iter", self.last_iter or "Loop not started"],
            ["next_iter", self.next_iter or "Loop not started"],
        ]

        now = datetime.datetime.utcnow()
        processed_data: List[list]
        if self.next_iter and self.last_iter:
            processed_data = [
                ["Seconds until next", (self.next_iter - now).total_seconds()],
                ["Seconds since last", (now - self.last_iter).total_seconds()],
            ]
        else:
            processed_data = [[]]

        emoji = CHECK if self.integrity else CROSS
        embed = discord.Embed(title=f"{self.friendly_name}: `{emoji}`")
        embed.add_field(name="Raw data", value=box(tabulate.tabulate(raw_data)), inline=False)
        embed.add_field(
            name="Processed data",
            value=box(tabulate.tabulate(processed_data) or "Loop hasn't started yet."),
            inline=False,
        )
        exc = self.last_exc
        if len(exc) > 1024:
            exc = list(pagify(exc, page_length=1024))[0] + "\n..."
        embed.add_field(name="Exception", value=box(exc), inline=False)

        return embed
