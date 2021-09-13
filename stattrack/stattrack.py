import asyncio
import datetime
import json
import logging
import time
from asyncio.events import AbstractEventLoop
from typing import Dict, Optional, Set

import discord
import pandas
import sentry_sdk
import vexcogutils
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from redbot.core.utils import AsyncIter
from vexcogutils import format_help, format_info
from vexcogutils.loop import VexLoop
from vexcogutils.meta import out_of_date_check
from vexcogutils.sqldriver import PandasSQLiteDriver

from stattrack.abc import CompositeMetaClass
from stattrack.commands import StatTrackCommands
from stattrack.plot import StatPlot

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

    __version__ = "1.3.1"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.df_cache = None
        self.loop = None
        self.loop_meta = None
        self.last_loop_time = None

        self.do_write: Optional[bool] = None

        self.cmd_count = 0
        self.msg_count = 0

        self.config = Config.get_conf(self, identifier=418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(main_df={})

        self.driver = PandasSQLiteDriver(bot, type(self).__name__, "timeseries.db")

        asyncio.create_task(self.async_init())

        if 418078199982063626 in bot.owner_ids:  # type:ignore
            bot.add_dev_env_value("stattrack", lambda _: self)

        # =========================================================================================
        # NOTE: IF YOU ARE EDITING MY COGS, PLEASE ENSURE SENTRY IS DISBALED BY FOLLOWING THE INFO
        # IN async_init(...) BELOW (SENTRY IS WHAT'S USED FOR TELEMETRY + ERROR REPORTING)
        self.sentry_hub: Optional[sentry_sdk.Hub] = None
        # =========================================================================================

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

        if self.sentry_hub and self.sentry_hub.client:
            self.sentry_hub.end_session()
            self.sentry_hub.client.close()  # type:ignore

        try:
            self.bot.remove_dev_env_value("stattrack")
        except KeyError:
            pass

    async def async_init(self) -> None:
        await self.bot.wait_until_red_ready()
        await out_of_date_check("stattrack", self.__version__)

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

        self.loop = asyncio.create_task(self.stattrack_loop())
        self.loop_meta = VexLoop("StatTrack loop", 60.0)

        # =========================================================================================
        # TO DISABLE SENTRY FOR THIS COG (EG IF YOU ARE EDITING THIS COG) EITHER DISABLE SENTRY
        # WITH THE `[p]vextelemetry` COMMAND, OR UNCOMMENT THE LINE BELOW, OR REMOVE IT COMPLETELY:
        # return

        while vexcogutils.sentryhelper.ready is False:
            await asyncio.sleep(0.1)

        await vexcogutils.sentryhelper.maybe_send_owners("stattrack")

        if vexcogutils.sentryhelper.sentry_enabled is False:
            _log.debug("Sentry detected as disabled.")
            return

        _log.debug("Sentry detected as enabled.")
        self.sentry_hub = await vexcogutils.sentryhelper.get_sentry_hub(
            "stattrack", self.__version__
        )
        # =========================================================================================

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.bot.on_command_error(ctx, error, unhandled_by_cog=True)  # type:ignore

        if self.sentry_hub is None:  # sentry disabled
            return

        with self.sentry_hub:
            sentry_sdk.add_breadcrumb(
                category="command", message="Command used was " + ctx.command.qualified_name
            )
            try:
                e = error.original
            except AttributeError:
                e = error
            sentry_sdk.capture_exception(e)
            _log.debug("Above exception successfully reported to Sentry")

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
        while True:
            _log.debug("StatTrack loop has started next iteration")
            try:
                self.loop_meta.iter_start()
                await self.update_stats()
                self.loop_meta.iter_finish()
            except Exception as e:
                self.loop_meta.iter_error(e, self.sentry_hub)
                _log.exception(
                    "Something went wrong in the StatTrack loop. The loop will try again "
                    "shortly."
                )

            await self.loop_meta.sleep_until_next()

    async def update_stats(self):
        if self.sentry_hub:
            with self.sentry_hub:
                master_trans = sentry_sdk.start_transaction(
                    op="loop",
                    name="StatTrack loop",
                    description="Main stats loop for collecting, processing and saving data.",
                )
            prep_trans = master_trans.start_child(
                op="prep", description="Preparation for stats collection"
            )

        now = snapped_utcnow()
        if now == self.df_cache.last_valid_index():  # just reloaded and this min's data collected
            _log.debug("Skipping this loop - cog was likely recently reloaded")
            return
        df = pandas.DataFrame(index=[snapped_utcnow()])
        start = time.monotonic()
        data = {}

        if self.sentry_hub:
            prep_trans.finish()
            data_trans = master_trans.start_child(op="data_collect", description="Data collection")
            data1_trans = data_trans.start_child(
                op="data_collect_1", description="Non-loop data collection"
            )

        await asyncio.sleep(0)

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

        if self.sentry_hub:
            data1_trans.finish()
            data2_trans = data_trans.start_child(
                op="data_collect_2", description="Loop data collection"
            )

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

        if self.sentry_hub:
            data2_trans.finish()
            data_trans.finish()
            format_trans = master_trans.start_child(
                op="data_conversion", description="Data format conversion"
            )

        for k, v in count.items():
            df[k] = len(v)

        for k, v in data.items():
            df[k] = v

        if self.sentry_hub:
            format_trans.finish()
            save_trans = master_trans.start_child(op="save", description="Save data")

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

        if self.sentry_hub:
            save_trans.finish()
            master_trans.set_status("ok")
            master_trans.finish()

        total_time = main_time + save_time

        if total_time > 30.0:
            # TODO: only warn once + send to owners
            _log.warning(
                "StatTrack loop took a while. This means that it's using lots of resources on "
                "this machine. You might want to consider unloading or removing the cog. There "
                "is also a high chance of some datapoints on the graphs being skipped."
                + f"\nMain loop: {main_time}s, Data saving: {save_time}s so total time is "
                + total_time
            )

        self.last_loop_time = f"{total_time} seconds ({main_time}, {save_time})"
