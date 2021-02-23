from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list
from redbot.core.utils import deduplicate_iterables


class Aliases(commands.Cog):
    """Get all the alias information you could ever want about a command"""

    __version__ = "1.0.0"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**"

    def __init__(self, bot: Red):
        self.bot = bot

    @commands.command()
    async def aliases(self, ctx, *, command: str):
        """Get all the alias information you could ever want about a command"""
        strcommand = command
        command = self.bot.get_command(strcommand)

        # meh, safe enough as only reading, there is a big warning on cog install about this
        alias = self.bot.get_cog("Alias")
        guild_aliases = await alias.config.guild(ctx.guild).entries()
        global_aliases = await alias.config.entries()

        com_global_aliases = []
        com_guild_aliases = []

        for alias in guild_aliases:
            if alias["name"] == strcommand:
                command = self.bot.get_command(alias["command"])
                com_guild_aliases.append(alias["name"])

        for alias in global_aliases:
            if alias["name"] == strcommand:
                command = self.bot.get_command(alias["command"])
                com_global_aliases.append(alias["name"])

        if command is None:
            await ctx.send("Hmm, I can't find that command.")
            return
        com_name = command.qualified_name
        com_aliases = command.aliases
        com_parent = command.parent

        # run again as can miss some in edge cases
        for alias in guild_aliases:
            if alias["command"] == com_name:
                com_guild_aliases.append(alias["name"])
        for alias in global_aliases:
            if alias["command"] == com_name:
                com_global_aliases.append(alias["name"])

        # and probs picked up duplicates from second run so:
        com_guild_aliases = deduplicate_iterables(com_guild_aliases)
        com_global_aliases = deduplicate_iterables(com_global_aliases)

        com_builtin_aliases = []
        for i in range(len(com_aliases)):
            com_builtin_aliases.append(f"`{com_parent} {com_aliases[i]}`")
        for i in range(len(com_global_aliases)):
            com_global_aliases[i] = f"`{com_global_aliases[i]}`"
        for i in range(len(com_guild_aliases)):
            com_guild_aliases[i] = f"`{com_guild_aliases[i]}`"

        aliases = ""
        none = []
        if not com_builtin_aliases:
            none.append("built-in")
        else:
            list = humanize_list(com_builtin_aliases)
            aliases += f"Built-in aliases: {list}\n"
        if not com_global_aliases:
            none.append("global")
        else:
            list = humanize_list(com_global_aliases)
            aliases += f"Global aliases: {list}\n"
        if not com_guild_aliases:
            none.append("guild")
        else:
            list = humanize_list(com_guild_aliases)
            aliases += f"Guild aliases: {list}\n"

        none = humanize_list(none, style="or")

        msg = f"Main command: `{com_name}`\n{aliases}"

        if none:
            msg += f"This command has no {none} aliases."
        await ctx.send(msg)