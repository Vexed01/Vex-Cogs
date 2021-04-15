import asyncio
import logging
from math import floor
from time import monotonic
from typing import Dict

from discord import Embed, Message, TextChannel
from redbot.core.bot import Red

from status.core import FEEDS, UPDATE_NAME
from status.objects import (
    ChannelData,
    ConfChannelSettings,
    ConfigWrapper,
    InvalidChannel,
    SendCache,
    Update,
)

from .utils import get_channel_data, get_webhook

_log = logging.getLogger("red.vexed.status.sendupdate")


class SendUpdate:
    """Send an update."""

    def __init__(
        self,
        bot: Red,
        config_wrapper: ConfigWrapper,
        update: Update,
        service: str,
        sendcache: SendCache,
        dispatch: bool = True,
        force: bool = False,
    ):
        self.bot = bot
        self.config_wrapper = config_wrapper

        self.incidentdata = update.incidentdata
        self.update = update
        self.service = service
        self.sendcache = sendcache
        self.dispatch = dispatch
        self.force = force
        self.channeldata: ChannelData

    def __repr__(self):
        return (
            f"<bot=bot update=update service={self.service} sendcache={self.sendcache} "
            f"dispatch={self.dispatch} force={self.force}>"
        )

    async def send(self, channels: Dict[int, ConfChannelSettings]) -> None:
        """Send the update decalred in the class init.

        Parameters
        ----------
        channels : dict
            Channels to send to, format {ID: SETTINGS}
        """
        if self.dispatch:
            self._dispatch_main(channels)
            # delay for listeners to do expensive stuff before channels start sending
            await asyncio.sleep(1)

        start = monotonic()
        _log.info(f"Sending update for {self.service} to {len(channels)} channels...")

        for c_id, settings in channels.items():
            try:
                await self._send_updated_feed(c_id, settings)
            except Exception:
                return _log.warning(
                    f"Something went wrong sending to {c_id} - skipping.", exc_info=True
                )

        end = monotonic()
        time = floor(end - start) or "under a"
        _log.info(f"Sending update for {self.service} took {time} second(s).")

    async def _send_updated_feed(self, c_id: int, settings: ConfChannelSettings) -> None:
        """Send feed decalred in init to a channel.

        Parameters
        ----------
        c_id : int
            Channel ID
        settings : ConfChannelSettings
            Settings for channel.
        """
        try:
            channeldata = await get_channel_data(self.bot, c_id, settings)
        except InvalidChannel:
            return

        self.channeldata = channeldata

        if channeldata.embed:
            if channeldata.mode in ["all", "edit"]:
                embed = self.sendcache.embed_all
            else:
                embed = self.sendcache.embed_latest

            if channeldata.webhook:
                await self._send_webhook(channeldata.channel, embed)
            else:
                await self._send_embed(channeldata.channel, embed)

        else:
            if channeldata.mode in ["all", "edit"]:
                msg = self.sendcache.plain_all
            else:
                msg = self.sendcache.plain_latest

            await self._send_plain(channeldata.channel, msg)

        if self.dispatch:
            self._dispatch_channel(channeldata)

    # TODO: maybe try to do some DRY on the next 3

    async def _send_webhook(self, channel: TextChannel, embed: Embed) -> None:
        """Send a webhook to the specified channel

        Parameters
        ----------
        channel : TextChannel
            Channel to send to
        embed : Embed
            Embed to use
        """
        embed.set_footer(text=f"Powered by {channel.guild.me.name}\nLast update")
        webhook = await get_webhook(channel)

        if self.channeldata.mode == "edit":
            if edit_id := self.channeldata.edit_id.get(self.incidentdata.incident_id):
                try:
                    await webhook.edit_message(edit_id, embed=embed, content=None)
                except Exception:  # eg message deleted
                    edit_id = None
            if not edit_id:
                sent_webhook = await webhook.send(
                    username=UPDATE_NAME.format(FEEDS[self.service]["friendly"]),
                    avatar_url=FEEDS[self.service]["avatar"],
                    embed=embed,
                    wait=True,
                )
                await self.config_wrapper.update_edit_id(
                    channel.id, self.service, self.incidentdata.incident_id, sent_webhook.id
                )

        else:
            await webhook.send(
                username=UPDATE_NAME.format(FEEDS[self.service]["friendly"]),
                avatar_url=FEEDS[self.service]["avatar"],
                embed=embed,
            )

    async def _send_embed(self, channel: TextChannel, embed: Embed) -> None:
        """Send an embed to the specified channel

        Parameters
        ----------
        channel : TextChannel
            Channel to send to
        embed : Embed
            Embed to use
        """
        embed.set_footer(text="Last update")
        embed.set_author(
            name=UPDATE_NAME.format(FEEDS[self.service]["friendly"]),
            icon_url=FEEDS[self.service]["avatar"],
        )

        if self.channeldata.mode == "edit":
            if edit_id := self.channeldata.edit_id.get(self.incidentdata.incident_id):
                try:
                    message = channel.get_partial_message(edit_id)
                    await message.edit(embed=embed, content=None)
                except Exception:  # eg message deleted
                    edit_id = None
            if not edit_id:
                sent_message: Message = await channel.send(embed=embed)
                await self.config_wrapper.update_edit_id(
                    channel.id, self.service, self.incidentdata.incident_id, sent_message.id
                )
        else:
            await channel.send(embed=embed)

    async def _send_plain(self, channel: TextChannel, msg: str) -> None:
        """Send a plain message to the specified channel

        Parameters
        ----------
        channel : TextChannel
            Channel to send to
        msg : str
            Message to send
        """
        if self.channeldata.mode == "edit":
            if edit_id := self.channeldata.edit_id.get(self.incidentdata.incident_id):
                try:
                    message = channel.get_partial_message(edit_id)
                    await message.edit(embed=None, content=None)
                except Exception:  # eg message deleted
                    edit_id = None
            if not edit_id:
                sent_message = await channel.send(content=msg)
                await self.config_wrapper.update_edit_id(
                    channel.id, self.service, self.incidentdata.incident_id, sent_message.id
                )
        else:
            await channel.send(content=msg)

    def _dispatch_main(self, channels: dict) -> None:
        """
        For more information on this event, take a look at the event reference in the docs:
        https://vex-cogs.readthedocs.io/en/latest/statusdev.html
        (yes i could use autodoc but thats scary)
        """
        self.bot.dispatch(
            "vexed_status_update",
            update=self.update,
            service=self.service,
            channels=channels,
            force=self.force,
        )

    def _dispatch_channel(self, channeldata: ChannelData) -> None:
        """
        For more information on this event, take a look at the event reference in the docs:
        https://vex-cogs.readthedocs.io/en/latest/statusdev.html
        (yes i could use autodoc but thats scary)
        """
        self.bot.dispatch(
            "vexed_status_channel_send",
            update=self.update,
            service=self.service,
            channel_data=channeldata,
            force=self.force,
        )
