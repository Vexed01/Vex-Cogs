# HELLO!
# This file is formatted with black, line length 120
# If you are looking for an event your cog can listen to, take a look here:
# https://vex-cogs.readthedocs.io/en/latest/statusdev.html

import asyncio
import datetime
import logging
import re
from typing import Optional

import aiohttp
import discord
import feedparser
from discord.ext import tasks
from discord.ext.commands.core import guild_only
from feedparser.util import FeedParserDict
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, pagify, warning
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
from tabulate import tabulate

from .consts import *
from .objects import FeedDict, SendCache, UsedFeeds
from .rsshelper import process_feed as _helper_process_feed


log = logging.getLogger("red.vexed.status")


class Status(commands.Cog):
    """
    Automatically check for status updates.

    When there is one, it will send the update to all channels that
    have registered to revieve updates from that service.

    If there's a service that you want added, contact Vexed#3211 or
    make an issue on the GitHub repo (or even better a PR!).
    """

    __version__ = "1.2.0"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        docs = (
            "This cog has docs! Check them out at\nhttps://vex-cogs.readthedocs.io/en/latest/cogs/status.html"
        )
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**\n{docs}"
        # adding docs link here so doesn't show up in auto generated docs

    def __init__(self, bot: Red):
        self.bot = bot

        self.config: Config = Config.get_conf(self, identifier="Vexed-status")
        default = {}
        self.config.register_global(etags=default)
        self.config.register_global(feed_store=default)
        self.config.register_global(latest=default)
        self.config.register_global(migrated=False)
        self.config.register_channel(feeds=default)

        self.used_feeds_cache: UsedFeeds = UsedFeeds({})
        self.send_cache: SendCache = SendCache.empty()

        self._check_for_updates.start()

    def cog_unload(self):
        self._check_for_updates.cancel()

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    @tasks.loop(minutes=2.0)
    async def _check_for_updates(self):
        """Loop that checks for updates and if needed triggers other functions to send them."""
        if self._check_for_updates.current_loop == 0:
            await self._make_used_feeds()
            if await self.config.migrated() is False:
                log.info("Migrating to new config format...")
                await self._migrate()
                await self.config.clear_all_guilds()
                log.info("Done!")

        if not self.used_feeds_cache.get_list():
            log.debug("Nothing to do, no channels have registered a feed.")
            return

        try:
            await asyncio.wait_for(self._actually_check_updates(), timeout=110.0)  # 1 min 50 secs
        except TimeoutError:
            log.error(
                "Loop timed out after 1 minute 50 seconds. Will try again shortly. If this keeps happening "
                "when there's an update for a specific service, contact Vexed."
            )
        except Exception as e:
            log.error(
                "Unable to check (and send) updates. Some services were likely skipped. If they had updates, "
                "they should send on the next loop.",
                exc_info=e,
            )

    @_check_for_updates.before_loop
    async def before_start(self):
        await self.bot.wait_until_red_ready()

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

    async def _make_used_feeds(self):
        """Make the list of used feeds on cog load"""
        feeds = await self.config.all_channels()
        self.used_feeds_cache = UsedFeeds(feeds)

    async def _migrate(self):
        """Migrate config format"""
        old_feeds = await self.config.all_guilds()
        for guild in old_feeds.items():
            try:
                feeds_in_guild = guild[1]["feeds"]
                for feed in feeds_in_guild.items():
                    if not feed[1]:  # could just be []
                        continue
                    feed_name = feed[0]
                    channels = feed[1]
                    if isinstance(channels, list):
                        for c in channels:
                            await self.config.channel_from_id(c).feeds.set_raw(feed_name, value=OLD_DEFAULTS)
                    else:
                        await self.config.channel_from_id(channels).feeds.set_raw(
                            feed_name, value=OLD_DEFAULTS
                        )
            except KeyError:
                continue
        await self.config.migrated.set(True)

    async def _actually_check_updates(self):
        """The actual update logic"""
        async with aiohttp.ClientSession() as session:
            for service in self.used_feeds_cache.get_list():
                async with self.config.etags() as etags:
                    try:
                        async with session.get(
                            FEED_URLS[service], headers={"If-None-Match": etags[service]}, timeout=5
                        ) as response:
                            html = await response.text()
                            status = response.status
                            if status == 200:
                                etags[service] = response.headers.get("ETag")
                    except KeyError:
                        async with session.get(FEED_URLS[service]) as response:
                            html = await response.text()
                            status = response.status
                        if service != "gcp":  # gcp doesn't do etags
                            etags[service] = response.headers.get("ETag")
                    except Exception as e:
                        log.warning(f"Unable to check for an update for {service}", exc_info=e)
                        continue

                if status == 200:
                    fp_data = feedparser.parse(html)
                    feeddict = await self._process_feed(service, fp_data)
                    if not await self._check_real_update(service, feeddict):
                        log.debug(f"Ghost status update for {service} detected, skipping")
                        continue
                    # log.debug(f"Feed dict for {service}: {feeddict}")
                    channels = await self._get_channels(service)
                    await self._make_send_cache(feeddict, service)
                    await self._update_dispatch(feeddict, fp_data, service, channels, False)
                    await asyncio.sleep(1)  # guaranteed wait for other CCs
                    log.info(f"Sending status update for {service} to {len(channels)} channels...")
                    for channel in channels.items():
                        await self._send_updated_feed(feeddict, channel, service)
                    self.send_cache = SendCache.empty()
                    log.info("Done")
                else:
                    log.debug(f"No status update for {service}")
        await session.close()

    async def _process_feed(self, service: str, feedparser: FeedParserDict):
        """Process a FeedParserDict into a nicer dict for embeds."""
        return await _helper_process_feed(service, feedparser)

    async def _check_real_update(self, service: str, feeddict: FeedDict) -> bool:
        """
        Check that there has been an actual update to the status against last known.
        If so, will update the feed store.
        """
        async with self.config.feed_store() as feed_store:
            try:
                old_fields = feed_store[service]["fields"]
            except KeyError:
                to_store = feeddict.to_dict()
                to_store["time"] = to_store["time"].timestamp()
                feed_store[service] = to_store
                return True  # ovy a new one as not in config
            prev_titles = []
            for field in old_fields:
                prev_titles.append(field.get("name"))
            if service in DONT_REVERSE and feeddict.fields[-1].name in prev_titles:
                if feeddict.fields[-1].name == "THIS IS A SCHEDULED EVENT":  # aaaaaaa
                    if feeddict.fields[-1].value == old_fields[-1]["value"]:
                        return False
                    return True
                return False
            elif service not in DONT_REVERSE and feeddict.fields[0].name in prev_titles:
                if feeddict.fields[0].name == "THIS IS A SCHEDULED EVENT":  # aaaaaaa
                    if feeddict.fields[0].value == old_fields[0]["value"]:
                        return False
                    return True
                return False
            else:
                to_store = feeddict.to_dict()
                if isinstance(to_store["time"], datetime.datetime):
                    to_store["time"] = to_store["time"].timestamp()
                else:
                    to_store["time"] = ""
                feed_store[service] = to_store
                return True

    async def _get_channels(self, service: str) -> dict:
        """Get the channels for a feed. The list is channel IDs from config, they may be invalid."""
        feeds = await self.config.all_channels()
        channels = {}
        for name, data in feeds.items():
            if service in data["feeds"].keys():
                channels[name] = data["feeds"][service]
        return channels

    async def _make_send_cache(self, feeddict: FeedDict, service: str):
        """Make the cache used in send_updated_feed"""
        try:
            base = discord.Embed(
                title=feeddict.title,
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
                colour=self._get_colour(feeddict, service),
                url=feeddict.link,
            )

        embed_latest: discord.Embed = base.copy()
        embed_all: discord.Embed = base.copy()

        # ALL
        if service in DONT_REVERSE:
            for field in feeddict.fields:
                embed_all.add_field(name=field.name, value=field.value, inline=False)
        else:
            for field in reversed(feeddict.fields):
                embed_all.add_field(name=field.name, value=field.value, inline=False)

        before_fields = len(embed_all.fields)
        if before_fields > 25:
            dict_embed = embed_all.to_dict()
            dict_embed["fields"] = dict_embed["fields"][-25:]
            embed_all = discord.Embed.from_dict(dict_embed)
            embed_all.set_field_at(
                0,
                name="{} earlier updates were ommited.".format(before_fields - 24),
                value="This is because embeds are limited to 25 fields.",
            )

        # LATEST
        # TODO: if two are published in quick succession could miss one
        # Note to self for above, iterate through fields and compare against feed store
        if service in DONT_REVERSE:
            embed_latest.add_field(
                name=feeddict.fields[-1].name,
                value=feeddict.fields[-1].name,
                inline=False,
            )
        else:
            embed_latest.add_field(
                name=feeddict.fields[0].name,
                value=feeddict.fields[0].value,
                inline=False,
            )

        t = feeddict.title
        l = feeddict.link
        n = FEED_FRIENDLY_NAMES[service]
        plain_latest = f"**{n} Status Update\n{t}**\nIncident link: {l}\n\n"
        plain_all = f"**{n} Status Update\n{t}**\nIncident link: {l}\n\n"

        if service in DONT_REVERSE:
            for i in feeddict.fields:
                n = i.name
                v = i.value
                plain_all += f"**{n}**\n{v}\n"
        else:
            for i in reversed(feeddict.fields):
                n = i.name
                v = i.value
                plain_all += f"**{n}**\n{v}\n"

        if service in DONT_REVERSE:
            n = feeddict.fields[-1].name
            v = feeddict.fields[-1].name
            plain_latest += f"**{n}**\n{v}\n"

        else:
            n = feeddict.fields[0].name
            v = feeddict.fields[0].name
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
            if service in DONT_REVERSE:
                last_title = feeddict.fields[-1].name
                status = last_title.split(" ")[0].lower()
            else:
                last_title = feeddict.fields[0].name
                status = last_title.split(" ")[0].lower()
            if status == "investigating":
                return discord.Color.red()
            elif status in [
                "update",
                "identified",
                "monitoring",
                "scheduled",  # decided to put this in orange as is in future, not now
                "in",  # scheduled - full is "in progress"
            ]:
                return discord.Color.orange()
            elif status in ["resolved", "completed"]:
                return discord.Color.green()
            else:
                return 1812720
        except Exception as e:  # hopefully never happens but will keep this for a while
            log.error(f"Error with getting correct colour for {service}:", exc_info=e)
            return 1812720

    async def _send_updated_feed(self, feeddict: FeedDict, channel: tuple, service: str):
        """Send a feeddict to the specified channel."""
        mode = channel[1]["mode"]
        use_webhook = channel[1]["webhook"]
        id = channel[1].get("edit_id", {}).get(feeddict.link)
        c_id = channel[0]
        channel: discord.TextChannel = self.bot.get_channel(c_id)
        if channel is None:
            try:
                channel = await self.bot.fetch_channel(c_id)
            except:
                log.info(
                    f"Unable to get channel {c_id} for status update. Removing from config so this won't happen again."
                )
                await self.config.channel_from_id(c_id).feeds.clear()
                return
        if await self.bot.cog_disabled_in_guild(self, channel.guild):
            log.debug(f"Skipping channel {c_id} as cog is disabled in that guild.")
            return
        if use_webhook and not channel.permissions_for(channel.guild.me).manage_webhooks:
            log.debug(
                f"Unable to send a webhook to {c_id} in guild {channel.guild.id} - sending normal instead"
            )
            use_webhook = False
        if not use_webhook and not channel.permissions_for(channel.guild.me).send_messages:
            log.info(
                f"Unable to send messages to {c_id} in guild {channel.guild.id}. Removing from config so this won't happen again."
            )
            await self.config.channel_from_id(c_id).feeds.clear()
            return
        if not use_webhook:
            use_embed = await self.bot.embed_requested(channel, None)
        else:
            use_embed = True

        # the efficiecy could probably be improved here
        if use_embed:
            if mode in ["all", "edit"]:
                embed = self.send_cache.embed_all
            elif mode == "latest":
                embed = self.send_cache.embed_latest
            else:
                return

            try:
                # thanks flare for your webhook logic (redditpost) (or trusty?)
                if use_webhook:
                    if channel.guild.me.nick:
                        botname = channel.guild.me.nick
                    else:
                        botname = channel.guild.me.name
                    embed.set_footer(text=f"Powered by {botname}")
                    webhook = None
                    for hook in await channel.webhooks():
                        if hook.name == channel.guild.me.name:
                            webhook = hook
                    if webhook is None:
                        webhook = await channel.create_webhook(
                            name=channel.guild.me.name, reason=WEBHOOK_REASON.format(service)
                        )
                    if mode == "edit":
                        if id is not None:
                            try:
                                await webhook.edit_message(id, embed=embed, content=None)
                            except discord.NotFound:
                                id = None
                            # im sure there's a better way to do this
                        if id is None:
                            sent_webhook = await webhook.send(
                                username=f"{FEED_FRIENDLY_NAMES[service]} Status Update",
                                avatar_url=AVATAR_URLS[service],
                                embed=embed,
                                wait=True,
                            )
                            async with self.config.channel(channel).feeds() as conf:
                                if conf[service].get("edit_id") is None:
                                    conf[service]["edit_id"] = {feeddict.link: sent_webhook.id}
                                else:
                                    conf[service]["edit_id"][feeddict.link] = sent_webhook.id
                    else:
                        await webhook.send(
                            username=f"{FEED_FRIENDLY_NAMES[service]} Status Update",
                            avatar_url=AVATAR_URLS[service],
                            embed=embed,
                        )
                else:
                    embed.set_author(
                        name=f"{FEED_FRIENDLY_NAMES[service]} Status Update",
                        icon_url=AVATAR_URLS[service],
                    )
                    if mode == "edit":
                        if id is not None:
                            try:
                                msg: discord.Message = await channel.fetch_message(id)
                                await msg.edit(embed=embed, content=None)
                            except discord.NotFound:
                                id = None
                        if id is None:
                            sent_message: discord.Message = await channel.send(embed=embed)
                            async with self.config.channel(channel).feeds() as conf:
                                if conf[service].get("edit_id") is None:
                                    conf[service]["edit_id"] = {feeddict.link: sent_message.id}
                                else:
                                    conf[service]["edit_id"][feeddict.link] = sent_message.id
                    else:
                        await channel.send(embed=embed)
            except Exception as e:
                log.info(  # TODO: remove from config
                    f"Somehting went wrong with {c_id} in guild {channel.guild.id} - skipping", exc_info=e
                )
                return

        else:
            if mode in ["all", "edit"]:
                msg = self.send_cache.plain_all
            elif mode == "latest":
                msg = self.send_cache.plain_latest

            try:
                if mode == "edit":
                    if id is not None:
                        old_msg = await channel.fetch_message(id)
                        await old_msg.edit(content=msg, embed=None)
                    else:
                        sent_message = await channel.send(msg)
                        async with self.config.channel(channel).feeds() as conf:
                            if conf[service].get("edit_id") is None:
                                conf[service]["edit_id"] = {feeddict.get(feeddict.link): sent_message.id}
                            else:
                                conf[service]["edit_id"][feeddict.get(feeddict.link)] = sent_message.id
                else:
                    await channel.send(msg)
            except Exception as e:
                log.info(  # TODO: remove from config
                    f"Something went wrong with {c_id} in guild {channel.guild.id} - skipping", exc_info=e
                )

        await self._channel_send_dispatch(feeddict, service, channel, use_webhook, use_embed, mode)

    @guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def statusset(self, ctx: commands.Context):
        """Base command for managing the Status cog."""

    @statusset.command(name="add")
    async def statusset_add(
        self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel]
    ):
        """
        Start getting status updates for the choses service!

        There is a list of services you can use in the `[p]statusset list` command.

        You can use the `[p]statusset preview` command to see how different options look.

        If you don't specify a specific channel, I will use the current channel.

        This is an interactive command.
        """
        channel = channel or ctx.channel
        service = service.lower()

        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")
        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send(f"I don't have permission to send messages in {channel.mention}")
        feeds = await self.config.channel(channel).feeds()
        if service in feeds.keys():
            return await ctx.send(
                f"{channel.mention} already receives {FEED_FRIENDLY_NAMES[service]} status updates!"
            )

        friendly = FEED_FRIENDLY_NAMES[service]

        modes = ""
        unsupported = []
        modes += (
            "**All**: Every time the service posts an update on an incident, I will send a new message "
            "contaning the previus updates as well as the new update. Best used in a fast-moving "
            "channel with other users.\n\n"
            "**Latest**: Every time the service posts an update on an incident, I will send a new message "
            "contanint only the latest update. Best used in a dedicated status channel.\n\n"
            "**Edit**: When a new incident is created, I will sent a new message. When this incident is "
            "updated, I will then add the update to the original message. Best used in a dedicated status "
            "channel.\n\n"
        )
        if ALL not in AVALIBLE_MODES[service]:
            unsupported.append(ALL)
        if LATEST not in AVALIBLE_MODES[service]:
            unsupported.append(LATEST)
        if EDIT not in AVALIBLE_MODES[service]:
            unsupported.append(EDIT)

        if unsupported:
            if len(unsupported) > 1:
                extra = "s"
            else:
                extra = ""
            unsupported = humanize_list(unsupported)
            modes += f"Due to {friendly} limitations, I can't support the `{unsupported}` mode{extra}\n\n"

        await ctx.send(
            "This is an interactive configuration. You have 2 minutes to answer each question.\n"
            f"If you aren't sure what to choose, just say `cancel` and take a look at the **`{ctx.clean_prefix}"
            f"statusset preview`** command.\n\n**What mode do you want to use?**\n\n{modes}"
        )

        try:
            mode = await self.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=120)
        except TimeoutError:
            return await ctx.send("Timed out. Canceling.")

        mode = mode.content.lower()
        if mode not in [ALL, LATEST, EDIT]:
            return await ctx.send("Hmm, that doesn't look like a valid mode. Canceling.")

        if ctx.channel.permissions_for(ctx.me).manage_webhooks:
            await ctx.send(
                "**Would you like to use a webhook?** (yes or no answer)\nUsing a webhook means that the status "
                f"updates will be sent with the avatar as {friendly}'s logo and the name will be `{friendly} "
                "Status Update`, instead of my avatar and name. If you aren't sure, say `yes`."
            )

            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred, timeout=120)
            except TimeoutError:
                return await ctx.send("Timed out. Canceling.")

            if pred.result is True:
                webhook = True

                # already checked for perms to create
                # thanks flare for your webhook logic (redditpost) (or trusty?)
                existing_webhook = False
                for hook in await channel.webhooks():
                    if hook.name == channel.guild.me.name:
                        existing_webhook = True
                if not existing_webhook:
                    await channel.create_webhook(
                        name=channel.guild.me.name, reason=WEBHOOK_REASON.format(service)
                    )
            else:
                webhook = False
        else:
            await ctx.send(
                "I would ask about whether you want me to send updates as a webhook (so they match the "
                "service), however I don't have the `manage webhooks` permission."
            )
            webhook = False

        settings = {"mode": mode, "webhook": webhook, "edit_id": {}}
        await self.config.channel(channel).feeds.set_raw(service, value=settings)
        self.used_feeds_cache.add_feed(service)

        if service in SPECIAL_INFO:
            await ctx.send(
                f"Note: {SPECIAL_INFO[service]}\n{channel.mention} will now receive {FEED_FRIENDLY_NAMES[service]} status updates."
            )
        else:
            await ctx.send(
                f"Done, {channel.mention} will now receive {FEED_FRIENDLY_NAMES[service]} status updates."
            )

    @statusset.command(name="remove", aliases=["del", "delete"])
    async def statusset_remove(
        self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel]
    ):
        """
        Stop status updates for a specific service in this server.

        If you don't specify a channel, I will use the current channel.
        """
        channel = channel or ctx.channel

        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")

        channel_conf = self.config.channel(channel)
        async with channel_conf.feeds() as feeds:
            if service not in feeds.keys():
                return await ctx.send(
                    f"It looks like I don't send {FEED_FRIENDLY_NAMES[service]} status updates to {channel.mention}"
                )
            feeds.pop(service)

        self.used_feeds_cache.remove_feed(service)

        await ctx.send(f"Removed {FEED_FRIENDLY_NAMES[service]} status updates from {channel.mention}")

    @statusset.command(name="list", aliases=["show", "settings"])
    async def statusset_list(self, ctx: commands.Context, service: Optional[str]):
        """
        List that available services and which ones are being used in this server.

        Optionally add a service at the end of the command to view detailed settings for that service.
        """
        unused_feeds = list(FEED_URLS.keys())

        if service:
            if service not in FEED_FRIENDLY_NAMES.keys():
                return await ctx.send(
                    f"That doesn't look like a valid service. You can run `{ctx.clean_prefix}statusset list` "
                    "with no arguments."
                )
            data = []
            for channel in ctx.guild.channels:
                feeds = await self.config.channel(channel).feeds()
                for name, data in feeds.items():
                    if name != service:
                        continue
                    mode = data["mode"]
                    webhook = data["webhook"]
                    data.append([f"#{channel.name}", mode, webhook])
            table = box(tabulate(data, headers=["Channel", "Send mode", "Use webhooks"]))
            await ctx.send(f"**Settings for {FEED_FRIENDLY_NAMES[service]}**: {table}")

        else:
            guild_feeds = {}
            for channel in ctx.guild.channels:
                feeds = await self.config.channel(channel).feeds()
                for feed in feeds.keys():
                    try:
                        guild_feeds[feed].append(f"#{channel.name}")
                    except KeyError:
                        guild_feeds[feed] = [f"#{channel.name}"]

            if not guild_feeds:
                msg = "There are no status updates set up in this server.\n"
            else:
                msg = ""
                data = []
                for name, settings in guild_feeds.items():
                    if not settings:
                        continue
                    data.append([name, humanize_list(settings)])
                    try:
                        unused_feeds.remove(name)
                    except Exception:
                        pass
                if data:
                    msg += "**Services used in this server:**"
                    msg += box(tabulate(data, tablefmt="plain"), lang="arduino")
            if unused_feeds:
                msg += "**Other available services:** "
                msg += humanize_list(unused_feeds)
            msg += (
                f"\nTo see settings for a specific service, run `{ctx.clean_prefix}statusset list <service>`"
            )
            await ctx.send(msg)

    @statusset.command(name="preview")
    async def statusset_preview(self, ctx: commands.Context, service: str, mode: str, webhook: bool):
        """
        Preview what status updates will look like

        __**Service**__
        The service you want to preview. There's a list of available services in the
        `[p]statusset list` command.

        **`<mode>`**
            **All**: Every time the service posts an update on an incident, I will send
            a new message contaning the previus updates as well as the new update. Best
            used in a fast-moving channel with other users.

            **Latest**: Every time the service posts an update on an incident, I will send
            a new message contaning only the latest update. Best used in a dedicated status
            channel.

            **Edit**: Natually, edit mode can't have a preview so won't work with this command.
            The message content is the same as the `all` mode.
            When a new incident is created, I will sent a new message. When this
            incident is updated, I will then add the update to the original message. Best
            used in a dedicated status channel.


        **`<webhook>`**
            Using a webhook means that the status updates will be sent with the avatar
            as the service's logo and the name will be `[service] Status Update`, instead
            of my avatar and name.
        """
        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")

        mode = mode.casefold()
        if mode not in [ALL, LATEST]:
            return await ctx.send(
                f"That's not a valid mode. Valid ones are listed in `{ctx.clean_prefix}help statusset preview`"
            )
        if mode not in AVALIBLE_MODES[service]:
            return await ctx.send(f"That mode isn't avalible for {FEED_FRIENDLY_NAMES[service]}")

        if webhook and not ctx.channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.send(f"I don't have permission to manage webhooks.")

        feed = await self.config.feed_store()
        feeddict = feed.get(service)
        if feeddict is None or feeddict.get("link") is None or feeddict.get("time") is None:
            async with aiohttp.ClientSession() as session:
                async with session.get(FEED_URLS[service]) as response:
                    html = await response.text()
                await session.close()
            feed = feedparser.parse(html)
            feeddict = await self._process_feed(service, feed)
        else:
            feeddict["time"] = datetime.datetime.fromtimestamp(feeddict["time"])
            feeddict = FeedDict.from_dict(feeddict)

        await self._make_send_cache(feeddict, service)
        channel = (ctx.channel.id, {"mode": mode, "webhook": webhook})

        try:
            await self._send_updated_feed(feeddict, channel, service)
        except KeyError:
            await ctx.send("Hmm, I couldn't preview that.")

    @guild_only()
    @statusset.group(name="edit")
    async def statusset_edit(self, ctx):
        """Base command for editing services"""

    @statusset_edit.command(name="mode")
    async def statusset_edit_mode(
        self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel], mode: str
    ):
        """Change what mode to use for updates

        **All**: Every time the service posts an update on an incident, I will send a new message
        contaning the previus updates as well as the new update. Best used in a fast-moving
        channel with other users.

        **Latest**: Every time the service posts an update on an incident, I will send a new message
        contaning only the latest update. Best used in a dedicated status channel.

        **Edit**: When a new incident is created, I will sent a new message. When this incident is
        updated, I will then add the update to the original message. Best used in a dedicated
        status channel.

        If you don't specify a channel, I will use the current channel.
        """
        channel = channel or ctx.channel
        service = service.lower()
        mode = mode.lower()

        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")

        old_conf = await self.config.channel(channel).feeds()
        if service not in old_conf.keys():
            return await ctx.send(
                f"It looks like I don't send {FEED_FRIENDLY_NAMES[service]} status updates to {channel.mention}"
            )

        if mode not in [ALL, LATEST, EDIT]:
            return await ctx.send("That doesn't look like a valid mode. It can be `all` or `latest`")
        if mode not in AVALIBLE_MODES[service]:
            return await ctx.send(f"That mode isn't avalible for {FEED_FRIENDLY_NAMES[service]}")

        if old_conf[service]["mode"] == mode:
            return await ctx.send(
                f"It looks like I already use that mode for {FEED_FRIENDLY_NAMES[service]} updates in {channel.mention}"
            )

        old_conf[service]["mode"] = mode
        await self.config.channel(channel).feeds.set_raw(service, value=old_conf[service])

        await ctx.send(
            f"{FEED_FRIENDLY_NAMES[service]} status updates in {channel.mention} will now use the {mode} mode."
        )

    @statusset_edit.command(name="webhook")
    async def statusset_edit_webhook(
        self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel], webhook: bool
    ):
        """Set whether or not to use webhooks to send the status update

        Using a webhook means that the status updates will be sent with the avatar as the service's
        logo and the name will be `[service] Status Update`, instead of my avatar and name.

        If you don't specify a channel, I will use the current channel.
        """
        channel = channel or ctx.channel
        service = service.lower()

        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")

        old_conf = await self.config.channel(channel).feeds()
        if service not in old_conf.keys():
            return await ctx.send(
                f"It looks like I don't send {FEED_FRIENDLY_NAMES[service]} status updates to {channel.mention}"
            )

        if old_conf[service]["webhook"] == webhook:
            if webhook:
                word = "use"
            else:
                word = "don't use"
            return await ctx.send(
                f"It looks like I already {word} webhooks for {FEED_FRIENDLY_NAMES[service]} status updates in {channel.mention}"
            )

        if webhook and not ctx.channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.send("I don't have manage webhook permissions so I can't do that.")

        old_conf[service]["edit_id"] = {}
        old_conf[service]["webhook"] = webhook
        await self.config.channel(channel).feeds.set_raw(service, value=old_conf[service])

        if webhook:
            word = "use"
        else:
            word = "not use"
        await ctx.send(
            f"{FEED_FRIENDLY_NAMES[service]} status updates in {channel.mention} will now {word} webhooks."
        )

    # -------------------------
    # STARTING THE DEV COMMANDS
    # -------------------------

    async def _dev_com(self, ctx: commands.Context):
        """Returns whether to continue or not"""
        if ctx.author.id != 418078199982063626:  # vexed (my) id
            msg = await ctx.send(
                warning(
                    "\nTHIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.\n\nUnintended things can "
                    "happen.\n\nRepeat: THIS COMMAND IS NOT SUPPORTED.\nAre you sure you want to continue?"
                )
            )
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            await ctx.bot.wait_for("reaction_add", check=pred, timeout=120)
            if pred.result is not True:
                await ctx.send("Aborting.")
                return False
        return True

    @checks.is_owner()
    @commands.group(hidden=True)
    async def statusdev(self, ctx: commands.Context):
        """hey dont use this, it's all hidden for a reason"""

    @statusdev.command(hidden=True, aliases=["fs"])
    async def forcestatus(self, ctx: commands.Context, service):
        if not await self._dev_com(ctx):
            return

        if service not in FEED_URLS.keys():
            return await ctx.send("Hmm, that doesn't look like a valid service.")

        async with aiohttp.ClientSession() as session:
            async with session.get(FEED_URLS[service]) as response:
                html = await response.text()
            await session.close()
        fp_data = feedparser.parse(html)
        feeddict = await self._process_feed(service, fp_data)
        real = await self._check_real_update(service, feeddict)
        await ctx.send(f"Real update: {real}")
        channels = await self._get_channels(service)
        await self._make_send_cache(feeddict, service)
        await self._update_dispatch(feeddict, fp_data, service, channels, True)
        await asyncio.sleep(1)
        log.debug(f"Sending to {len(channels)}")
        for channel in channels.items():
            await self._send_updated_feed(feeddict, channel, service)

    @guild_only()
    @statusdev.command(aliases=["cf"], hidden=True)
    async def checkfeed(self, ctx: commands.Context, link, mode, service):
        if not await self._dev_com(ctx):
            return

        link = FEED_URLS.get(link, link)
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                html = await response.text()
            await session.close()
        feed = feedparser.parse(html)

        feeddict = await _helper_process_feed(service, feed)
        # await self._make_send_cache(feeddict, service)
        return await self._send_updated_feed(
            feeddict, (ctx.channel.id, {"mode": mode, "webhook": False}), service
        )

    @statusdev.command(aliases=["cfr"], hidden=True)
    async def checkfeedraw(self, ctx: commands.Context, link: str):
        if not await self._dev_com(ctx):
            return

        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                html = await response.text()
            await session.close()
        feed = feedparser.parse(html)

        # feed = await _helper_process_feed("twitter", feed)
        # feed = feed.to_dict()

        pages = pagify(str(feed.entries[0]))

        await ctx.send_interactive(pages, box_lang="")

    @statusdev.command(aliases=["cfc"], hidden=True)
    async def checkusedfeedcache(self, ctx: commands.Context):
        if not await self._dev_com(ctx):
            return

        raw = box(self.used_feeds_cache.raw, lang="py")
        actual = box(self.used_feeds_cache.get_list(), lang="py")
        await ctx.send(f"**Raw data:**\n{raw}\n**Active:**\n{actual}")
