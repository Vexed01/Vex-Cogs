from typing import TYPE_CHECKING

import rapidfuzz
from pytz import common_timezones
from redbot.core.commands import BadArgument, Context, Converter

if TYPE_CHECKING:
    TimezoneConverter = str
else:

    class TimezoneConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> str:
            fuzzy_results = rapidfuzz.process.extract(
                argument, common_timezones, limit=2, score_cutoff=90
            )
            if len(fuzzy_results) > 1:
                raise BadArgument(
                    "That search returned too many matches. Use the `Region/Location` format or "
                    'you can see the full list here (the "TZ database name" '
                    "column):\nhttps://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List"
                )
            if len(fuzzy_results) == 0:
                raise BadArgument(
                    "That search didn't find any matches. You should be able to enter any "
                    'major city, or you can see the full list here (the "TZ database name" '
                    "column):\nhttps://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List"
                )

            return fuzzy_results[0][0]
