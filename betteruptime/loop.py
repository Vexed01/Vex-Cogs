import asyncio
import datetime
import logging
from time import time
from typing import Dict

from discord.ext import tasks
from redbot.core.bot import Red
from redbot.core.config import Config

from betteruptime.consts import INF

_log = logging.getLogger("red.vexed.betteruptime.loop")


class BetterUptimeLoop:
    def __init__(self):
        self.bot: Red

        self.config: Config

        self.last_known_ping: float
        self.last_ping_change: float

        self.fist_load: float

        self.cog_loaded_cache: Dict[str, int]
        self.connected_cache: Dict[str, int]

        asyncio.create_task(self.start())

    async def start(self):
        await self.bot.wait_until_red_ready()

        self.last_known_ping: float = self.bot.latency
        self.last_ping_change = time()

        self.first_load = await self.config.first_load()
        # want to make sure its actually written
        if self.first_load is None:
            await self.config.first_load.set(time())
            self.first_load = time()

        _log.debug("Waiting a bit to allow for previous unload to clean up (assuming reload)...")
        await asyncio.sleep(2)  # assume reload - wait for unloading to be able to clean up properly
        _log.debug("Setting up...")
        self.cog_loaded_cache = await self.config.cog_loaded()
        self.connected_cache = await self.config.connected()

        _log.info("BetterUptime has been initialized. Waiting for some uptime to occur...")

        await asyncio.sleep(15)
        self.uptime_loop.start()

        await asyncio.sleep(1)
        self.config_loop.start()

        _log.info("BetterUptime is now fully running.")

    async def write_to_config(self, final=False):
        if self.cog_loaded_cache:  # dont want to write if the cache is empty
            await self.config.cog_loaded.set(self.cog_loaded_cache)
        if self.connected_cache:
            await self.config.connected.set(self.connected_cache)

        if final:
            _log.info("BetterUptime is fully unloaded.")
        else:
            _log.debug("Wrote local cache to config.")

    @tasks.loop(seconds=15)  # 15 seconds is basically guaranteed to catch all, heartbeats are ~41 secs atm
    async def uptime_loop(self):
        _log.debug("Loop started")
        utcdatetoday = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        utcdateyesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        utcdateyesterday = utcdateyesterday.strftime("%Y-%m-%d")

        # === COG LOADED ===

        # im sure the indentation could be reduced here
        try:
            self.cog_loaded_cache[utcdatetoday] += 15
        except KeyError:
            # we need to top up both today and yesterday with their respective amounts

            now = datetime.datetime.now(datetime.timezone.utc)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            just_after_midnight = (now - midnight).seconds

            if just_after_midnight > 15:
                self.cog_loaded_cache[utcdatetoday] = 15
            else:
                just_before_midnight = 15 - just_after_midnight
                self.cog_loaded_cache[utcdatetoday] = just_after_midnight

                try:
                    self.cog_loaded_cache[utcdateyesterday] += just_before_midnight
                except KeyError:
                    pass

        # === CONNECTED ===
        # bit of background info here: the latency is updated every heartbeat and if the heartbeat fails the latency
        # is infinity (INF)

        current_latency = self.bot.latency

        # the latency has changed and it's not infinity (couldn't connect)
        if current_latency != self.last_known_ping:
            if current_latency != INF:
                since_last = time() - self.last_ping_change

                try:
                    self.connected_cache[utcdatetoday] += since_last
                except KeyError:
                    # we need to top up both today and yesterday with their respective amounts

                    now = datetime.datetime.now(datetime.timezone.utc)
                    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    just_after_midnight = (now - midnight).seconds

                    if just_after_midnight > since_last:
                        self.connected_cache[utcdatetoday] = since_last
                    else:
                        just_before_midnight = since_last - just_after_midnight
                        self.connected_cache[utcdatetoday] = just_after_midnight

                        try:
                            self.connected_cache[utcdateyesterday] += just_before_midnight
                        except KeyError:
                            pass
            self.last_known_ping = current_latency
            self.last_ping_change = time()

    @tasks.loop(seconds=60)
    async def config_loop(self):
        await self.write_to_config()
