import datetime
from typing import TYPE_CHECKING, List

from redbot.core.commands import BadArgument, Context, Converter, parse_timedelta


class _GraphConverter(Converter):
    async def convert(self, ctx: Context, argument: str, valid: List[str]) -> str:
        if argument.lower() not in valid:
            raise BadArgument(
                f"That's not a valid graph. See `{ctx.clean_prefix}help stattrack "
                f"{ctx.command.name}` for a list of valid types and some examples."
            )
        return argument.lower()


if TYPE_CHECKING:
    TimespanConverter = datetime.timedelta
    StatusGraphConverter = str
    UserGraphConverter = str
    ChannelGraphConverter = str

else:

    class TimespanConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> datetime.timedelta:
            if argument.lower() == "all":
                return datetime.timedelta(days=9000)
            delta = parse_timedelta(argument, minimum=datetime.timedelta(hours=1))
            if delta is None:
                raise BadArgument("That's not a valid time.")

            return delta

    class StatusGraphConverter(_GraphConverter):
        async def convert(self, ctx: Context, argument: str) -> str:
            return await super().convert(ctx, argument, ["online", "offline", "idle", "dnd"])

    class UserGraphConverter(_GraphConverter):
        async def convert(self, ctx: Context, argument: str) -> str:
            return await super().convert(ctx, argument, ["total", "unique", "humans", "bots"])

    class ChannelGraphConverter(_GraphConverter):
        async def convert(self, ctx: Context, argument: str) -> str:
            return await super().convert(
                ctx, argument, ["text", "voice", "category", "stage", "total"]
            )
