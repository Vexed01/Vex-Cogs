import datetime
import logging
import sys
from collections import deque
from io import BytesIO
from typing import Deque, Union

import discord
from discord.ext.commands.errors import CheckFailure as DpyCheckFailure
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.commands import CheckFailure as RedCheckFailure
from redbot.core.utils.chat_formatting import humanize_number
from vexcogutils import format_help, format_info
from vexcogutils.chat import humanize_bytes

from cmdlog.objects import TIME_FORMAT, LoggedCheckFailure, LoggedCommand

_log = logging.getLogger("red.vex.cmdlog")


class CmdLog(commands.Cog):
    """
    Log command usage in a form searchable by user ID, server ID or command name.

    The cog keeps an internal cache and everything is also logged to the bot's main logs under
    `red.vex.cmdlog`, level INFO.
    """

    __author__ = "Vexed#3211"
    __version__ = "1.1.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.log_cache: Deque[Union[LoggedCommand, LoggedCheckFailure]] = deque(maxlen=100_000)
        # this is about 50MB max from my simulated testing

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    # not supporting red_delete_data_for_user - see EUD statement in info.json or `[p]cog info`

    def log_com(self, ctx: commands.Context) -> None:
        logged_com = LoggedCommand(ctx)
        _log.info(logged_com)
        self.log_cache.append(logged_com)

    def log_cf(self, ctx: commands.Context) -> None:
        logged_com = LoggedCheckFailure(ctx)
        _log.info(logged_com)
        self.log_cache.append(logged_com)

    def cache_size(self) -> int:
        return sum(sys.getsizeof(i) for i in self.log_cache)

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.guild:
            assert not isinstance(ctx.channel, discord.DMChannel)
        self.log_com(ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, (RedCheckFailure, DpyCheckFailure)):
            self.log_cf(ctx)

    @commands.command(hidden=True)
    async def cmdloginfo(self, ctx: commands.Context):
        main = await format_info(self.qualified_name, self.__version__)
        cache_size = humanize_bytes(self.cache_size(), 1)
        cache_count = humanize_number(len(self.log_cache))
        extra = f"\nCache size: {cache_size} with {cache_count} commands."
        await ctx.send(main + extra)

    @commands.is_owner()
    @commands.group(aliases=["cmdlogs"])
    async def cmdlog(self, ctx: commands.Context):
        """
        View command logs.

        Note the cache is limited to 100 000 commands, which is approximately 50MB of RAM
        """

    @cmdlog.command()
    async def cache(self, ctx: commands.Context):
        """Show the size of the internal command cache."""
        cache_bytes = self.cache_size()
        _log.debug(f"Cache size is exactly {cache_bytes} bytes.")
        cache_size = humanize_bytes(cache_bytes, 1)
        cache_count = humanize_number(len(self.log_cache))
        await ctx.send(f"\nCache size: {cache_size} with {cache_count} commands.")

    @cmdlog.command()
    async def full(self, ctx: commands.Context):
        """Upload all the logs that are stored in the cache."""
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [f"[{i.time}] {str(i)}" for i in self.log_cache]
        log_str = f"Generated at {now}.\n" + "\n".join(logs)
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send("Here is the command log.", file=discord.File(logs_bytes, "cmdlog.txt"))

    @cmdlog.command()
    async def user(self, ctx: commands.Context, user_id: int):
        """
        Upload all the logs that are stored for a specific User ID in the cache.

        **Example:**
            - `[p]cmdlog user 418078199982063626`
        """
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [f"[{i.time}] {str(i)}" for i in self.log_cache if i.user.id == user_id]
        log_str = f"Generated at {now} for user {user_id}.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that user."
        )  # happy doing this because of file previews
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send(
            f"Here is the command log for user {user_id}.",
            file=discord.File(logs_bytes, f"cmdlog_{user_id}.txt"),
        )

    @cmdlog.command(aliases=["guild"])
    async def server(self, ctx: commands.Context, server_id: int):
        """
        Upload all the logs that are stored for for a specific server ID in the cache.

        **Example:**
            - `[p]cmdlog server 527961662716772392`
        """
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [
            f"[{i.time}] {str(i)}" for i in self.log_cache if i.guild and i.guild.id == server_id
        ]
        log_str = f"Generated at {now} for server {server_id}.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that user."
        )  # happy doing this because of file previews
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send(
            f"Here is the command log for server {server_id}.",
            file=discord.File(logs_bytes, f"cmdlog_{server_id}.txt"),
        )

    @cmdlog.command()
    async def command(self, ctx: commands.Context, *, command: str):
        """
        Upload all the logs that are stored for a specific command in the cache.

        This does not check it is a real command, so be careful. Do not enclose it in " if there
        are spaces.

        You can search for a group command (eg `cmdlog`) or a full command (eg `cmdlog user`).
        As arguments are not stored, you cannot search for them.

        **Examples:**
            - `[p]cmdlog command ping`
            - `[p]cmdlog command playlist`
            - `[p]cmdlog command playlist create`
        """
        # not checking if a command exists because want to allow for this to find it if it was
        # unloaded (eg if com was found to be intensive, see if it was one user spamming it)
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [f"[{i.time}] {str(i)}" for i in self.log_cache if i.command.startswith(command)]
        log_str = f"Generated at {now} for command '{command}'.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that command."
        )  # happy doing this because of file previews
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send(
            f"Here is the command log for command '{command}'.",
            file=discord.File(logs_bytes, f"cmdlog_{command.replace(' ', '_')}.txt"),
        )
