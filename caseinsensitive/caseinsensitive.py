from __future__ import annotations

import types
from typing import TYPE_CHECKING, Callable, Dict, List, Optional, Union

import discord
from discord.ext.commands.view import StringView
from redbot.cogs.alias.alias_entry import AliasCache, AliasEntry
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands.context import Context

from .fakealias import FakeAlias
from .vexutils import format_help, format_info, get_vex_logger

log = get_vex_logger(__name__)


class CaseInsensitiveStringView(StringView):
    """A subclass of StringView where StringView.skip_string is case insensitive."""

    def skip_string(self, string):
        strlen = len(string)
        if self.buffer[self.index : self.index + strlen].lower() == string.lower():
            self.previous = self.index
            self.index += strlen
            return True
        return False

    def get_word(self):
        pos = 0
        while not self.eof:
            try:
                current = self.buffer[self.index + pos]
                if current.isspace():
                    break
                pos += 1
            except IndexError:
                break
        self.previous = self.index
        result = self.buffer[self.index : self.index + pos]
        self.index += pos
        return result.lower()


# this could affect other cogs as described in install_msg in info.json
# copied from dpy version 2.2.3 (red 3.5.1)
async def ci_get_context_dpy2(
    self: Red, origin: Union[discord.Message, discord.Interaction], *, cls=Context
) -> Context:
    do_case_insensitive = not await self.cog_disabled_in_guild(
        CaseInsensitive(None), origin.guild  # type:ignore
    )  # its okay to create the class again without any issues (not great but okay) as no coms
    # will be registered and nothing will be plugged from the __init__ of the class

    if isinstance(origin, discord.Interaction):
        return await cls.from_interaction(origin)

    view = StringView(origin.content)
    ctx = cls(prefix=None, view=view, bot=self, message=origin)

    view = (
        CaseInsensitiveStringView(origin.content)
        if do_case_insensitive
        else StringView(origin.content)
    )

    ctx = cls(prefix=None, view=view, bot=self, message=origin)

    if origin.author.id == self.user.id:  # type: ignore
        return ctx

    prefix = await self.get_prefix(origin)
    invoked_prefix = prefix

    if isinstance(prefix, str):
        if not view.skip_string(prefix):
            return ctx
    else:
        try:
            # if the context class' __init__ consumes something from the view this
            # will be wrong.  That seems unreasonable though.
            if origin.content.lower().startswith(tuple(p.lower() for p in prefix)):
                invoked_prefix = discord.utils.find(view.skip_string, prefix)
            else:
                return ctx

        except TypeError:
            if not isinstance(prefix, list):
                raise TypeError(
                    "get_prefix must return either a string or a list of string, "
                    f"not {prefix.__class__.__name__}"
                )

            # It's possible a bad command_prefix got us here.
            for value in prefix:
                if not isinstance(value, str):
                    raise TypeError(
                        "Iterable command_prefix or list returned from get_prefix must "
                        f"contain only strings, not {value.__class__.__name__}"
                    )

            # Getting here shouldn't happen
            raise

    if self.strip_after_prefix:
        view.skip_ws()

    invoker = view.get_word()

    ctx.invoked_with = invoker
    # type-checker fails to narrow invoked_prefix type.
    ctx.prefix = invoked_prefix  # type: ignore
    ctx.command = self.all_commands.get(  # type:ignore
        invoker.lower() if do_case_insensitive else invoker
    )
    return ctx


# last edited in core ages ago so restriction of 3.4.11 from above is more than enough
async def ci_get_alias(
    self: AliasCache, guild: Optional[discord.Guild], alias_name: str
) -> Optional[AliasEntry]:
    """Returns an AliasEntry object if the provided alias_name is a registered alias"""
    server_aliases: List[AliasEntry] = []

    alias_name = alias_name.lower()

    if self._cache_enabled:
        aliases: Dict[Optional[int], Dict[str, AliasEntry]] = {}
        for guild_id, guild_aliases in self._aliases.items():
            aliases[guild_id] = {}
            for k, v in guild_aliases.items():
                aliases[guild_id][k.lower()] = v

        if alias_name in aliases[None]:
            return aliases[None][alias_name]
        if guild is not None:
            if guild.id in aliases:
                if alias_name in aliases[guild.id]:
                    return aliases[guild.id][alias_name]

    else:
        if guild:
            server_aliases = [
                AliasEntry.from_json(d) for d in await self.config.guild(guild).entries()
            ]
        global_aliases = [AliasEntry.from_json(d) for d in await self.config.entries()]

        all_aliases = global_aliases + server_aliases

        for alias in all_aliases:
            if alias.name.lower() == alias_name:
                return alias

    return None


# this class (apart from the version command) allows for a class which `command disablecog` can use
# and dealling with cog unload
class CaseInsensitive(commands.Cog):
    """
    This allows prefixes and commands to be case insensitive (for example ``!Ping``
    would be accepted and responded to).

    Whenever the cog is loaded, prefixes and commands will be case insensitive.
    This cog itself has no commands.

    If you want to disable it in a certain servers, use
    `[p]command disablecog CaseInsensitive`.

    There are also other configurations, such as setting a default as disabled
    and enabling per-server, listed under `[p]help command`.
    """

    __version__ = "1.0.5"
    __author__ = "@vexingvexed"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.old_get_context: Optional[Callable] = None
        self.old_alias_get: Optional[Callable] = None

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

    async def cog_load(self) -> None:
        self.plug_core()
        self.plug_alias()

        log.info("CaseInsensitive methods have been plugged")

    def plug_core(self) -> None:
        """Plug the case-insensitive shit."""
        new_method = types.MethodType(ci_get_context_dpy2, self.bot)

        self.old_get_context = self.bot.get_context
        self.bot.get_context = new_method

        log.trace("patched get_context for dpy2")

    def unplug_core(self) -> None:
        """Unplug case-insensitive stuff."""
        if self.old_get_context is not None:
            self.bot.get_context = self.old_get_context

            log.trace("unpatched get_context")

    def plug_alias(self) -> None:
        """Plug the alias magic."""
        alias_cog: Optional[commands.Cog] = self.bot.get_cog("Alias")
        if alias_cog is None:
            log.trace("not patching alias - not loaded")
            return

        if TYPE_CHECKING:
            assert isinstance(alias_cog, FakeAlias)

        new_method = types.MethodType(ci_get_alias, alias_cog._aliases)
        self.old_alias_get = alias_cog._aliases.get_alias
        alias_cog._aliases.get_alias = new_method

        log.trace("patched get_alias")

    def unplug_alias(self) -> None:
        alias_cog = self.bot.get_cog("Alias")
        if alias_cog is None or self.old_alias_get is None:
            log.trace("not unpatched get_alias - not loaded")
            return

        if TYPE_CHECKING:
            assert isinstance(alias_cog, FakeAlias)
        alias_cog._aliases.get_alias = self.old_alias_get

        log.trace("unpatched get_alias")

    async def cog_unload(self):
        self.unplug_core()
        self.unplug_alias()

        log.info("CaseInsensitive methods have been unplugged")

    @commands.Cog.listener()
    async def on_cog_add(self, cog: commands.Cog):
        if cog.qualified_name == "Alias":
            self.plug_alias()
