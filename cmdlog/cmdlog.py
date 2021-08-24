import asyncio
import datetime
import logging
import sys
from collections import deque
from io import BytesIO
from typing import Deque, Optional, Union

import discord
import sentry_sdk
import vexcogutils
from discord.channel import DMChannel, TextChannel
from discord.ext.commands.errors import CheckFailure as DpyCheckFailure
from discord.member import Member
from discord.message import PartialMessage
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.commands import CheckFailure as RedCheckFailure
from redbot.core.utils.chat_formatting import humanize_number, humanize_timedelta
from vexcogutils import format_help, format_info
from vexcogutils.chat import humanize_bytes
from vexcogutils.meta import out_of_date_check

from cmdlog.objects import TIME_FORMAT, LoggedAppCom, LoggedComError, LoggedCommand

if discord.__version__.startswith("2"):
    from discord import Interaction, InteractionType  # type:ignore

_log = logging.getLogger("red.vex.cmdlog")


class CmdLog(commands.Cog):
    """
    Log command usage in a form searchable by user ID, server ID or command name.

    The cog keeps an internal cache and everything is also logged to the bot's main logs under
    `red.vex.cmdlog`, level INFO.

    The internal cache is non persistant and subsequently is lost on cog unload,
    including bot shutdowns. The logged data will last until Red's custom logging
    rotator deletes old logs.
    """

    __author__ = "Vexed#3211"
    __version__ = "1.3.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.log_cache: Deque[Union[LoggedCommand, LoggedComError, LoggedAppCom]] = deque(
            maxlen=100_000
        )
        # this is about 50MB max from my simulated testing

        if discord.__version__.startswith("1"):
            self.load_time = datetime.datetime.utcnow()
        else:
            self.load_time = discord.utils.utcnow()  # type:ignore

        self.config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(log_content=False)

        self.log_content: Optional[bool] = None

        asyncio.create_task(self.async_init())

        # =========================================================================================
        # NOTE: IF YOU ARE EDITING MY COGS, PLEASE ENSURE SENTRY IS DISBALED BY FOLLOWING THE INFO
        # IN async_init(...) BELOW (SENTRY IS WHAT'S USED FOR TELEMETRY + ERROR REPORTING)
        self.sentry_hub: Optional[sentry_sdk.Hub] = None
        # =========================================================================================

    async def async_init(self):
        await out_of_date_check("cmdlog", self.__version__)

        # =========================================================================================
        # TO DISABLE SENTRY FOR THIS COG (EG IF YOU ARE EDITING THIS COG) EITHER DISABLE SENTRY
        # WITH THE `[p]vextelemetry` COMMAND, OR UNCOMMENT THE LINE BELOW, OR REMOVE IT COMPLETELY:
        # return

        await vexcogutils.sentryhelper.maybe_send_owners("cmdlog")

        while vexcogutils.sentryhelper.ready is False:
            await asyncio.sleep(0.1)

        if vexcogutils.sentryhelper.sentry_enabled is False:
            _log.debug("Sentry detected as disabled.")
            return

        _log.debug("Sentry detected as enabled.")
        self.sentry_hub = await vexcogutils.sentryhelper.get_sentry_hub("cmdlog", self.__version__)
        # =========================================================================================

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.bot.on_command_error(ctx, error, unhandled_by_cog=True)

        if self.sentry_hub is None:  # sentry disabled
            return

        with self.sentry_hub:
            sentry_sdk.add_breadcrumb(
                category="command", message="Command used was " + ctx.command.qualified_name
            )
            sentry_sdk.capture_exception(error.original)  # type:ignore
            _log.debug("Above exception successfully reported to Sentry")

    def cog_unload(self):
        if self.sentry_hub:
            self.sentry_hub.end_session()
            self.sentry_hub.client.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    # not supporting red_delete_data_for_user - see EUD statement in info.json or `[p]cog info`
    # whilst it is possible to remove data from the internal cache, data in the bot's logs isn't
    # so easy to remove so imo there's no point removing only 1 data location

    def log_com(self, ctx: commands.Context) -> None:
        logged_com = LoggedCommand(
            author=ctx.author,
            com_name=ctx.command.qualified_name,
            msg_id=ctx.message.id,
            channel=ctx.channel,
            guild=ctx.guild,
            log_content=self.log_content,
            content=ctx.message.content,
        )
        _log.info(logged_com)
        self.log_cache.append(logged_com)

    def log_ce(self, ctx: commands.Context) -> None:
        logged_com = LoggedComError(
            author=ctx.author,
            com_name=ctx.command.qualified_name,
            msg_id=ctx.message.id,
            channel=ctx.channel,
            guild=ctx.guild,
            log_content=self.log_content,
            content=ctx.message.content,
        )
        _log.info(logged_com)
        self.log_cache.append(logged_com)

    def cache_size(self) -> int:
        return sum(sys.getsizeof(i) for i in self.log_cache)

    def get_track_start(self) -> str:
        if len(self.log_cache) == 100_000:  # max size
            return "Max log size reached. Only the last 100 000 commands are stored."

        if discord.__version__.startswith("1"):
            ago = humanize_timedelta(timedelta=datetime.datetime.utcnow() - self.load_time)
        else:
            ago = humanize_timedelta(
                timedelta=discord.utils.utcnow() - self.load_time  # type:ignore
            )
        return f"Log started {ago} ago."

    def log_list_error(self, e):
        _log.exception("Something went wrong processing a command. See below for more info.", e)

        # a reminder data such as *IDs are scrubbed* before being sent to sentry and the log object
        # has a __repr__ without names (which sentry sends) which does not give actual names while
        # __str__ is what is logged to the user

        if self.sentry_hub is None:
            return

        with self.sentry_hub:
            sentry_sdk.capture_exception(e)

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        try:
            if self.log_content is None:
                self.log_content = await self.config.log_content()

            if ctx.guild:
                assert not isinstance(ctx.channel, discord.DMChannel)
            self.log_com(ctx)
        except Exception as e:
            self.log_list_error(e)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        try:
            if self.log_content is None:
                self.log_content = await self.config.log_content()

            if isinstance(error, (RedCheckFailure, DpyCheckFailure)):
                self.log_ce(ctx)
        except Exception as e:
            self.log_list_error(e)

    # SLASH COM PARSE FOR: KOWLIN'S SLASHINJECTOR
    @commands.Cog.listener()
    async def on_interaction_create(self, data: dict):
        try:
            if data.get("type") != 2:
                return

            userid = data.get("member", {}).get("user", {}).get("id")

            if data.get("guild_id", 0):
                user = self.bot.get_guild(data.get("guild_id", 0)).get_member(
                    userid
                )  # type:ignore
            else:
                user = self.bot.get_user(userid)

            inter_data = data["data"]
            chan = self.bot.get_channel(data.get("channel_id", 0))

            self.log_app_com(user, chan, inter_data)  # type:ignore
        except Exception as e:
            self.log_list_error(e)

    # SLASH COM PARSE FOR: DPY 2
    @commands.Cog.listener()
    async def on_interaction(self, inter: "Interaction"):
        try:
            if inter.type != InteractionType.application_command:
                return

            inter_data = inter.data
            user = inter.user
            chan = inter.channel

            self.log_app_com(user, chan, inter_data)
        except Exception as e:
            self.log_list_error(e)

    def log_app_com(
        self,
        user: Optional[Union[discord.User, discord.Member]],
        chan: Union[DMChannel, TextChannel],
        data: dict,
    ):
        if user is None:
            return

        target: Optional[Union[PartialMessage, Member]]
        if target_id := data.get("target_id"):
            target = chan.get_partial_message(target_id) or chan.guild.get_member(  # type:ignore
                target_id
            )
        else:
            target = None

        logged_com = LoggedAppCom(
            author=user,
            com_name=data.get("name"),  # type:ignore
            channel=chan,
            guild=chan.guild if isinstance(chan, TextChannel) else None,
            log_content=self.log_content,
            application_command=data["type"],
            target=target,
        )

        _log.info(logged_com)
        self.log_cache.append(logged_com)

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
    async def content(self, ctx: commands.Context, to_log: bool):
        """Set whether or not whole message content should be logged. Default false."""
        await self.config.log_content.set(to_log)
        self.log_content = to_log
        await ctx.send("Message content will " + ("now" if to_log else "now not") + " be logged.")

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
        logs = [f'[{i.time}] {i}' for i in self.log_cache]
        log_str = f"Generated at {now}.\n" + "\n".join(logs)
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send(
            "Here is the command log. " + self.get_track_start(),
            file=discord.File(logs_bytes, "cmdlog.txt"),
        )
        logs_bytes.close()

    @cmdlog.command()
    async def user(self, ctx: commands.Context, user_id: int):
        """
        Upload all the logs that are stored for a specific User ID in the cache.

        **Example:**
            - `[p]cmdlog user 418078199982063626`
        """
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [f'[{i.time}] {i}' for i in self.log_cache if i.user.id == user_id]
        log_str = f"Generated at {now} for user {user_id}.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that user."
        )  # happy doing this because of file previews
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send(
            f"Here is the command log for user {user_id}. " + self.get_track_start(),
            file=discord.File(logs_bytes, f"cmdlog_{user_id}.txt"),
        )
        logs_bytes.close()

    @cmdlog.command(aliases=["guild"])
    async def server(self, ctx: commands.Context, server_id: int):
        """
        Upload all the logs that are stored for for a specific server ID in the cache.

        **Example:**
            - `[p]cmdlog server 527961662716772392`
        """
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [
            f'[{i.time}] {i}'
            for i in self.log_cache
            if i.guild and i.guild.id == server_id
        ]

        log_str = f"Generated at {now} for server {server_id}.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that user."
        )  # happy doing this because of file previews
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send(
            f"Here is the command log for server {server_id}. " + self.get_track_start(),
            file=discord.File(logs_bytes, f"cmdlog_{server_id}.txt"),
        )
        logs_bytes.close()

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
        logs = [
            f'[{i.time}] {i}'
            for i in self.log_cache
            if i.command.startswith(command)
        ]

        log_str = f"Generated at {now} for command '{command}'.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that command."
        )  # happy doing this because of file previews
        logs_bytes = BytesIO(log_str.encode())

        await ctx.send(
            f"Here is the command log for command '{command}'. " + self.get_track_start(),
            file=discord.File(logs_bytes, f"cmdlog_{command.replace(' ', '_')}.txt"),
        )
        logs_bytes.close()
