import asyncio
import datetime
import traceback
from typing import Optional

import discord
from redbot.core.utils.chat_formatting import box, pagify
from rich.table import Table  # type:ignore

from .chat import no_colour_rich_markup
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

    def iter_error(self, error: BaseException) -> None:
        """Register an iteration's exception."""
        self.currently_running = False
        self.last_exc_raw = error
        self.last_exc = "".join(
            traceback.format_exception(type(error), error, error.__traceback__)
        )

    def get_debug_embed(self) -> discord.Embed:
        """Get an embed with infomation on this loop."""
        table = Table("Key", "Value")

        table.add_row("expected_interval", str(self.expected_interval))
        table.add_row("iter_count", str(self.iter_count))
        table.add_row("currently_running", str(self.currently_running))
        table.add_row("last_iterstr", str(self.last_iter) or "Loop not started")
        table.add_row("next_iterstr", str(self.next_iter) or "Loop not started")

        raw_table_str = no_colour_rich_markup(table)

        now = datetime.datetime.utcnow()

        if self.next_iter and self.last_iter:
            table = Table("Key", "Value")
            table.add_row("Seconds until next", str((self.next_iter - now).total_seconds()))
            table.add_row("Seconds since last", str((now - self.last_iter).total_seconds()))
            processed_table_str = no_colour_rich_markup(table)

        else:
            processed_table_str = "Loop hasn't started yet."

        emoji = CHECK if self.integrity else CROSS
        embed = discord.Embed(title=f"{self.friendly_name}: `{emoji}`")
        embed.add_field(name="Raw data", value=raw_table_str, inline=False)
        embed.add_field(
            name="Processed data",
            value=processed_table_str,
            inline=False,
        )
        exc = self.last_exc
        if len(exc) > 1024:
            exc = list(pagify(exc, page_length=1024))[0] + "\n..."
        embed.add_field(name="Exception", value=box(exc), inline=False)

        return embed
