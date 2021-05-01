from typing import TYPE_CHECKING

import rapidfuzz
from pytz import common_timezones
from redbot.core.commands import BadArgument, Context, Converter

if TYPE_CHECKING:
    TimezoneConverter = str
else:

    class TimezoneConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> str:
            fuzzy = rapidfuzz.process.extractOne(argument, common_timezones, score_cutoff=90)
            if fuzzy is None:
                raise BadArgument(
                    "That doesn't look like a valid timezone. You should be able to enter any "
                    'major city, or you can see the full list here (the "TZ database name" '
                    "column):\nhttps://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List"
                )

            return fuzzy[0]
