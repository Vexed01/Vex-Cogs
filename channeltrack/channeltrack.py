import asyncio
import datetime
import logging
import time
from collections import defaultdict
from typing import Dict, Optional, Tuple

import discord
import pandas
from redbot.core import Config, commands
from redbot.core.bot import Red

from .abc import CompositeMetaClass
from .commands import ChannelTrackCommands
from .plot import StatPlot
from .table import TableType
from .vexutils import format_help, format_info
from .vexutils.chat import humanize_bytes
from .vexutils.loop import VexLoop
from .vexutils.sqldriver import PandasSQLiteDriver

_log = logging.getLogger("red.vex.channeltrack")


def snapped_utcnow():
    return datetime.datetime.utcnow().replace(microsecond=0, second=0)


class ChannelTrack(commands.Cog, ChannelTrackCommands, StatPlot, metaclass=CompositeMetaClass):
    """
    Track your bot's metrics and view them in Discord.
    Requires no external setup, so uses Red's config. This cog will use around 150KB per day.

    Commands will output as a graph.
    Data can also be exported with `[p]channeltrack export` into a few different formats.
    """

    __version__ = "1.8.0"
    __author__ = "Vexed#9000"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config = Config.get_conf(self, identifier=418078199982063626, force_registration=True)
        self.config.register_global(version=1, opted_in_guilds=[527961662716772392])

        self.driver = PandasSQLiteDriver(self.bot, self.qualified_name, "database.sqlite")

        bot.add_dev_env_value("channeltrack", lambda _: self)

        self.reset_counter()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        if self.loop:
            self.loop.cancel()

        self.plot_executor.shutdown(wait=False)
        self.driver.sql_executor.shutdown(wait=False)

        try:
            self.bot.remove_dev_env_value("channeltrack")
        except KeyError:
            pass

    async def async_init(self) -> None:
        self.opted_in_guilds = await self.config.opted_in_guilds()
        print(self.opted_in_guilds)

        self.loop = self.bot.loop.create_task(self.channeltrack_loop())

    def reset_counter(self) -> Tuple[Dict[int, Dict[int, int]], Dict[int, Dict[int, int]]]:
        if hasattr(self, "msg_count"):
            ret_msg = self.msg_count
            ret_cmd = self.cmd_count
        else:
            ret_msg = {}
            ret_cmd = {}

        self.msg_count = defaultdict(lambda: defaultdict(lambda: 0))  # type:ignore
        self.cmd_count = defaultdict(lambda: defaultdict(lambda: 0))  # type:ignore

        return ret_msg, ret_cmd  # type:ignore

    def get_table_name(
        self,
        coms_or_msg: TableType,
        *,
        ctx: Optional[commands.Context] = None,
        guild_id: Optional[int] = None,
    ) -> str:
        if ctx is not None:
            guild_id = ctx.guild.id  # type:ignore
        elif guild_id is None:
            raise ValueError("ctx or guild_id must be provided")

        suffix = "com" if coms_or_msg == TableType.COMMANDS else "msg"
        return str(guild_id) + "_" + suffix

    async def append_or_write_data(self, df: pandas.DataFrame, table: str) -> None:
        """Append or write a new set of data to the databse."""
        try:
            await self.driver.append(df, table)  # try a normal append, could fail if not exist
            # or if columns don't match (ie new channel)
            _log.debug("Appended data to %s", table)
        except Exception:  # yes i should be more specific
            try:
                old = await self.driver.read(table)  # see if there's anything actually there
                if old.empty:
                    old = None
            except Exception:
                old = None

            if old is not None:
                # merge old with new and handle potential new columns
                df = pandas.concat([old, df], axis=0)

            await self.driver.write(df, table)
            _log.debug("Wrote data to %s", table)

    @commands.command(hidden=True)
    async def channeltrackinfo(self, ctx: commands.Context):
        await ctx.send(
            await format_info(
                ctx,
                self.qualified_name,
                self.__version__,
                loops=[self.loop_meta] if self.loop_meta else [],
                extras={
                    "Loop time": f"{self.last_loop_time}",
                },
            )
            + f"\nDisk usage (SQLite database): {humanize_bytes(self.driver.storage_usage())}"
        )

    @commands.command(hidden=True)
    async def channeltrackloop(self, ctx: commands.Context):
        if not self.loop_meta:
            return await ctx.send("Loop not running yet")
        await ctx.send(embed=self.loop_meta.get_debug_embed())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.guild.id not in self.opted_in_guilds or await self.bot.cog_disabled_in_guild(
            self, message.guild
        ):
            return
        # want to include all messages regardless if from a bot

        self.msg_count[message.guild.id][message.channel.id] += 1

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if (ctx.guild.id) not in self.opted_in_guilds or await self.bot.cog_disabled_in_guild(
            self, ctx.guild
        ):
            return
        # want to include all messages regardless if from a bot

        self.cmd_count[ctx.guild.id][ctx.channel.id] += 1

    async def channeltrack_loop(self):
        await self.bot.wait_until_red_ready()

        _log.debug("ChannelTrack loop is waiting 10 mins for initial data")
        # await asyncio.sleep(600)  # 10 min
        await asyncio.sleep(15)

        self.loop_meta = VexLoop("ChannelTrack loop", 600.0)

        while True:
            _log.debug("ChannelTrack loop has started next iteration")
            try:
                self.loop_meta.iter_start()
                await self.update_stats()
                self.loop_meta.iter_finish()
            except Exception as e:
                self.loop_meta.iter_error(e)
                _log.exception(
                    "Something went wrong in the ChannelTrack loop. The loop will try again "
                    "shortly.",
                    exc_info=e,
                )

            await self.loop_meta.sleep_until_next()

    async def update_stats(self):
        now = snapped_utcnow()
        start = time.monotonic()

        no_msg_guilds = self.opted_in_guilds.copy()
        no_cmd_guilds = self.opted_in_guilds.copy()

        all_msg, all_cmd = self.reset_counter()

        for guild_id, data in all_msg.items():
            no_msg_guilds.remove(guild_id)
            df = pandas.DataFrame(data=data, index=[now])
            await self.append_or_write_data(
                df=df,
                table=self.get_table_name(TableType.MESSAGES, guild_id=guild_id),
            )

        for guild_id in no_msg_guilds:  # make sure there is an entry for every guild
            df = pandas.DataFrame(data={}, index=[now])
            await self.append_or_write_data(
                df=df,
                table=self.get_table_name(TableType.MESSAGES, guild_id=guild_id),
            )

        for guild_id, data in all_cmd.items():
            no_cmd_guilds.remove(guild_id)
            df = pandas.DataFrame(data=data, index=[now])
            await self.append_or_write_data(
                df=df,
                table=self.get_table_name(TableType.COMMANDS, guild_id=guild_id),
            )

        for guild_id in no_cmd_guilds:  # make sure there is an entry for every guild
            df = pandas.DataFrame(data={}, index=[now])
            await self.append_or_write_data(
                df=df,
                table=self.get_table_name(TableType.COMMANDS, guild_id=guild_id),
            )

        # i know this is a lot of writes and connections, but as each guild is a table this is
        # needed. i have mentioned this cog is not intended for large bots in the info.json

        end = time.monotonic()

        _log.debug("ChannelTrack loop has finished an iteration in %s seconds", end - start)
