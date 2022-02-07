from typing import TYPE_CHECKING, Tuple

import rapidfuzz.process
from redbot.core.commands import BadArgument, Context, Converter

from timechannel.data import ZONE_KEYS

if TYPE_CHECKING:
    TimezoneConverter = Tuple[str, float, int]
else:

    class TimezoneConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> Tuple[str, float, int]:
            fuzzy_results = rapidfuzz.process.extract(
                argument, ZONE_KEYS, limit=2, score_cutoff=90
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

            return fuzzy_results[0]
