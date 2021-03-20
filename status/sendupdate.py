import asyncio
import datetime
import logging
import re
from time import monotonic, time
from typing import List

import discord
import feedparser
from feedparser import FeedParserDict
from redbot.core import Config
from redbot.core.bot import Red

from .consts import AVATAR_URLS, CUSTOM_SERVICES, FEED_FRIENDLY_NAMES, WEBHOOK_REASON
from .objects import FeedDict, SendCache
from .rsshelper import process_feed as helper_process_feed

log = logging.getLogger("red.vexed.status.updatechecker")


class SendUpdate:
    def __init__(self, config: Config, bot: Red):
        self.bot = bot
        self.config = config

    async def _update_dispatch(self, feed, feedparser, service, channels, force):
        """
        For more information on this event, take a look at the event reference in the docs:
        https://vex-cogs.readthedocs.io/en/latest/statusdev.html
        """
        self.bot.dispatch(
            "vexed_status_update",
            feed=feed,
            feedparser=feedparser,
            service=service,
            channels=channels,
            force=force,
        )

    async def _channel_send_dispatch(self, feed, service, channel, webhook, embed, mode):
        """
        For more information on this event, take a look at the event reference in the docs:
        https://vex-cogs.readthedocs.io/en/latest/statusdev.html
        """
        self.bot.dispatch(
            "vexed_status_channel_send",
            feed=feed,
            service=service,
            channel=channel,
            webhook=webhook,
            embed=embed,
            mode=mode,
        )

    async def _maybe_send_update(self, html: str, service: str):
        """Send updates if the update is determined to be real"""
        fp_data = feedparser.parse(html)
        feeddict = self._process_feed(service, fp_data)
        real_updates = await self._check_real_update(service, feeddict)
        if not real_updates:
            log.debug(f"Ghost status update for {service} detected, skipping")
            return
        for feeddict in real_updates:
            if feeddict is None:
                continue
            # this will nearly always only iterate once
            # log.debug(f"Feed dict for {service}: {feeddict}")
            channels = await self._get_channels(service)
            await self._make_send_cache(feeddict, service)
            await self._update_dispatch(feeddict, fp_data, service, channels, False)
            await asyncio.sleep(1)  # guaranteed wait for other CCs
            log.info(f"Sending status update for {service} to {len(channels)} channels...")
            start = monotonic()
            for channel in channels.items():
                await self._channel_send_updated_feed(feeddict, channel, service)
            end = monotonic()
            raw = end - start
            time = round(raw) or "under a"
            if raw <= 15:
                log.info(f"Done, took {time} second(s).")
            elif raw <= 60:
                log.info(f"Sending status update for {service} took a long time ({time} seconds).")
            else:
                log.warning(
                    f"Sending status update for {service} took too long ({time} seconds). All updates were "
                    "sent.\nThere is a real risk that, if multiple services post updates at once, some will "
                    "be skipped.\nPlease contact Vexed for ways to mitigate this."
                )
            self.send_cache = SendCache.empty()

    def _process_feed(self, service: str, feedparser: FeedParserDict):
        """Process a FeedParserDict into a nicer dict for embeds."""
        return helper_process_feed(service, feedparser)

    async def _check_real_update(self, service: str, feeddict: List[FeedDict]) -> List[FeedDict]:
        """
        Check that there has been an actual update to the status against last known.
        If so, will update the feed store.

        Returns a list of valid status updates - the list might be empty.
        """
        to_return = []
        for entry in feeddict:
            # if service in CUSTOM_SERVICES:
            #     async with self.config.feed_store() as feed_store:
            #         # these are aws and gcp which only parse to one field
            #         old_fields = feed_store.get(service, {}).get("fields", [])
            #         if not old_fields:
            #             to_store = entry.to_dict()
            #             to_store["time"] = to_store["time"].timestamp()
            #             to_store["actual_time"] = to_store["actual_time"].timestamp()
            #             feed_store[service] = to_store
            #             return [entry]
            #         if entry.fields[0].name != old_fields[0]["name"]:
            #             return []
            #         to_store = entry.to_dict()
            #         to_store["time"] = to_store["time"].timestamp()
            #         to_store["actual_time"] = to_store["actual_time"].timestamp()
            #         feed_store[service] = to_store
            #         return [entry]

            if abs(entry.actual_time.timestamp() - time()) < 330:
                # 5 and a half mins to allow for 2 update runs
                to_return.append(entry)

        # add to the feed store for preview command, [-1] will be the one at the top of the feed
        if to_return:
            to_store = to_return[-1].to_dict()
            if isinstance(to_store["time"], datetime.datetime):
                to_store["time"] = to_store["time"].timestamp()
            else:
                to_store["time"] = ""

            if isinstance(to_store["actual_time"], datetime.datetime):
                to_store["actual_time"] = to_store["actual_time"].timestamp()
            else:
                to_store["actual_time"] = ""

            await self.config.feed_store.set_raw("discord", value=to_store)

        return to_return

    async def _get_channels(self, service: str) -> dict:
        """Get the channels for a feed. The list is channel IDs from config, they may be invalid."""
        feeds = await self.config.all_channels()
        return {name: data["feeds"][service] for name, data in feeds.items() if service in data["feeds"].keys()}

    async def _make_send_cache(self, feeddict: FeedDict, service: str):
        """Make the cache used in send_updated_feed"""
        try:
            base = discord.Embed(
                title=feeddict.title,
                description=feeddict.description,
                timestamp=feeddict.time,
                colour=self._get_colour(feeddict, service),
                url=feeddict.link,
            )
        except Exception as e:  # can happen with timestamps, should now be fixed
            log.error(
                "Failed turning a feed into an embed. Updates will not be sent. PLEASE REPORT THIS AND THE INFO BELOW TO VEXED.\n"
                f"{feeddict.to_dict()}",
                exc_info=e,
            )
            base = discord.Embed(
                title=feeddict.title,
                description=feeddict.description,
                colour=self._get_colour(feeddict, service),
                url=feeddict.link,
            )

        embed_latest: discord.Embed = base.copy()
        embed_all: discord.Embed = base.copy()

        # ALL
        for field in feeddict.fields:
            embed_all.add_field(name=field.name, value=field.value, inline=False)

        before_fields = len(embed_all.fields)
        if before_fields > 25:
            dict_embed = embed_all.to_dict()
            dict_embed["fields"] = dict_embed["fields"][-25:]
            embed_all = discord.Embed.from_dict(dict_embed)
            embed_all.set_field_at(
                0,
                name="{} earlier updates were omitted.".format(before_fields - 24),
                value="This is because embeds are limited to 25 fields.",
            )

        # LATEST
        # TODO: implement usage of group_id for longer updates
        # TODO: implement field time so don't miss an update if in quick succession
        id = feeddict.get_group_ids()[-1]
        for field in feeddict.fields:
            if field.group_id == id or abs(field.time.timestamp() - time()) < 150:
                embed_latest.add_field(
                    name=field.name,
                    value=field.value,
                    inline=False,
                )

        if service in CUSTOM_SERVICES:
            embed_latest = embed_all.copy()
            # not the most efficient but i dont want more nesting

        # PLAIN MESSAGE
        t = feeddict.title
        d = f"{feeddict.description}\n" if feeddict.description else ""
        l = feeddict.link
        n = FEED_FRIENDLY_NAMES[service]
        plain_latest = f"**{n} Status Update\n{t}**\nIncident link: {l}\n{d}\n"
        plain_all = f"**{n} Status Update\n{t}**\nIncident link: {l}\n{d}\n"

        for i in feeddict.fields:
            n = i.name
            v = i.value
            plain_all += f"**{n}**\n{v}\n"

        n = feeddict.fields[-1].name
        v = feeddict.fields[-1].name
        plain_latest += f"**{n}**\n{v}\n"

        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        # regex from https://stackoverflow.com/a/28187496
        plain_all = re.sub(regex, r"<\1>", plain_all)  # wrap links in <> for no previews
        plain_latest = re.sub(regex, r"<\1>", plain_latest)

        self.send_cache = SendCache(
            embed_all=embed_all,
            embed_latest=embed_latest,
            plain_latest=plain_latest,
            plain_all=plain_all,
        )

    def _get_colour(self, feeddict: FeedDict, service: str):
        if service in ["aws", "gcp"]:  # only do this for statuspage ones
            return 1812720

        try:
            last_title = feeddict.fields[-1].name
            status = last_title.split(" ")[0].lower()

            if status == "investigating":
                return discord.Colour.red()
            elif status in [
                "update",
                "identified",
                "monitoring",
                "scheduled",  # decided to put this in orange as is in future, not now
                "in",  # scheduled - full is "in progress"
            ]:
                return discord.Colour.orange()
            elif status in ["resolved", "completed"]:
                return discord.Colour.green()
            else:
                return 1812720
        except Exception as e:  # hopefully never happens but will keep this for a while
            log.error(f"Error with getting correct colour for {service}:", exc_info=e)
            return 1812720

    async def _channel_send_updated_feed(self, feeddict: FeedDict, channel_data: tuple, service: str, dispatch: bool = True):
        """Send a feeddict to the specified channel."""
        mode = channel_data[1].get("mode")
        m_id = channel_data[1].get("edit_id", {}).get(feeddict.link)
        channel: discord.TextChannel = self.bot.get_channel(channel_data[0])
        use_webhook = await self._validate(channel, channel_data[1].get("webhook"))
        if use_webhook == "exit":
            return

        if not use_webhook:
            use_embed = await self.bot.embed_requested(channel, None)
        else:
            use_embed = True

        # the efficiency could probably be improved here
        if use_embed:
            if mode in ["all", "edit"]:
                embed = self.send_cache.embed_all
            elif mode == "latest":
                embed = self.send_cache.embed_latest
            else:
                return

            try:
                if use_webhook:
                    await self._send_webhook(channel, embed, service, mode, feeddict.link, m_id)
                else:
                    await self._send_embed(channel, embed, service, mode, feeddict.link, m_id)
            except Exception as e:
                log.info(  # TODO: remove from config
                    f"Something went wrong with {channel.id} in guild {channel.guild.id} - skipping", exc_info=e
                )
                return

        else:
            if mode in ["all", "edit"]:
                msg = self.send_cache.plain_all
            elif mode == "latest":
                msg = self.send_cache.plain_latest

            try:
                await self._send_plain(channel, msg, service, mode, feeddict.link, m_id)
            except Exception as e:
                log.info(  # TODO: remove from config
                    f"Something went wrong with {channel.id} in guild {channel.guild.id} - skipping", exc_info=e
                )
                return

        if dispatch:
            await self._channel_send_dispatch(feeddict, service, channel, use_webhook, use_embed, mode)

    async def _send_webhook(
        self, channel: discord.TextChannel, embed: discord.Embed, service: str, mode: str, feeddict_link: str, m_id: int
    ):
        botname = channel.guild.me.nick or channel.guild.me.name
        embed.set_footer(text=f"Powered by {botname}")
        webhook = await self._get_webhook(service, channel)
        if mode == "edit":
            if m_id:
                try:
                    await webhook.edit_message(m_id, embed=embed, content=None)
                except discord.NotFound:
                    id = None
            if not id:
                sent_webhook = await webhook.send(
                    username=f"{FEED_FRIENDLY_NAMES[service]} Status Update",
                    avatar_url=AVATAR_URLS[service],
                    embed=embed,
                    wait=True,
                )
                async with self.config.channel(channel).feeds() as conf:
                    if conf[service].get("edit_id") is None:
                        conf[service]["edit_id"] = {}
                    conf[service]["edit_id"][feeddict_link] = sent_webhook.id
        else:
            await webhook.send(
                username=f"{FEED_FRIENDLY_NAMES[service]} Status Update",
                avatar_url=AVATAR_URLS[service],
                embed=embed,
            )
        return id

    async def _send_embed(
        self, channel: discord.TextChannel, embed: discord.Embed, service: str, mode, feeddict_link: str, m_id: str
    ):
        embed.set_author(
            name=f"{FEED_FRIENDLY_NAMES[service]} Status Update",
            icon_url=AVATAR_URLS[service],
        )
        if mode == "edit":
            if m_id is not None:
                try:
                    msg: discord.Message = await channel.fetch_message(m_id)
                    await msg.edit(embed=embed, content=None)
                except discord.NotFound:
                    m_id = None
            if m_id is None:
                sent_message: discord.Message = await channel.send(embed=embed)
                async with self.config.channel(channel).feeds() as conf:
                    if conf[service].get("edit_id") is None:
                        conf[service]["edit_id"] = {}
                    conf[service]["edit_id"][feeddict_link] = sent_message.id
        else:
            await channel.send(embed=embed)

    async def _send_plain(
        self, channel: discord.TextChannel, msg: str, service: str, mode: str, feeddict_link: str, m_id: str
    ):
        if mode == "edit":
            if m_id is not None:
                old_msg = await channel.fetch_message(m_id)
                await old_msg.edit(content=msg, embed=None)
            else:
                sent_message = await channel.send(msg)
                async with self.config.channel(channel).feeds() as conf:
                    if conf[service].get("edit_id") is None:
                        conf[service]["edit_id"] = {}
                    conf[service]["edit_id"][feeddict_link] = sent_message.id
        else:
            await channel.send(msg)

    async def _get_webhook(self, service: str, channel: discord.TextChannel) -> discord.Webhook:
        # thanks flare for your webhook logic (redditpost) (or trusty?)
        webhook = None
        for hook in await channel.webhooks():
            if hook.name == channel.guild.me.name:
                webhook = hook
        if webhook is None:
            webhook = await channel.create_webhook(name=channel.guild.me.name, reason=WEBHOOK_REASON.format(service))
        return webhook

    async def _validate(self, channel: discord.TextChannel, webhook: bool):
        use_webhook = webhook
        c_id = channel.id

        if channel is None:
            try:
                channel = await self.bot.fetch_channel(c_id)
            except:
                log.info(
                    f"Unable to get channel {c_id} for status update. Removing from config so this won't happen again."
                )
                await self.config.channel_from_id(c_id).feeds.clear()
                return "exit"

        if await self.bot.cog_disabled_in_guild_raw("Status", channel.guild):
            log.debug(f"Skipping channel {c_id} as cog is disabled in that guild.")
            return "exit"

        if use_webhook and not channel.permissions_for(channel.guild.me).manage_webhooks:
            log.debug(f"Unable to send a webhook to {c_id} in guild {channel.guild.id} - sending normal instead")
            use_webhook = False

        if not use_webhook and not channel.permissions_for(channel.guild.me).send_messages:
            log.info(
                f"Unable to send messages to {c_id} in guild {channel.guild.id}. Removing from config so this won't happen again."
            )
            await self.config.channel_from_id(c_id).feeds.clear()
            return "exit"

        return use_webhook
