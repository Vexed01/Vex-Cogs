import asyncio
import datetime
import json
import logging
import time
from typing import Dict, Set

import discord
import pandas
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils import AsyncIter
from vexcogutils import format_help, format_info
from vexcogutils.loop import VexLoop

from stattrack.abc import CompositeMetaClass
from stattrack.commands import StatTrackCommands

_log = logging.getLogger("red.vexed.stattrack")


def snapped_utcnow():
    return datetime.datetime.utcnow().replace(microsecond=0, second=0)


class StatTrack(commands.Cog, StatTrackCommands, metaclass=CompositeMetaClass):
    """BETA COG: StatTrack (Stat Tracking)"""

    __version__ = "0.0.0"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.df_cache = None
        self.loop = None
        self.loop_meta = None
        self.last_loop_time = None

        self.cmd_count = 0
        self.msg_count = 0

        self.config = Config.get_conf(self, identifier=418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(main_df={})

        # if 418078199982063626 in bot.owner_ids:  # for main release
        bot.add_dev_env_value("stattrack", lambda _: self)

        asyncio.create_task(self.async_init())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        if self.loop:
            self.loop.cancel()
        # if 418078199982063626 in self.bot.owner_ids:  # for main release
        self.bot.remove_dev_env_value("stattrack")

    async def async_init(self) -> None:
        await self.bot.wait_until_red_ready()
        df_conf = await self.config.main_df()
        if df_conf:
            self.df_cache = pandas.read_json(json.dumps(df_conf), orient="split")
            assert isinstance(self.df_cache, pandas.DataFrame)
        else:
            self.df_cache = pandas.DataFrame()

        self.loop = asyncio.create_task(self.stattrack_loop())
        self.loop_meta = VexLoop("StatTrack loop", 60.0)

    @commands.command(hidden=True)
    async def stattrackinfo(self, ctx: commands.Context):
        await ctx.send(
            await format_info(
                self.qualified_name,
                self.__version__,
                loops=[self.loop_meta] if self.loop_meta else [],
                extras={"Loop time": f"{self.last_loop_time} seconds"},  # type:ignore
            )
        )

    @commands.command(hidden=True)
    async def stattrackloop(self, ctx: commands.Context):
        if not self.loop_meta:
            return await ctx.send("Loop not running yet")
        await ctx.send(embed=self.loop_meta.get_debug_embed())

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author != self.bot.user:
            self.msg_count += 1

    @commands.Cog.listener()
    async def on_command(self, ctx: commands.Context):
        if ctx.author != self.bot.user:
            self.cmd_count += 1

    async def stattrack_loop(self):
        while True:
            _log.debug("StatTrack loop has started next iteration")
            try:
                self.loop_meta.iter_start()
                await self.update_stats()
                self.loop_meta.iter_finish()
            except Exception as e:
                self.loop_meta.iter_error(e)
                _log.exception(
                    "Something went wrong in the StatTrack loop. The loop will try again "
                    "shortly. Please report this to Vexed."
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
        await self.config.main_df.set(json.loads(self.df_cache.to_json(orient="split")))

        end = time.monotonic()

        looptime = round(end - start, 1)

        _log.debug(f"Loop finished in {looptime} seconds")
        self.last_loop_time = looptime
