import asyncio
import datetime
import logging
from time import time

from vexcogutils.loop import VexLoop

from .abc import MixinMeta
from .consts import INF

_log = logging.getLogger("red.vex.betteruptime.loop")


class BULoop(MixinMeta):
    def __init__(self) -> None:
        asyncio.create_task(self.initialise())

        self.main_loop_meta = VexLoop("BetterUptime Main Loop", 15.0)
        self.main_loop = asyncio.create_task(self.betteruptime_main_loop())

        self.conf_loop_meta = VexLoop("BetterUptime Config Loop", 60.0)
        self.conf_loop = asyncio.create_task(self.betteruptime_conf_loop())

    async def initialise(self) -> None:
        await self.bot.wait_until_red_ready()

        self.last_known_ping = self.bot.latency
        self.last_ping_change = time()

        self.first_load = await self.config.first_load()
        # want to make sure its actually written
        if self.first_load is None:
            await self.config.first_load.set(time())
            self.first_load = time()

        _log.debug("Waiting a bit to allow for previous unload to clean up (assuming reload)...")
        await asyncio.sleep(2)  # wait for unloading to be able to clean up properly
        _log.debug("Setting up...")
        self.cog_loaded_cache = await self.config.cog_loaded()
        self.connected_cache = await self.config.connected()

        _log.info("BetterUptime has been initialised and is now running.")

        self.ready = True

    async def betteruptime_main_loop(self):
        while not self.ready:
            await asyncio.sleep(1)

        await asyncio.sleep(15)  # wait for initial uptime to occur

        while True:
            _log.debug("Main BetterUptime loop has started next iteration")
            try:
                self.main_loop_meta.iter_start()
                await self.update_uptime()
                self.main_loop_meta.iter_finish()
            except Exception as e:
                self.main_loop_meta.iter_error(e)
                _log.exception(
                    "Something went wrong in the main BetterUptime loop. The loop will try again "
                    "in 15 seconds. Please report this to Vexed."
                )

            await self.main_loop_meta.sleep_until_next()

    async def betteruptime_conf_loop(self):
        while not self.ready:
            await asyncio.sleep(1)

        await asyncio.sleep(65)  # wait for main loop to run for a minute before writing anything

        while True:
            _log.debug("Config BetterUptime loop has started next iteration")
            try:
                self.conf_loop_meta.iter_start()
                await self.update_uptime()
                self.conf_loop_meta.iter_finish()
            except Exception as e:
                self.conf_loop_meta.iter_error(e)
                _log.exception(
                    "Something went wrong in the conf BetterUptime loop. The loop will try again "
                    "in 60 seconds. Please report this to Vexed."
                )

            await self.conf_loop_meta.sleep_until_next()

    async def write_to_config(self, final=False) -> None:
        if self.cog_loaded_cache:  # dont want to write if the cache is empty
            await self.config.cog_loaded.set(self.cog_loaded_cache)
        if self.connected_cache:
            await self.config.connected.set(self.connected_cache)

        if final:
            _log.info("BetterUptime is fully unloaded.")
        else:
            _log.debug("Wrote local cache to config.")

    async def update_uptime(self):
        utcdatetoday = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        utcdateyesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(
            days=1
        )
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
        # bit of background info here: the latency is updated every heartbeat and if the heartbeat
        # fails the latency is infinity (INF)

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
