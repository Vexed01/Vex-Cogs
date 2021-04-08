from typing import List

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils import deduplicate_iterables
from redbot.core.utils.chat_formatting import humanize_list, inline, pagify
from vexcogutils import format_help, format_info, inline_hum_list


class Aliases(commands.Cog):
    """Get all the alias information you could ever want about a command."""

    __version__ = "1.0.2"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        return format_help(self, ctx)

    def __init__(self, bot: Red):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    def _inline(self, text: str):
        return inline(text.lstrip())

    @commands.command(hidden=True)
    async def aliasesinfo(self, ctx: commands.Context):
        await ctx.send(format_info(self.qualified_name, self.__version__))

    @commands.command(usage="<command>")
    async def aliases(self, ctx: commands.Context, *, strcommand: str):
        """
        Get all the alias information you could ever want about a command.

        This will show the main command, built-in aliases, global aliases and
        server aliases.
        """
        command: commands.Command = self.bot.get_command(strcommand)

        try:
            alias_cog = self.bot.get_cog("Alias")
            all_global_aliases = await alias_cog.config.entries()
        except Exception:
            if command is None:
                return await ctx.send("Hmm, I can't find that command.")
            full_com = command.qualified_name
            builtin_aliases = command.aliases
            com_parent = command.parent or ""

            com_builtin_aliases = [
                self._inline(f"{com_parent} {builtin_aliases[i]}") for i in range(len(builtin_aliases))
            ]

            msg = "I was unable to get information from the alias cog. It's probably not loaded.\n"
            msg += f"Main command: `{full_com}`\nBuilt in aliases: "
            msg += humanize_list(com_builtin_aliases)
            return await ctx.send(msg)

        global_aliases = []
        guild_aliases = []
        if ctx.guild:
            all_guild_aliases: List[dict] = await alias_cog.config.guild(ctx.guild).entries()
        else:
            all_guild_aliases = []

        # check if command is actually from alias cog
        if command is None:
            for alias_cog in all_guild_aliases:
                if alias_cog["name"] == strcommand:
                    command = self.bot.get_command(alias_cog["command"])
                    full_com = alias_cog["command"]

            for alias_cog in all_global_aliases:
                if alias_cog["name"] == strcommand:
                    command = self.bot.get_command(alias_cog["command"])
                    full_com = alias_cog["command"]

        else:
            full_com = command.qualified_name

        if command is None:
            return await ctx.send("That's not a command or alias.")

        builtin_aliases = command.aliases
        com_parent = command.parent or ""

        if command is None:
            await ctx.send("Hmm, I can't find that command.")
            return

        for alias_cog in all_guild_aliases:
            if full_com in [alias_cog["command"], alias_cog["name"]]:
                guild_aliases.append(alias_cog["name"])
        for alias_cog in all_global_aliases:
            if full_com in [alias_cog["command"], alias_cog["name"]]:
                global_aliases.append(alias_cog["name"])

        # and probs picked up duplicates on second run so:
        guild_aliases = deduplicate_iterables(guild_aliases)
        global_aliases = deduplicate_iterables(global_aliases)

        # make everything inline + make built in aliases
        # inline_builtin_aliases = [self._inline(f"{com_parent} {i}") for i in builtin_aliases]
        # inline_global_aliases = [self._inline(i) for i in global_aliases]
        # inline_guild_aliases = [self._inline(i) for i in guild_aliases]
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
        else:
            if ctx.guild:
                none.append("guild")
            else:
                aliases += "You're in DMs, so there aren't any server aliases."
        none = humanize_list(none, style="or")

        msg = f"Main command: `{full_com}`\n{aliases}"

        if none:
            msg += f"This command has no {none} aliases."

        pages = pagify(msg, delims=["\n", ", "])
        for page in pages:
            await ctx.send(page)
