from typing import TYPE_CHECKING

from redbot.core.commands import BadArgument, Context, Converter

from status.core import FEEDS, MODES_LITERAL, SERVICE_LITERAL


class _ServiceTypeHint:
    name: SERVICE_LITERAL
    id: str
    url: str
    friendly: str
    avatar: str


if TYPE_CHECKING:
    ServiceConverter = _ServiceTypeHint
    ModeConverter = MODES_LITERAL
else:

    class ServiceConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> _ServiceTypeHint:
            argument = argument.casefold()
            if argument not in FEEDS.keys():
                # not the best but atm only used with `status` and `statusset` with both have
                # service lists in the docstring.
                raise BadArgument(
                    "That doesn't look like a valid service. "
                    f"Take a look at `{ctx.clean_prefix}help {ctx.command}` for a list."
                )

            self.name = argument
            self.id = FEEDS[argument]["id"]
            self.url = FEEDS[argument]["url"]
            self.friendly = FEEDS[argument]["friendly"]
            self.avatar = FEEDS[argument]["avatar"]

            return self

    class ModeConverter(Converter):
        async def convert(self, ctx: Context, argument: str) -> MODES_LITERAL:
            if argument.casefold() in ["all", "edit", "latest"]:
                return argument.casefold()

            raise BadArgument(
                "That doesn't look like a valid mode. Valid modes are `all`, `latest` and `edit`."
            )
