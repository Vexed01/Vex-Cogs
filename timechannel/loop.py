import asyncio
import datetime
import logging
import math

from discord.channel import VoiceChannel
from discord.errors import HTTPException

from timechannel.utils import gen_replacements

from .abc import MixinMeta
from .vexutils.loop import VexLoop

_log = logging.getLogger("red.vex.timechannel.loop")


class TCLoop(MixinMeta):
    def __init__(self) -> None:
        self.loop_meta = VexLoop("TimeChannel Loop", 900)  # 15 mins
        self.loop = self.bot.loop.create_task(self.timechannel_loop())

    async def wait_until_iter(self) -> None:
        now = datetime.datetime.utcnow()
        time = now.timestamp()
        time = math.ceil(time / 900) * 900
        next_iter = datetime.datetime.fromtimestamp(time) - now
        seconds_to_sleep = (next_iter).total_seconds()

        _log.debug(f"Sleeping for {seconds_to_sleep} seconds until next iter...")
        await asyncio.sleep(seconds_to_sleep)

    async def timechannel_loop(self) -> None:
        await self.bot.wait_until_red_ready()
        await asyncio.sleep(1)
        _log.debug("Timechannel loop has started.")
        while True:
            try:
                self.loop_meta.iter_start()
                await self.maybe_update_channels()
                self.loop_meta.iter_finish()

                _log.debug("Timechannel iteration finished")
            except Exception as e:
                _log.exception(
                    "Something went wrong in the timechannel loop. Some channels may have been "
                    "missed. The loop will run again at the next hour.",
                    exc_info=e,
                )
            await self.wait_until_iter()

    async def maybe_update_channels(self) -> None:
        all_guilds: dict[int, dict[str, dict[int, str]]] = await self.config.all_guilds()
        if not all_guilds:
            _log.debug("No time channels registered, nothing to do...")
            return

        reps = gen_replacements()

        for guild_id, guild_data in all_guilds.items():
            guild = self.bot.get_guild(guild_id)
            if guild is None:
                _log.debug(f"Can't find guild with ID {guild_id} - skipping")
                continue

            for c_id, string in guild_data.get("timechannels", {}).items():
                channel = self.bot.get_channel(int(c_id))
                if channel is None:
                    # yes log *could* be inaccurate but a timezone being removed is unlikely
                    _log.debug(f"Can't find channel with ID {c_id} - skipping")
                    continue

                assert isinstance(channel, VoiceChannel)

                new_name = string.format(**reps)

                try:
                    await channel.edit(
                        name=new_name,
                        reason="Edited for timechannel - disable with `tcset remove`",
                    )
                    _log.debug(f"Edited channel {c_id} to {new_name}")
                except HTTPException:
                    _log.debug(f"Unable to edit channel ID {c_id}")
                    continue
