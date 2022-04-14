import asyncio
from typing import Literal, NoReturn

import discord

from .abc import MixinMeta
from .objects import MessageData, ServerUnreachable
from .vexutils import get_vex_logger
from .vexutils.loop import VexLoop

_log = get_vex_logger(__name__)


class FiveMLoop(MixinMeta):
    def __init__(self) -> None:
        self.loop_meta = VexLoop("FiveMStatus Loop", 60)  # 1 min
        self.loop = self.bot.loop.create_task(self.fivemstatus_loop())

    async def fivemstatus_loop(self) -> NoReturn:
        await self.bot.wait_until_red_ready()
        await asyncio.sleep(1)
        _log.debug("FiveMStatus loop has started.")
        while True:
            try:
                self.loop_meta.iter_start()
                await self.update_messages()
                self.loop_meta.iter_finish()

                _log.debug("FiveMStatus iteration finished")
            except Exception as e:
                _log.exception(
                    "Something went wrong in the FiveMStatus loop. Some channels may have been "
                    "missed. The loop will run again at the next hour.",
                    exc_info=e,
                )
            await self.loop_meta.sleep_until_next()

    async def update_messages(self) -> None:
        all_guilds: dict[
            int, dict[Literal["message"], MessageData]
        ] = await self.config.all_guilds()
        if not all_guilds:
            _log.debug("Nothing registered, nothing to do...")
            return

        for guild_id, data in all_guilds.items():
            message = data["message"]
            if not message:
                continue
            channel = self.bot.get_channel(message.get("channel_id"))  # TODO: dpy 2 - partial chan
            partial_message = channel.get_partial_message(message["msg_id"])

            try:
                data = await self.get_data(message["server"])
                embed = await self.generate_embed(data, message, message["maintenance"])
                try:
                    await partial_message.edit(embed=embed)
                except discord.Forbidden:
                    _log.warning(
                        f"Could not edit message in channel {message['channel_id']} for server"
                        f" {message['server']} because I do not have permission"
                    )
                except discord.NotFound:
                    _log.warning(
                        f"Could not edit message in channel {message['channel_id']} for server"
                        f" {message['server']} because it was deleted. Stopping updates for"
                        " this."
                    )
                    async with self.config.guild_from_id(guild_id).message() as conf:
                        for message_data in conf:
                            if message_data["msg_id"] == message["msg_id"]:
                                conf.remove(message_data)
                                break

            except ServerUnreachable:
                embed = await self.generate_embed(None, message, message["maintenance"])
                try:
                    await partial_message.edit(embed=embed)
                except discord.Forbidden:
                    _log.warning(
                        f"Could not edit message in channel {message['channel_id']} for server"
                        f" {message['server']} because I do not have permission"
                    )
                except discord.NotFound:
                    _log.warning(
                        f"Could not edit message in channel {message['channel_id']} for server"
                        f" {message['server']} because it was deleted. Stopping updates for"
                        " this."
                    )
                    async with self.config.guild_from_id(guild_id).message() as conf:
                        for message_data in conf:
                            if message_data["msg_id"] == message["msg_id"]:
                                conf.remove(message_data)
                                break
