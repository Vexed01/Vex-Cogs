from typing import List

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils import deduplicate_iterables
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.utils.chat_formatting import inline as cf_inline
from redbot.core.utils.chat_formatting import pagify

from .vexutils import format_help, format_info, get_vex_logger, inline_hum_list

log = get_vex_logger(__name__)


def inline(text: str) -> str:
    """Get the given text as inline code."""
    return cf_inline(text.lstrip())


class Aliases(commands.Cog):
    """Get all the alias information you could ever want about a command."""

    __version__ = "1.0.6"
    __author__ = "Vexed#0714"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def aliasesinfo(self, ctx: commands.Context) -> None:
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    @commands.command(usage="<command>")
    async def aliases(self, ctx: commands.Context, *, strcommand: str):
        """
        Get all the alias information you could ever want about a command.

        This will show the main command, built-in aliases, global aliases and
        server aliases.

        **Examples:**
            - `[p]aliases foo`
            - `[p]aliases foo bar`
        """
        command = self.bot.get_command(strcommand)

        alias_cog = self.bot.get_cog("Alias")
        if alias_cog is None:
            if command is None:
                return await ctx.send("Hmm, I can't find that command.")
            full_com = command.qualified_name
            builtin_aliases = command.aliases
            com_parent = command.parent or ""

            com_builtin_aliases = [
                inline(f"{com_parent} {builtin_aliases[i]}") for i in range(len(builtin_aliases))
            ]

            msg = "I was unable to get information from the alias cog. It's probably not loaded.\n"
            msg += f"Main command: `{full_com}`\nBuilt in aliases: "
            msg += humanize_list(com_builtin_aliases)
            return await ctx.send(msg)

        alias_conf: Config = alias_cog.config  # type:ignore
        all_global_aliases: List[dict] = await alias_conf.entries()

        if ctx.guild:
            all_guild_aliases: List[dict] = await alias_conf.guild(ctx.guild).entries()
        else:
            all_guild_aliases = []

        # check if command is actually from alias cog
        if command is None:
            for alias in all_guild_aliases:
                if alias["name"] == strcommand:
                    command = self.bot.get_command(alias["command"])

            for alias in all_global_aliases:
                if alias["name"] == strcommand:
                    command = self.bot.get_command(alias["command"])

        if command is None:
            return await ctx.send("That's not a command or alias.")

        builtin_aliases = command.aliases
        com_parent = command.parent or ""

        guild_aliases = [
            alias["name"]
            for alias in all_guild_aliases
            if strcommand in [alias["command"], alias["name"]]
        ]

        global_aliases = [
            alias["name"]
            for alias in all_global_aliases
            if strcommand in [alias["command"], alias["name"]]
        ]

        # and probs picked up duplicates on second run so:
        guild_aliases = deduplicate_iterables(guild_aliases)
        guild_aliases = [i for i in guild_aliases if not self.bot.get_command(i)]
        global_aliases = deduplicate_iterables(global_aliases)
        global_aliases = [i for i in global_aliases if not self.bot.get_command(i)]

        # make everything inline + make built in aliases
        hum_builtin_aliases = inline_hum_list([f"{com_parent} {i}" for i in builtin_aliases])
        hum_global_aliases = inline_hum_list(global_aliases)
        hum_guild_aliases = inline_hum_list(guild_aliases)

        aliases = ""
        none = []
        if hum_builtin_aliases:
            aliases += f"Built-in aliases: {hum_builtin_aliases}\n"
        else:
            none.append("built-in")

        if hum_global_aliases:
            aliases += f"Global aliases: {hum_global_aliases}\n"
        else:
            none.append("global")

        if hum_guild_aliases:
            aliases += f"Server aliases: {hum_guild_aliases}\n"
        elif ctx.guild:
            none.append("guild")
        else:
            aliases += "You're in DMs, so there aren't any server aliases."
        str_none = humanize_list(none, style="or")

        msg = f"Main command: `{command.name}`\n{aliases}"

        if str_none:
            msg += f"This command has no {str_none} aliases."

        pages = pagify(msg, delims=["\n", ", "])
        for page in pages:
            await ctx.send(page)
