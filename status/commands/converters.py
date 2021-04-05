from redbot.core.commands import BadArgument, Context, Converter

from ..core.consts import FEEDS


class ServiceConverter(Converter):
    def __init__(self):
        # for typehinting, copied from Service in objects/service.py

        self.name: str
        self.id: str
        self.url: str
        self.friendly: str
        self.avatar: str

    async def convert(self, ctx: Context, argument: str):
        argument = argument.casefold()
        if argument not in FEEDS.keys():
            # not the best but atm only used with `status` and `statusset` with both have service
            # lists in the docstring.
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
    async def convert(self, ctx: Context, argument: str):
        if argument.casefold() in ["all", "edit", "latest"]:
            return argument.casefold()

        raise BadArgument("That doesn't look like a valid mode. Valid modes are `all`, `latest` and `edit`.")
