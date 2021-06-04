import datetime
from typing import TYPE_CHECKING

from redbot.core.commands import BadArgument, Context, Converter, parse_timedelta

if TYPE_CHECKING:
    TimespanConverter = datetime.timedelta

else:

    class TimespanConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> datetime.timedelta:
            if argument.lower() == "all":
                return datetime.timedelta(days=9000)
            delta = parse_timedelta(argument, minimum=datetime.timedelta(hours=1))
            if delta is None:
                raise BadArgument("That's not a valid time.")

            return delta
