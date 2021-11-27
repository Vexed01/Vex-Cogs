import types
from typing import Callable, Optional

import discord
from discord import Message
from discord.ext.commands.view import StringView  # not available in red commands
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands.context import Context

from .vexutils import format_help, format_info


class CaseInsensitiveStringView(StringView):
    """A subclass of StringView where StringView.skip_string is case insensitive."""

    def skip_string(self, string):
        strlen = len(string)
        if self.buffer[self.index : self.index + strlen].lower() == string.lower():
            self.previous = self.index
            self.index += strlen
            return True
        return False


# this could affect other cogs as described in install_msg in info.json
# copied from dpy 1.7.3 which is when it was last edited (hence req of red 3.4.11)
async def case_insensitive_get_context(self: Red, message: Message, *, cls=Context) -> None:
    do_case_insensitive = not await self.cog_disabled_in_guild(
        CaseInsensitive(None), message.guild  # type:ignore
    )  # its okay to create the class again without any issues (not great but okay) as no coms
    # will be registered and nothing will be plugged from the __init__ of the class

    view = (
        CaseInsensitiveStringView(message.content)
        if do_case_insensitive
        else StringView(message.content)
    )

    ctx = cls(prefix=None, view=view, bot=self, message=message)

    if self._skip_check(message.author.id, self.user.id):  # type:ignore
        return ctx

    prefix = await self.get_prefix(message)
    invoked_prefix = prefix

    if isinstance(prefix, str):
        if not view.skip_string(prefix):
            return ctx
    else:
        try:
            # if the context class' __init__ consumes something from the view this
            # will be wrong.  That seems unreasonable though.
            if message.content.lower().startswith(tuple(p.lower() for p in prefix)):
                invoked_prefix = discord.utils.find(view.skip_string, prefix)
            else:
                return ctx

        except TypeError:
            if not isinstance(prefix, list):
                raise TypeError(
                    "get_prefix must return either a string or a list of string, "
                    "not {}".format(prefix.__class__.__name__)
                )

            # It's possible a bad command_prefix got us here.
            for value in prefix:
                if not isinstance(value, str):
                    raise TypeError(
                        "Iterable command_prefix or list returned from get_prefix must "
                        "contain only strings, not {}".format(value.__class__.__name__)
                    )

            # Getting here shouldn't happen
            raise

    if self.strip_after_prefix:
        view.skip_ws()

    invoker = view.get_word()

    ctx.invoked_with = invoker
    ctx.prefix = invoked_prefix
    ctx.command = self.all_commands.get(invoker.lower() if do_case_insensitive else invoker)
    return ctx


# this class (apart from the version command) allows for a class which `command disablecog` can use
# and dealling with cog unload
class CaseInsensitive(commands.Cog):
    """
    This allows prefixes and commands to be case insensitive (for example ``!Ping``
    would be accepted and responded to).

    Whenever the cog is loaded, prefixes and commands will be case insensitive.
    This cog itself has no commands.

    If you want to disable it in a certain servers, use
    ``[p]command disablecog CaseInsensitiveComs``.

    There are also other configurations, such as setting a default as disabled
    and enabling per-server, listed under ``[p]help command``.
    """

    __version__ = "1.0.2"
    __author__ = "Vexed#9000"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.old_get_context: Optional[Callable] = None

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        # lets assume the owner wont run this.....
        return

    @commands.command(hidden=True)
    async def caseinsensitiveinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    def plug(self) -> None:
        """Plug the case-insensitive shit."""
        new_method = types.MethodType(case_insensitive_get_context, self.bot)
        self.old_get_context = self.bot.get_context
        self.bot.get_context = new_method  # type:ignore

    def unplug(self) -> None:
        """Unplug case-insensitive stuff."""
        if self.old_get_context is not None:
            self.bot.get_context = self.old_get_context  # type:ignore

    def cog_unload(self):
        self.unplug()
