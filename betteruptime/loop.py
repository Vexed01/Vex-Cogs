import asyncio
import datetime
import json
import logging
from time import time
from typing import Dict

import pandas
import sentry_sdk
from vexcogutils.loop import VexLoop

from .abc import MixinMeta
from .consts import INF, SECONDS_IN_DAY

_log = logging.getLogger("red.vex.betteruptime.loop")


class BULoop(MixinMeta):
    def __init__(self) -> None:
        asyncio.create_task(self.initialise())

        self.main_loop = asyncio.create_task(self.betteruptime_main_loop())

    async def initialise(self) -> None:
        await self.bot.wait_until_red_ready()
        _log.debug("[BU SETUP] Starting setup...")

        self.last_known_ping = self.bot.latency
        self.last_ping_change = time()

        self.first_load = await self.config.first_load()
        # want to make sure its actually written
        if self.first_load is None:
            await self.config.first_load.set(time())
            self.first_load = time()

        if await self.config.version() == 1:
            _log.info("Migrating BetterUptime config to new format (1 -> 3)...")
            await self.migrate_v1_to_v3()
            await self.config.version.set(3)
        elif await self.config.version() == 2:
            _log.info("Migrating BetterUptime config to new format (2 -> 3)...")
            await self.migate_v2_to_v3()
            await self.config.version.set(3)
        else:
            self.cog_loaded_cache = pandas.read_json(
                json.dumps(await self.config.cog_loaded()), typ="series"
            )
            self.connected_cache = pandas.read_json(
                json.dumps(await self.config.connected()), typ="series"
            )

        self.ready = True

        _log.debug("[BU SETUP] Config setup finished, waiting to start loops")

    async def migrate_v1_to_v3(self):
        old_cog_loaded = await self.config.cog_loaded()
        old_connected = await self.config.connected()

        partially_converted = {
            datetime.datetime.strptime(k, "%Y-%m-%d"): v for k, v in old_cog_loaded.items()
        }
        self.cog_loaded_cache = pandas.Series(data=partially_converted)

        partially_converted = {
            datetime.datetime.strptime(k, "%Y-%m-%d"): v for k, v in old_connected.items()
        }
        self.connected_cache = pandas.Series(data=partially_converted)

        await self.write_to_config()

    async def migate_v2_to_v3(self):
        # i had bad code when making v2 so config was a mixtre of v1 and v2 format.... congrats me
        old_cog_loaded = await self.config.cog_loaded()
        old_connected = await self.config.connected()

        def convert(data: Dict[str, float]) -> pandas.Series:
            new_data = {}
            for k, v in data.items():
                if "-" in k:
                    time = datetime.datetime.strptime(k, "%Y-%m-%d")
                else:
                    time = datetime.datetime.utcfromtimestamp(float(k) / 1000.0)

                if v > (SECONDS_IN_DAY + 30):  # can happen... dont know why
                    v = SECONDS_IN_DAY

                new_data[time] = v

            return pandas.Series(data=new_data)

        self.cog_loaded_cache = convert(old_cog_loaded)
        self.connected_cache = convert(old_connected)

        await self.write_to_config()

    async def betteruptime_main_loop(self):
        while self.ready is False:
            await asyncio.sleep(0.1)

        await asyncio.sleep(1)

        # making the loop run on the minute every time means i don't need to worry about seconds
        # well, on the minute - 5 sec. it's to make stuff easier in the loop code
        while (round(time() + 5) % 60) != 0:
            await asyncio.sleep(0.1)

        self.main_loop_meta = VexLoop("BetterUptime Main Loop", 60.0)

        _log.debug("[BU SETUP] Starting loop")
        _log.debug("[BU SETUP] BetterUptime is now fully initialised. Setup complete.")

        while True:
            _log.debug("Loop has started next iteration")
            try:
                self.main_loop_meta.iter_start()
                await self.update_uptime()
                self.main_loop_meta.iter_finish()
                _log.debug("Loop has finished, saved to config")
            except Exception as e:
                self.main_loop_meta.iter_error(e, self.sentry_hub)
                _log.exception(
                    "Something went wrong in the main BetterUptime loop. The loop will try again "
                    "in 60 seconds. Please report this and the below information to Vexed."
                )

            await self.main_loop_meta.sleep_until_next()

    async def write_to_config(self) -> None:
        if not self.cog_loaded_cache.empty:
            data = json.loads(self.cog_loaded_cache.to_json())  # type: ignore
            await self.config.cog_loaded.set(data)
        if not self.connected_cache.empty:
            data = json.loads(self.connected_cache.to_json())  # type: ignore
            await self.config.connected.set(data)

    async def update_uptime(self):
        if self.sentry_hub:
            with self.sentry_hub:
                master_span = sentry_sdk.start_transaction(
                    op="loop",
                    name="BetterUptime main loop",
                    description="Main loop for BetterUptime",
                )
                collection_span = master_span.start_child(
                    op="collect_data", description="Data collection"
                )

        utcdatetoday = datetime.datetime.utcnow().replace(
            microsecond=0, second=0, minute=0, hour=0
        )

        # === COG LOADED ===
        try:
            self.cog_loaded_cache[utcdatetoday] += 60
        except KeyError:
            self.cog_loaded_cache[utcdatetoday] = 60

        # === CONNECTED ===
        # bit of background info here: the latency is updated every heartbeat and if the heartbeat
        # fails (so bot is unable to connect) the latency is infinity (float("inf"))
        # heartbeats are around every 42 seconds as of the time i write this
        # and it's a float for compatibility with old versions
        if self.bot.latency != INF:
            try:
                self.connected_cache[utcdatetoday] += 60.0
            except KeyError:
                self.connected_cache[utcdatetoday] = 60.0

        if self.sentry_hub:
            collection_span.finish()
            save_span = master_span.start_child(op="save", description="Save data")

        await self.write_to_config()

        if self.sentry_hub:
            save_span.finish()
            master_span.set_status("ok")
            master_span.finish()
