import asyncio
import datetime
import json
import logging
import time
from asyncio.events import AbstractEventLoop
from typing import Dict, Optional, Set

import discord
import pandas
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from redbot.core.utils import AsyncIter

from stattrack.abc import CompositeMetaClass
from stattrack.commands import StatTrackCommands
from stattrack.plot import StatPlot

from .vexutils import format_help, format_info
from .vexutils.loop import VexLoop
from .vexutils.sqldriver import PandasSQLiteDriver

_log = logging.getLogger("red.vexed.stattrack")


def snapped_utcnow():
    return datetime.datetime.utcnow().replace(microsecond=0, second=0)


class StatTrack(commands.Cog, StatTrackCommands, StatPlot, metaclass=CompositeMetaClass):
    """
    Track your bot's metrics and view them in Discord.
    Requires no external setup, so uses Red's config. This cog will use around 150KB per day.

    Commands will output as a graph.
    Data can also be exported with `[p]stattrack export` into a few different formats.
    """

    __version__ = "1.4.0"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.do_write: Optional[bool] = None

        self.cmd_count = 0
        self.msg_count = 0

        self.config = Config.get_conf(self, identifier=418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(main_df={})

        self.last_loop_time = "Loop not ran yet"

        self.driver = PandasSQLiteDriver(bot, type(self).__name__, "timeseries.db")

        if 418078199982063626 in bot.owner_ids:  # type:ignore
            bot.add_dev_env_value("stattrack", lambda _: self)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        if self.loop:
            self.loop.cancel()

        self.plot_executor.shutdown()
        self.driver.sql_executor.shutdown()

        try:
            self.bot.remove_dev_env_value("stattrack")
        except KeyError:
            pass

    async def async_init(self) -> None:
        if await self.config.version() != 2:
            self.do_write = True
            _log.info("Migrating StatTrack config.")
            df_conf = await self.config.main_df()

            if df_conf:  # needs migration
                self.df_cache = pandas.read_json(json.dumps(df_conf), orient="split", typ="frame")
                await self.migrate_v1_to_v2(df_conf)
            else:  # new install
                self.df_cache = pandas.DataFrame()
            assert self.df_cache is not None
            await self.driver.write(self.df_cache)
            await self.config.version.set(2)
            _log.info("Done.")
        else:
            self.do_write = False
            self.df_cache = await self.driver.read()

        self.loop = self.bot.loop.create_task(self.stattrack_loop())
        self.loop_meta = VexLoop("StatTrack loop", 60.0)

    async def migrate_v1_to_v2(self, data: dict) -> None:
        assert isinstance(self.bot.loop, AbstractEventLoop)
        # a big dataset can take 1 second to write as JSON, so better make it not blocking

        def backup() -> None:
            with open(cog_data_path(self) / "v1_to_v2_backup.json", "w") as fp:
                json.dump(data, fp)

        await self.bot.loop.run_in_executor(None, backup)

        await self.config.version.set(2)

        await self.config.main_df.clear()

    @commands.command(hidden=True)
    async def stattrackinfo(self, ctx: commands.Context):
        assert self.df_cache is not None
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
        )

    @commands.command(hidden=True)
    async def stattrackloop(self, ctx: commands.Context):
        if not self.loop_meta:
            return await ctx.send("Loop not running yet")
        await ctx.send(embed=self.loop_meta.get_debug_embed())

    @commands.command(hidden=True)
    async def stattrackdev(self, ctx: commands.Context):
        """Add a dev env var called `stattrack`. Will be removed on cog unload."""
        self.bot.add_dev_env_value("stattrack", lambda _: self)
        await ctx.send("Added env var `stattrack`. Will be removed on cog unload.")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            self.msg_count += 1

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.author != self.bot.user:
            self.cmd_count += 1

    async def stattrack_loop(self):
        await asyncio.sleep(1)

        await self.bot.wait_until_red_ready()

        while True:
            _log.debug("StatTrack loop has started next iteration")
            try:
                self.loop_meta.iter_start()
                await self.update_stats()
                self.loop_meta.iter_finish()
            except Exception as e:
                _log.exception(
                    "Something went wrong in the StatTrack loop. The loop will try again "
                    "shortly.",
                    exc_info=e,
                )

            await self.loop_meta.sleep_until_next()

    async def update_stats(self):
        now = snapped_utcnow()
        if now == self.df_cache.last_valid_index():  # just reloaded and this min's data collected
            _log.debug("Skipping this loop - cog was likely recently reloaded")
            return
        df = pandas.DataFrame(index=[snapped_utcnow()])
        start = time.monotonic()
        data = {}

        try:
            latency = round(self.bot.latency * 1000)
            if latency > 1000:  # somethings up... lets not track stats
                return
            df["ping"] = latency
        except OverflowError:  # ping is INF so not connected, no point in updating
            return
        data["users_unique"] = len(self.bot.users)
        data["guilds"] = len(self.bot.guilds)
        data["users_total"] = 0
        data["channels_total"] = 0
        data["channels_text"] = 0
        data["channels_voice"] = 0
        data["channels_cat"] = 0
        data["channels_stage"] = 0
        data["command_count"] = self.cmd_count
        data["message_count"] = self.msg_count
        self.cmd_count, self.msg_count = 0, 0

        count: Dict[str, Set[int]] = {  # can't use defaultdict, got to have these set
            "status_online": set(),
            "status_idle": set(),
            "status_offline": set(),
            "status_dnd": set(),
            "users_humans": set(),
            "users_bots": set(),
        }
        guild: discord.Guild
        member: discord.Member
        async for guild in AsyncIter(self.bot.guilds):
            async for member in AsyncIter(guild.members):
                data["users_total"] += 1
                count[f"status_{member.raw_status}"].add(member.id)
                if member.bot:
                    count["users_bots"].add(member.id)
                else:
                    count["users_humans"].add(member.id)
            data["channels_total"] += len(guild.channels)
            data["channels_text"] += len(guild.text_channels)
            data["channels_voice"] += len(guild.voice_channels)
            data["channels_cat"] += len(guild.categories)
            data["channels_stage"] += len(guild.stage_channels)

        for k, v in count.items():
            df[k] = len(v)

        for k, v in data.items():
            df[k] = v

        self.df_cache = self.df_cache.append(df)

        end = time.monotonic()
        main_time = round(end - start, 1)
        _log.debug(f"Loop finished in {main_time} seconds")

        if self.do_write is True:
            start = time.monotonic()
            await self.driver.write(self.df_cache)
            end = time.monotonic()
            save_time = round(end - start, 3)
            _log.debug(f"SQLite wrote in {save_time} seconds")
            self.do_write = False
        else:
            start = time.monotonic()
            await self.driver.append(df)
            end = time.monotonic()
            save_time = round(end - start, 3)
            _log.debug(f"SQLite appended in {save_time} seconds")

        total_time = main_time + save_time

        if total_time > 30.0:
            # TODO: only warn once + send to owners
            _log.warning(
                "StatTrack loop took a while. This means that it's using lots of resources on "
                "this machine. You might want to consider unloading or removing the cog. There "
                "is also a high chance of some datapoints on the graphs being skipped."
                + f"\nMain loop: {main_time}s, Data saving: {save_time}s so total time is "
                + str(total_time)
            )

        self.last_loop_time = f"{total_time} seconds ({main_time}, {save_time})"
