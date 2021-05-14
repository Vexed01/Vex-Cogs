import datetime
from typing import TYPE_CHECKING, NamedTuple

from redbot.core.commands import BadArgument, Context, Converter, parse_timedelta


class TimeData(NamedTuple):
    freq: str
    friendly_freq: str
    delta: datetime.timedelta


if TYPE_CHECKING:
    TimespanConverter = TimeData

else:

    class TimespanConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> TimeData:
            if argument.lower() == "all":
                return TimeData("5min", "30 minutes", datetime.timedelta(days=9000))
            delta = parse_timedelta(argument, minimum=datetime.timedelta(hours=1))
            if delta is None:
                raise BadArgument("That's not a valid time.")

            if delta.seconds <= 86400:  # 1 day
                freq = "1min"
                friendly_freq = "1 minute"
            elif delta.days <= 7:
                freq = "10min"
                friendly_freq = "10 minutes"
            else:
                freq = "30min"
                friendly_freq = "30 minutes"

            return TimeData(freq, friendly_freq, delta)
