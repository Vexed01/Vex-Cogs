import asyncio
import datetime
import logging
from typing import Dict

import pytz
from discord.channel import DMChannel, GroupChannel
from discord.errors import HTTPException
from vexcogutils.loop import VexLoop

from .abc import MixinMeta

log = logging.getLogger("red.vexed.timechannel.loop")


class TCLoop(MixinMeta):
    def __init__(self) -> None:
        self.loop_meta = VexLoop("TimeChannel Loop", 3600)  # 1 hour
        self.loop = asyncio.create_task(self.timechannel_loop())

    async def wait_until_hour(self) -> None:
        delta = datetime.timedelta(hours=1)
        now = datetime.datetime.utcnow()
        next_hour = now.replace(minute=0, second=1, microsecond=0) + delta
        seconds_to_sleep = (next_hour - now).total_seconds()

        log.debug(f"Sleeping for {seconds_to_sleep} seconds until next hour...")
        await asyncio.sleep(seconds_to_sleep)

    async def timechannel_loop(self) -> None:
        await self.bot.wait_until_red_ready()
        log.debug("Timechannel loop has started.")
        while True:
            try:
                self.loop_meta.iter_start()
                # await self.maybe_update_channels()
                self.loop_meta.iter_finish()
            except Exception as e:
                self.loop_meta.iter_error(e)
                log.exception(
                    "Something went wrong in the timechannel loop. Some channels may have been "
                    "missed. The loop will run again at the next hour."
                )

            await self.wait_until_hour()

    async def maybe_update_channels(self) -> None:
        all_guilds: Dict[int, Dict[str, Dict[int, str]]] = await self.config.all_guilds()
        if not all_guilds:
            log.debug("No time channels registered, nothing to do...")
            return

        for guild_id, guild_data in all_guilds.items():
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                log.debug(f"Can't find guild with ID {guild_id} - removing from config")
                await self.config.guild_from_id(guild_id).clear()
                continue

            for c_id, target_timezone in guild_data.get("timechannels", {}).items():
                channel = self.bot.get_channel(int(c_id))  # dont know why its str
                assert not isinstance(channel, DMChannel) and not isinstance(channel, GroupChannel)
                if channel is None:
                    # yes log *could* be inaccurate but a timezone being removed is unlikely
                    log.debug(f"Can't find channel with ID {c_id} - skipping")
                    continue
                if target_timezone not in pytz.common_timezones:
                    log.debug(f"Timezone {target_timezone} is not recognised.")
                    # hard to remove from config as config is guild based, guild based so can
                    # easily iterate through timechannels in guild for timezones command.
                    continue

                new_time = (
                    datetime.datetime.now(pytz.timezone(target_timezone))
                    .strftime("%I%p")
                    .lstrip("0")
                )
                short_tz = target_timezone.split("/")[-1].replace(
                    "_", " "
                )  # full one usually is too long
                new_name = f"{short_tz}: {new_time} "

                try:
                    await channel.edit(
                        name=new_name,
                        reason="Edited for timechannel - disable with `tcset remove`",
                    )
                    log.debug(f"Edited channel {c_id} to {new_name}")
                except HTTPException:
                    log.debug(f"Unable to edit channel ID {c_id} - removing from config")
                    continue
