from typing import TYPE_CHECKING

from redbot.core import commands
from redbot.core.commands.context import Context

from .consts import GEOS

if TYPE_CHECKING:
    TimeframeConverter = str
    GeoConverter = str
else:

    class TimeframeConverter(commands.Converter):
        """Converts user input into a timeframe string suitable for Google Trends."""

        async def convert(self, ctx: Context, argument: str) -> str:
            # see timeframe at of https://github.com/GeneralMills/pytrends#common-api-parameters
            argument = argument.lower()
            if argument in ("all", "alltime"):
                return "all"
            if argument in ("hour", "1hour", "1h"):
                return "now 1-H"
            if argument in ("4hour", "4hours", "4h", "4hrs"):
                return "now 4-H"
            if argument in ("today", "day", "1d", "1day", "24h", "24hours"):
                return "now 1-d"
            if argument in ("week", "1w", "1week", "7d", "7day", "7days"):
                return "now 7-d"
            if argument in ("month", "1m", "1month", "1mo"):
                return "today 1-m"
            if argument in ("3month", "3months", "3m", "3mo"):
                return "today 3-m"
            if argument in ("year", "1y", "1year", "1yr", "12months", "12m", "12mo"):
                return "today 12-m"
            if argument in ("5year", "5y", "5years", "5yrs"):
                return "today 5-y"
            raise commands.BadArgument(
                f"Invalid timeframe: {argument}."
                "See `{ctx.clean_prefix}help {ctx.command.qualified_name}` for a valid list."
            )

            # thank you copilot saving me time

    class GeoConverter(commands.Converter):
        """Converts user input into a geo string suitable for Google Trends."""

        async def convert(self, ctx: Context, argument: str) -> str:
            argument = argument.upper()
            if argument in ("WORLD", "WORLDWIDE", "GLOBAL", "ALL"):
                return ""
            if argument not in GEOS.values():
                raise commands.BadArgument(
                    "That is an invalid location. See `[p]help trends` for a link to a list."
                )
            return argument
