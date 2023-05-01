import datetime
import sys
from collections import deque
from io import StringIO
from typing import TYPE_CHECKING, Deque, Optional, Union

import discord
from discord.channel import TextChannel
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_number, humanize_timedelta

from cmdlog.objects import TIME_FORMAT, LoggedAppCom, LoggedComError, LoggedCommand

from .channellogger import ChannelLogger
from .vexutils import format_help, format_info, get_vex_logger
from .vexutils.chat import humanize_bytes

if discord.__version__.startswith("2"):
    from discord import Interaction, InteractionType

log = get_vex_logger(__name__)


class CmdLog(commands.Cog):
    """
    Log command usage in a form searchable by user ID, server ID or command name.

    The cog keeps an internal cache and everything is also logged to the bot's main logs under
    `red.vex.cmdlog`, level INFO.

    The internal cache is non persistant and subsequently is lost on cog unload,
    including bot shutdowns. The logged data will last until Red's custom logging
    rotator deletes old logs.
    """

    __author__ = "Vexed#0714"
    __version__ = "1.5.4"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.log_cache: Deque[Union[LoggedCommand, LoggedComError, LoggedAppCom]] = deque(
            maxlen=100_000
        )
        # this is about 50MB max from my simulated testing

        if discord.__version__.startswith("1"):
            self.load_time = datetime.datetime.utcnow()
        else:
            self.load_time = discord.utils.utcnow()

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(log_content=False)
        self.config.register_global(log_channel=None)

        self.log_content: Optional[bool] = None

        self.channel_logger: Optional[ChannelLogger] = None

        bot.loop.create_task(self.start_channel_logger())

    async def start_channel_logger(self) -> None:
        await self.bot.wait_until_red_ready()

        chan_id: Optional[str] = await self.config.log_channel()
        if chan_id is not None:
            chan = self.bot.get_channel(int(chan_id))
            if chan is not None:
                self.channel_logger = ChannelLogger(self.bot, chan)  # type:ignore
                self.channel_logger.start()
            else:
                log.warning("Commands will NOT be sent to a channel because it appears invalid.")

    async def cog_unload(self):
        if self.channel_logger:
            self.channel_logger.stop()

        log.trace("cmdlog unload")

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    # not supporting red_delete_data_for_user - see EUD statement in info.json or `[p]cog info`
    # whilst it is possible to remove data from the internal cache, data in the bot's logs isn't
    # so easy to remove so imo there's no point removing only 1 data location

    def log_com(self, ctx: commands.Context) -> None:
        logged_com = LoggedCommand(
            user=ctx.author,
            command=ctx.command.qualified_name,
            msg_id=ctx.message.id,
            channel=ctx.channel,
            guild=ctx.guild,
            log_content=self.log_content,
            content=ctx.message.content,
        )
        log.info(logged_com)
        self.log_cache.append(logged_com)
        if self.channel_logger:
            self.channel_logger.add_command(logged_com)

    def log_ce(self, ctx: commands.Context, error: commands.CommandError) -> None:
        if isinstance(
            error,
            (
                commands.ConversionError,
                commands.MissingRequiredArgument,
                # commands.MissingRequiredAttachment,  # waiting for red 3.5
                commands.TooManyArguments,
                commands.BadArgument,
                commands.UserInputError,
            ),
        ):
            error_info = "an error with inputted command arguments"
        elif isinstance(
            error,
            (commands.BotMissingPermissions, commands.BotMissingRole, commands.BotMissingAnyRole),
        ):
            error_info = "the bot missing permissions/roles"
        elif isinstance(error, (commands.CheckFailure)):
            error_info = "an error with the command checks"
        elif isinstance(error, (commands.CommandNotFound)):
            error_info = "invoking an invalid command"
        else:
            error_info = "an unexpected error"

        logged_com = LoggedComError(
            user=ctx.author,
            command=ctx.command.qualified_name if ctx.command else "UNKNOWN",
            msg_id=ctx.message.id,
            channel=ctx.channel,
            guild=ctx.guild,
            log_content=self.log_content,
            content=ctx.message.content,
            error_info=error_info,
        )

        log.info(logged_com)
        self.log_cache.append(logged_com)
        if self.channel_logger:
            self.channel_logger.add_command(logged_com)

    def cache_size(self) -> int:
        return sum(sys.getsizeof(i) for i in self.log_cache)

    def get_track_start(self) -> str:
        if len(self.log_cache) == 100_000:  # max size
            return "Max log size reached. Only the last 100 000 commands are stored."

        if discord.__version__.startswith("1"):
            ago = humanize_timedelta(timedelta=datetime.datetime.utcnow() - self.load_time)
        else:
            ago = humanize_timedelta(timedelta=discord.utils.utcnow() - self.load_time)
        return f"Log started {ago} ago."

    def log_list_error(self, e):
        log.exception(
            "Something went wrong processing a command. See below for more info.", exc_info=e
        )

    @commands.Cog.listener()
    async def on_command_completion(self, ctx: commands.Context):
        log.trace("command completion received for %s", ctx.command.qualified_name)
        try:
            if self.log_content is None:
                self.log_content = await self.config.log_content()

            self.log_com(ctx)
        except Exception as e:
            self.log_list_error(e)

    @commands.Cog.listener()
    async def on_command_error(self, ctx: commands.Context, error: commands.CommandError):
        log.trace("command error received: %s", error)
        try:
            if self.log_content is None:
                self.log_content = await self.config.log_content()

            self.log_ce(ctx, error)
        except Exception as e:
            self.log_list_error(e)

    @commands.Cog.listener()
    async def on_interaction(self, inter: "Interaction"):
        log.trace("received interaction %s", inter)
        try:
            if inter.data is None:
                return

            if inter.type in (InteractionType.autocomplete, InteractionType.ping):
                log.trace("skipping logging of %s - type is %s", inter, inter.type)
                return
            elif inter.type == InteractionType.application_command:
                if inter.command is None:
                    return
                type = inter.data.get("type")
                target_id = inter.data.get("target_id")

                if target_id:
                    target = self.bot.get_user(target_id)
                    if target is None:
                        try:
                            target = inter.channel.get_partial_message(target_id)
                        except AttributeError:
                            target = None
                else:
                    target = None

                log_obj = LoggedAppCom(
                    author=inter.user,
                    com_name=inter.command.name,
                    channel=inter.channel,
                    guild=inter.guild,
                    app_type=type,
                    target=target,
                )

            elif inter.type == InteractionType.component:
                log.trace("skipping logging of %s - type is %s", inter, inter.type)
                # TODO: add support for component interaction
                return

            elif inter.type == InteractionType.modal_submit:
                log.trace("skipping logging of %s - type is %s", inter, inter.type)
                # TODO: MAYBE add support for modals
                return

            else:  # we should never get here
                log.warning(
                    "Skipping logging of %s - unknown type - type is %s. Please report this to"
                    " Vexed, it should never happen.",
                    inter,
                    inter.type,
                )
                return

            log.info(log_obj)
            self.log_cache.append(log_obj)
            if self.channel_logger:
                self.channel_logger.add_command(log_obj)
        except Exception as e:
            self.log_list_error(e)

    @commands.command(hidden=True)
    async def cmdloginfo(self, ctx: commands.Context):
        main = await format_info(ctx, self.qualified_name, self.__version__)
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

    @commands.guild_only()
    @cmdlog.command()
    async def channel(self, ctx: commands.Context, channel: Optional[TextChannel]):
        """Set the channel to send logs to, this is optional.

        Run the comand without a channel to stop sending.

        **Example:**
        - `[p]cmdlog channel #com-log` - set the log channel to #com-log
        - `[p]cmdlog channel` - stop sending logs
        """
        # guild only check
        if TYPE_CHECKING:
            assert isinstance(ctx.me, discord.Member)

        if channel is None:
            await self.config.log_channel.set(None)
            if self.channel_logger:
                self.channel_logger.stop()
                self.channel_logger = None
            await ctx.send(
                "Reset, logs will not be sent to a Discord channel. You can always access them "
                "though the other commands in this group.\n\n If you meant to set the channel, "
                f"do `{ctx.clean_prefix}cmdlog channel #your-channel-here`"
            )
            return

        if channel.permissions_for(ctx.me).send_messages is False:
            return await ctx.send(
                "I can't do that because I don't have send message permissions in that channel."
            )

        await self.config.log_channel.set(channel.id)
        if self.channel_logger:
            self.channel_logger.stop()
        self.channel_logger = ChannelLogger(self.bot, channel)
        self.channel_logger.start()
        await ctx.send(
            f"Command logs will now be sent to {channel.mention}. Please be aware "
            "of the privacy implications of permanently logging End User Data (unlike the other "
            "logs in this cog, which are either in memory or part of logging rotation) and ensure "
            "permissions for accessing this channel are restricted - you are responsible. Logging "
            "this End User Data is a grey area in Discord's Terms of Service.\n\n"
            "To avoid rate limits, **logs will only be sent every 60 seconds**."
        )

    @cmdlog.command()
    async def cache(self, ctx: commands.Context):
        """Show the size of the internal command cache."""
        cache_bytes = self.cache_size()
        log.debug(f"Cache size is exactly {cache_bytes} bytes.")
        cache_size = humanize_bytes(cache_bytes, 1)
        cache_count = humanize_number(len(self.log_cache))
        await ctx.send(f"\nCache size: {cache_size} with {cache_count} commands.")

    @commands.bot_has_permissions(attach_files=True)
    @cmdlog.command()
    async def full(self, ctx: commands.Context):
        """Upload all the logs that are stored in the cache."""
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [f"[{i.time}] {i}" for i in self.log_cache]
        log_str = f"Generated at {now}.\n" + "\n".join(logs)
        fp = StringIO()
        fp.write(log_str)
        size = fp.tell()
        if ctx.guild:
            max_size = ctx.guild.filesize_limit
        else:
            max_size = 8388608
        if size > max_size:
            await ctx.send(
                "Hmm, it looks like you've got some seriously long logs! They're over "
                "the file size limit. Reset with `[p]reload cmdlog` or choose a different user."
            )
            return
        fp.seek(0)

        await ctx.send(
            "Here is the command log. " + self.get_track_start(),
            file=discord.File(fp, "cmdlog.txt"),  # type:ignore
        )
        fp.close()

    @commands.bot_has_permissions(attach_files=True)
    @cmdlog.command()
    async def user(self, ctx: commands.Context, user_id: int):
        """
        Upload all the logs that are stored for a specific User ID in the cache.

        **Example:**
        - `[p]cmdlog user 418078199982063626`
        """
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [f"[{i.time}] {i}" for i in self.log_cache if i.user.id == user_id]
        log_str = f"Generated at {now} for user {user_id}.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that user."
        )  # happy doing this because of file previews

        fp = StringIO()
        fp.write(log_str)
        size = fp.tell()
        if ctx.guild:
            max_size = ctx.guild.filesize_limit
        else:
            max_size = 8388608
        if size > max_size:
            await ctx.send(
                "Hmm, it looks like you've got some seriously long logs! They're over "
                "the file size limit. Reset with `[p]reload cmdlog` or choose a different user."
            )
            return
        fp.seek(0)

        await ctx.send(
            f"Here is the command log for user {user_id}. " + self.get_track_start(),
            file=discord.File(fp, f"cmdlog_{user_id}.txt"),  # type:ignore
        )
        fp.close()

    @commands.bot_has_permissions(attach_files=True)
    @cmdlog.command(aliases=["guild"])
    async def server(self, ctx: commands.Context, server_id: int):
        """
        Upload all the logs that are stored for for a specific server ID in the cache.

        **Example:**
        - `[p]cmdlog server 527961662716772392`
        """
        now = datetime.datetime.now().strftime(TIME_FORMAT)
        logs = [f"[{i.time}] {i}" for i in self.log_cache if i.guild and i.guild.id == server_id]

        log_str = f"Generated at {now} for server {server_id}.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that server."
        )  # happy doing this because of file previews
        fp = StringIO()
        fp.write(log_str)
        size = fp.tell()
        if ctx.guild:
            max_size = ctx.guild.filesize_limit
        else:
            max_size = 8388608
        if size > max_size:
            await ctx.send(
                "Hmm, it looks like you've got some seriously long logs! They're over "
                "the file size limit. Reset with `[p]reload cmdlog` or choose a different server."
            )
            return
        fp.seek(0)

        await ctx.send(
            f"Here is the command log for server {server_id}. " + self.get_track_start(),
            file=discord.File(fp, f"cmdlog_{server_id}.txt"),  # type:ignore
        )
        fp.close()

    @commands.bot_has_permissions(attach_files=True)
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
        logs = [f"[{i.time}] {i}" for i in self.log_cache if i.command.startswith(command)]

        log_str = f"Generated at {now} for command '{command}'.\n" + (
            "\n".join(logs) or "It looks like I didn't find anything for that command."
        )  # happy doing this because of file previews
        fp = StringIO()
        fp.write(log_str)
        size = fp.tell()
        if ctx.guild:
            max_size = ctx.guild.filesize_limit  # type:ignore
        else:
            max_size = 8388608
        if size > max_size:
            await ctx.send(
                "Hmm, it looks like you've got some seriously long logs! They're over "
                "the file size limit. Reset with `[p]reload cmdlog` or choose a different command."
            )
            return
        fp.seek(0)

        await ctx.send(
            f"Here is the command log for command '{command}'. " + self.get_track_start(),
            file=discord.File(fp, f"cmdlog_{command.replace(' ', '_')}.txt"),  # type:ignore
        )
        fp.close()
