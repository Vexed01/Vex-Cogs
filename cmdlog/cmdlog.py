import datetime
import logging
from collections import deque
from io import BytesIO
from typing import Deque, Union

import discord
from discord.ext.commands.errors import CheckFailure as DpyCheckFailure
from redbot.core import checks, commands
from redbot.core.bot import Red
from redbot.core.commands import CheckFailure as RedCheckFailure
from vexcogutils import format_help
from vexcogutils.utils import format_info

from cmdlog.objects import TIME_FORMAT, LoggedCheckFailure, LoggedCommand

log = logging.getLogger("red.vexed.cmdlog")


class CmdLog(commands.Cog):
    """
    Log command usage in a form searchable by user ID, server ID or command name.

    The cog keeps an internal cache and everything is also logged to the bot's main logs under
    `red.vexed.cmdlog`, level INFO.
    """

    __author__ = "Vexed#3211"
    __version__ = "1.0.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.log_cache: Deque[Union[LoggedCommand, LoggedCheckFailure]] = deque(maxlen=20000)
        # this is about 1MB max RAM

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    # not supporting red_delete_data_for_user - see EUD statement in info.json or `[p]cog info`

    def log_com(self, ctx: commands.Context) -> None:
        logged_com = LoggedCommand(ctx)
        log.info(logged_com)
        self.log_cache.append(logged_com)

    def log_cf(self, ctx: commands.Context) -> None:
        logged_com = LoggedCheckFailure(ctx)
        log.info(logged_com)
        self.log_cache.append(logged_com)

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.guild:
            # just for mypy:
            if isinstance(ctx.channel, discord.DMChannel):
                return
            self.log_com(ctx)
        else:
            self.log_com(ctx)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        if isinstance(error, (RedCheckFailure, DpyCheckFailure)):
            self.log_cf(ctx)

    @commands.command(hidden=True)
    async def cmdloginfo(self, ctx: commands.Context):
        await ctx.send(format_info(self.qualified_name, self.__version__))

    @checks.is_owner()
    @commands.group(aliases=["cmdlogs"])
    async def cmdlog(self, ctx: commands.Context):
        """
        View command logs.

        Note the cache is limited to 20 000 commands, which is approximately 1MB of RAM
        """

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
        """Upload all the logs that are stored for a specific User ID in the cache."""
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
        """Upload all the logs that are stored for for a specific server ID in the cache."""
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

    @cmdlog.command(aliases=["cmdlog"])
    async def command(self, ctx: commands.Context, *, command: str):
        """
        Upload all the logs that are stored for a specific command in the cache.

        This does not check it is a real command, so be careful. Do not enclose it in " if there
        are spaces.

        You can search for a group command (eg `cmdlog`) or a full command (eg `cmdlog user`).
        As arguments are not stored, you cannot search for them.
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
