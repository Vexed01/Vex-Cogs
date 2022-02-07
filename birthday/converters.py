import datetime
from typing import TYPE_CHECKING

from dateutil.parser import ParserError, parse
from redbot.core.commands import BadArgument, Context, Converter

if TYPE_CHECKING:
    BirthdayConverter = datetime.datetime
    TimeConverter = datetime.datetime
else:

    class BirthdayConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> datetime.datetime:
            try:
                default = datetime.datetime(year=1, month=1, day=1)
                out = parse(argument, default=default, ignoretz=True).replace(
                    hour=0, minute=0, second=0, microsecond=0
                )
                return out
            except ParserError:
                raise BadArgument(
                    f"That's not a valid date. See {ctx.clean_prefix}help"
                    f" {ctx.command.qualified_name} for more information."
                )

    class TimeConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> datetime.datetime:
            try:
                return parse(argument, ignoretz=True).replace(
                    year=1, month=1, day=1, minute=0, second=0, microsecond=0
                )
            except ParserError:
                raise BadArgument(
                    f"That's not a valid time. See {ctx.clean_prefix}help"
                    f" {ctx.command.qualified_name} for more information."
                )
