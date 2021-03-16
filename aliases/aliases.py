from typing import List

from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils import deduplicate_iterables
from redbot.core.utils.chat_formatting import humanize_list, inline


class Aliases(commands.Cog):
    """Get all the alias information you could ever want about a command."""

    __version__ = "1.0.1"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        docs = "This cog has docs! Check them out at\nhttps://vex-cogs.readthedocs.io/en/latest/cogs/aliases.html"
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**\n{docs}"
        # adding docs link here so doesn't show up in auto generated docs

    def __init__(self, bot: Red):
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    def _inline(self, text: str):
        return inline(text.lstrip())

    @commands.command()
    async def aliases(self, ctx: commands.Context, *, command: str):
        """
        Get all the alias information you could ever want about a command.

        This will show the main command, built-in aliases, global aliases and
        server aliases.
        """
        strcommand = command
        command: commands.Command = self.bot.get_command(strcommand)

        # meh, safe enough as only reading, there is a big warning on cog install about this
        try:
            alias_cog = self.bot.get_cog("Alias")
            all_global_aliases = await alias_cog.config.entries()
        except Exception:
            if command is None:
                return await ctx.send("Hmm, I can't find that command.")
            full_com = command.qualified_name
            builtin_aliases = command.aliases
            com_parent = command.parent or ""

            com_builtin_aliases = []
            for i in range(len(builtin_aliases)):
                com_builtin_aliases.append(self._inline(f"{com_parent} {builtin_aliases[i]}"))

            msg = "I was unable to get information from the alias cog. It's probably not loaded.\n"
            msg += f"Main command: `{full_com}`\nBuilt in aliases: "
            msg += humanize_list(com_builtin_aliases)
            return await ctx.send(msg)

        global_aliases = []
        guild_aliases = []

        if ctx.guild:
            all_guild_aliases: List[dict] = await alias_cog.config.guild(ctx.guild).entries()
            for alias_cog in all_guild_aliases:
                if alias_cog["name"] == strcommand:
                    command = self.bot.get_command(alias_cog["command"])
                    guild_aliases.append(alias_cog["name"])

        for alias_cog in all_global_aliases:
            if alias_cog["name"] == strcommand:
                command = self.bot.get_command(alias_cog["command"])
                global_aliases.append(alias_cog["name"])

        if command is None:
            await ctx.send("Hmm, I can't find that command.")
            return

        full_com = command.qualified_name
        builtin_aliases = command.aliases
        com_parent = command.parent or ""

        if ctx.guild:
            for alias_cog in all_guild_aliases:
                if alias_cog["command"] == full_com:
                    guild_aliases.append(alias_cog["name"])
        for alias_cog in all_global_aliases:
            if alias_cog["command"] == full_com:
                global_aliases.append(alias_cog["name"])

        # and probs picked up duplicates on secod run so:
        guild_aliases = deduplicate_iterables(guild_aliases)
        global_aliases = deduplicate_iterables(global_aliases)

        # make everything inline + make built in aliases
        com_builtin_aliases = []
        for i in range(len(builtin_aliases)):
            com_builtin_aliases.append(self._inline(f"{com_parent} {builtin_aliases[i]}"))
        for i in range(len(global_aliases)):
            global_aliases[i] = self._inline(global_aliases[i])
        for i in range(len(guild_aliases)):
            guild_aliases[i] = self._inline(guild_aliases[i])

        aliases = ""
        none = []
        if not com_builtin_aliases:
            none.append("built-in")
        else:
            list = humanize_list(com_builtin_aliases)
            aliases += f"Built-in aliases: {list}\n"
        if not global_aliases:
            none.append("global")
        else:
            list = humanize_list(global_aliases)
            aliases += f"Global aliases: {list}\n"
        if not guild_aliases:
            if ctx.guild:
                none.append("guild")
            else:
                aliases += "Your're in DMs, so ther aren't any server aliases."
        else:
            list = humanize_list(guild_aliases)
            aliases += f"Server aliases: {list}\n"

        none = humanize_list(none, style="or")

        msg = f"Main command: `{full_com}`\n{aliases}"

        if none:
            msg += f"This command has no {none} aliases."
        await ctx.send(msg)
