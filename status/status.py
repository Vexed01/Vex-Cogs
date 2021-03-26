# HELLO!
# This file is formatted with black, line length 120
# If you are looking for an event your cog can listen to, take a look here:
# https://vex-cogs.readthedocs.io/en/latest/statusdev.html

# ======== PLEASE READ ======================================================
# Status is currently a bit of a mess. For this reason, I'll be undertaking a
# rewrite in the near future: https://github.com/Vexed01/Vex-Cogs/issues/13
#
# For this reason, unless it's minor, PLEASE DO NOT OPEN A PR.
# ===========================================================================

import asyncio
import datetime
import logging
from math import floor
from time import time
from typing import Optional

import aiohttp
import discord
import feedparser
from discord.ext import tasks
from discord.ext.commands.core import guild_only
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, humanize_timedelta, pagify, warning
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
from tabulate import tabulate

from .consts import *
from .objects import FeedDict, ServiceRestrictionsCache, UsedFeeds
from .rsshelper import process_feed as helper_process_feed
from .sendupdate import SendUpdate
from .utils import deserialize, serialize

_base_log = logging.getLogger("red.vexed.status")
_update_checker_log = logging.getLogger("red.vexed.status.updatechecker")


# cspell:ignore DONT


class Status(commands.Cog):
    """
    Automatically check for status updates.

    When there is one, it will send the update to all channels that
    have registered to recieve updates from that service.

    If there's a service that you want added, contact Vexed#3211 or
    make an issue on the GitHub repo (or even better a PR!).
    """

    __version__ = "1.4.1"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        docs = "This cog has docs! Check them out at\nhttps://vex-cogs.readthedocs.io/en/latest/cogs/status.html"
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**\n{docs}"
        # adding docs link here so doesn't show up in auto generated docs

    def __init__(self, bot: Red):
        self.bot = bot

        # config
        default = {}
        self.config: Config = Config.get_conf(self, identifier="Vexed-status")  # shit idntfr. bit late to change it...
        self.config.register_global(version=1)
        self.config.register_global(etags=default)
        self.config.register_global(incidents=default)
        self.config.register_global(latest=default)  # this is unused? i think? remove soonish
        self.config.register_channel(feeds=default)
        self.config.register_guild(service_restrictions=default)

        # objects
        self.used_feeds_cache = None
        self.service_restrictions_cache = None
        self.sendupdate = SendUpdate(config=self.config, bot=self.bot)
        self.session = aiohttp.ClientSession()

        # async stuff
        asyncio.create_task(self._async_init())

    def cog_unload(self):
        self._check_for_updates.cancel()
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    async def _async_init(self):
        await self.bot.wait_until_red_ready()

        self.used_feeds_cache = UsedFeeds(await self.config.all_channels())
        self.service_restrictions_cache = ServiceRestrictionsCache(await self.config.all_guilds())

        if await self.config.version() != 2:
            _base_log.info("Getting initial data from services...")
            await self._migrate()
            _base_log.info("Done!")

        self._check_for_updates.start()

        _base_log.info("Status cog has been successfully initialized.")

    @tasks.loop(minutes=2.0)
    async def _check_for_updates(self):
        """Loop dealing with automatic updates."""
        if not self.used_feeds_cache.get_list():
            _update_checker_log.debug("Nothing to do, no channels have registered a feed.")
            return

        try:
            await asyncio.wait_for(self._actually_check_updates(), timeout=110.0)  # 1 min 50 secs
        except asyncio.TimeoutError:
            _update_checker_log.error(
                "Loop timed out after 1 minute 50 seconds. Will try again shortly. If this keeps happening "
                "when there's an update for a specific service, contact Vexed."
            )
        except Exception as e:
            _update_checker_log.error(
                "Unable to check (and send) updates. Some services were likely skipped. If they had updates, "
                "they should send on the next loop.",
                exc_info=e,
            )

    async def _actually_check_updates(self):
        """The actual update logic"""
        for service in self.used_feeds_cache.get_list():
            async with self.config.etags() as etags:
                try:
                    async with self.session.get(
                        FEED_URLS[service], headers={"If-None-Match": etags[service]}, timeout=10
                    ) as response:
                        html = await response.text()
                        status = response.status
                        if status == 200:
                            etags[service] = response.headers.get("ETag")
                except KeyError:
                    async with self.session.get(FEED_URLS[service], timeout=10) as response:
                        html = await response.text()
                        status = response.status
                    if service != "gcp":  # gcp doesn't do etags
                        etags[service] = response.headers.get("ETag")
                except asyncio.TimeoutError:
                    _update_checker_log.warning(f"Timeout checking for {service} update")
                    continue
                except Exception as e:
                    _update_checker_log.warning(f"Unable to check for an update for {service}", exc_info=e)
                    continue

            if status == 200:
                await self.sendupdate._maybe_send_update(html, service)
            elif status == 304:  # not modified
                _update_checker_log.debug(f"No new status update for {service}")
            elif status == 429:
                _update_checker_log.warning(
                    f"Unable to get an update for {service}. It looks like we're being rate limited (429). This "
                    "should never happen; therefore this cog does not handle rate limits. Please tell Vexed about "
                    "this and for ways to mitigate this."
                )
            elif str(status)[0] == "5":  # 500 status code
                _update_checker_log.info(
                    f"Unable to get an update for {service} - internal server error on the status page "
                    f"(HTTP Error {status})"
                )
            else:
                _update_checker_log.info(
                    f"Unexpected status code received from {service}: {status}\nPlease report this to Vexed."
                )

        async with self.config.incidents() as incidents:
            for service in self.used_feeds_cache.get_list():
                incidents["checked"][service] = time()

    async def _migrate(self):
        """Migrate config format"""
        incidents = dict.fromkeys(FEED_URLS.keys(), {})
        incidents["latest"] = {}
        incidents["checked"] = {}
        for service, url in FEED_URLS.items():
            json_ready = {}
            _base_log.debug(f"Starting {service}.")
            try:
                async with self.session.get(url, timeout=10) as response:
                    html = await response.text()
            except Exception:
                _base_log.warning(f"Unable to migrate {service} properly. This won't affect the automatic updates.")
                continue
            if response.status == 200:
                fp_data = feedparser.parse(html)
                feeds = self.sendupdate._process_feed(service, fp_data)
                for feed in feeds:  # do latest last for stuff just after loop
                    feed = feed.to_dict()
                    json_ready[feed["link"]] = serialize(feed)

            incidents["latest"][service] = feeds[0].link
            incidents["checked"][service] = time()
            incidents[service] = json_ready

        await self.config.incidents.set(incidents)
        await self.config.feed_store.clear()
        await self.config.version.set(2)

    # TODO: support DMs
    @guild_only()
    @commands.cooldown(2, 120, commands.BucketType.user)
    @commands.command()
    async def status(self, ctx: commands.Context, service: str):
        """
        Check for incidents for a variety of services, eg Discord.

        discord, github, zoom, reddit, epic_games, cloudflare, statuspage,
        python, twitter_api, oracle_cloud, twitter, digitalocean, aws, gcp,
        smartthings, sentry, status.io
        """
        service = service.lower()
        if service not in FEED_URLS.keys():
            return await ctx.send(
                f"It looks like that isn't a valid service. Run the command `{ctx.clean_prefix}status` on its own to "
                "see available services."
            )

        restrictions = self.service_restrictions_cache.get_guild(ctx.guild.id, service)
        if restrictions:
            channels = [self.bot.get_channel(channel) for channel in restrictions]
            channels = [channel.mention for channel in channels if channel]
            if channels:
                rest_list = humanize_list(channels, style="or")
                return await ctx.send(f"You can check updates for {FEED_FRIENDLY_NAMES[service]} in {rest_list}")

        incidents = await self.config.incidents()

        if service in CUSTOM_SERVICES:
            if abs(time() - incidents["checked"][service]) > 300:  # TODO: implement same logic as below to get feed
                return ctx.send("Sorry, I can't show status updates for that service at the moment.")
            feeddict = deserialize(incidents[service][incidents["latest"][service]])
            cache = await self.sendupdate._make_send_cache(feeddict, service, set_global=False)
            await self.sendupdate._channel_send_updated_feed(
                feeddict, (ctx.channel.id, {"mode": "all", "webhook": False}), service, dispatch=False, cache=cache
            )
            cache_time = humanize_timedelta(seconds=5 * floor(abs(time() - incidents["checked"][service]) / 5))
            cached_at = f"{cache_time} ago" if cache_time else "now"
            return await ctx.send(f"_This was cached {cached_at}._")

        if abs(time() - incidents["checked"][service]) > 180:  # 3 mins
            _base_log.debug(f"Unscheduled check of {service} triggered.")
            await ctx.trigger_typing()
            try:
                async with self.session.get(FEED_URLS[service], timeout=10) as response:
                    html = await response.text()
                if response.status != 200:
                    raise Exception
            except Exception:
                return await ctx.send("Hmm, I couldn't connect to their status page.")
            fp_data = feedparser.parse(html)
            feeds = self.sendupdate._process_feed(service, fp_data)

            json_ready = {}
            for feed in feeds:
                feed = feed.to_dict()
                json_ready[feed["link"]] = serialize(feed)

            async with self.config.incidents() as conf_incidents:
                conf_incidents["latest"][service] = feeds[0].link
                conf_incidents["checked"][service] = time()
                conf_incidents[service] = json_ready

            cached_at = "now"
            incidents = json_ready
        else:
            # this rounds down to nearest 5 then humanizes
            cache_time = humanize_timedelta(seconds=5 * floor(abs(time() - incidents["checked"][service]) / 5))
            cached_at = f"{cache_time} ago" if cache_time else "now"
            incidents = {i["link"]: serialize(i) for i in incidents[service].values()}

        # improve this
        # links = []
        # incidents = []
        # for link, incident in old_incidents:
        #     if link not in links:
        #         incidents.append(incident)
        #         links.append(link)

        live = []
        recent_finished = []
        for _, incident in incidents.items():
            if not incident["actual_time"]:  # could be ""
                _base_log.debug("Unknown time")
                continue
            elif abs(time() - incident["actual_time"]) > (60 * 60 * 24):  # 1 day
                continue
            elif incident["fields"][-1]["name"].startswith(("Resolved", "Completed", "Scheduled")):
                recent_finished.append(incident)
            else:
                live.append(incident)

        if not live:
            msg = "\N{WHITE HEAVY CHECK MARK} There are currently no live incidents."
            if recent_finished:
                msg += f"\n\n{len(recent_finished)} incident(s) were resolved in the last 24 hours:"
                for incident in recent_finished:
                    msg += "\n{}: <{}>".format(incident["title"], incident["link"])
            return await ctx.send(f"{msg}\n_This was cached {cached_at}._")

        feeddict = deserialize(live[0])
        cache = await self.sendupdate._make_send_cache(feeddict, service, False)
        await self.sendupdate._channel_send_updated_feed(
            feeddict, (ctx.channel.id, {"mode": "all", "webhook": False}), service, dispatch=False, cache=cache
        )

        msg = ""
        others = len(live) - 1
        num_recent_finished = len(recent_finished)
        if others:
            msg += f"{others} other incident(s) are live at the moment:"
            for incident in live[1:]:
                msg += "\n{} (<{}>)".format(incident["title"], incident["link"])
            msg += "\n\n"
        if num_recent_finished:
            msg += f"{num_recent_finished} other incident(s) were resolved in the last 24 hours:"
            for incident in recent_finished:
                resolved_at = humanize_timedelta(seconds=abs(time() - incident["actual_time"]))
                msg += "\nResolved at {} - {} (<{}>)".format(resolved_at, incident["title"], incident["link"])

        await ctx.send(f"{msg}\n_This was cached {cached_at}._")

    @guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def statusset(self, ctx: commands.Context):
        """
        Get automatic status updates in a channel, eg Discord.

        Get started with `[p]statusset preview` to see what they look like,
        then `[p]statusset add` to set up automatic updates.

        **Available services:**
        **`discord`**, `github`, `cloudflare`, `python`, `twitter_api`, `statuspage`,
        **`zoom`**, `oracle_cloud`, `twitter`, **`epic_games`**, `digitalocean`, **`reddit`**,
        `aws`,`gcp`, `smartthings`, `sentry`, `status.io`
        """

    @statusset.command(name="add")
    async def statusset_add(self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel]):
        """
        Start getting status updates for the chosen service!

        There is a list of services you can use in the `[p]statusset list` command.

        You can use the `[p]statusset preview` command to see how different options look.

        If you don't specify a specific channel, I will use the current channel.

        This is an interactive command. It will ask what mode you want to use and if you
        want to use a webhook. There's more information about these options in the
        command.
        """
        channel = channel or ctx.channel
        service = service.lower()

        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")
        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send(f"I don't have permission to send messages in {channel.mention}")
        feeds = await self.config.channel(channel).feeds()
        if service in feeds.keys():
            return await ctx.send(f"{channel.mention} already receives {FEED_FRIENDLY_NAMES[service]} status updates!")

        friendly = FEED_FRIENDLY_NAMES[service]

        modes = ""
        unsupported = []
        modes += (
            "**All**: Every time the service posts an update on an incident, I will send a new message "
            "containing the previous updates as well as the new update. Best used in a fast-moving "
            "channel with other users.\n\n"
            "**Latest**: Every time the service posts an update on an incident, I will send a new message "
            "containing only the latest update. Best used in a dedicated status channel.\n\n"
            "**Edit**: When a new incident is created, I will sent a new message. When this incident is "
            "updated, I will then add the update to the original message. Best used in a dedicated status "
            "channel.\n\n"
        )
        if ALL not in AVAILABLE_MODES[service]:
            unsupported.append(ALL)
        if LATEST not in AVAILABLE_MODES[service]:
            unsupported.append(LATEST)
        if EDIT not in AVAILABLE_MODES[service]:
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
        except asyncio.TimeoutError:
            return await ctx.send("Timed out. Cancelling.")

        mode = mode.content.lower()
        if mode not in [ALL, LATEST, EDIT]:
            return await ctx.send("Hmm, that doesn't look like a valid mode. Cancelling.")
        if mode in unsupported:
            return await ctx.send("That mode is not supported for this service.")

        if ctx.channel.permissions_for(ctx.me).manage_webhooks:
            await ctx.send(
                "**Would you like to use a webhook?** (yes or no answer)\nUsing a webhook means that the status "
                f"updates will be sent with the avatar as {friendly}'s logo and the name will be `{friendly} "
                "Status Update`, instead of my avatar and name. If you aren't sure, say `yes`."
            )

            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred, timeout=120)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out. Cancelling.")

            if pred.result is True:
                webhook = True

                # already checked for perms to create
                # thanks flare for your webhook logic (redditpost) (or trusty?)
                existing_webhook = False
                for hook in await channel.webhooks():
                    if hook.name == channel.guild.me.name:
                        existing_webhook = True
                if not existing_webhook:
                    await channel.create_webhook(name=channel.guild.me.name, reason=WEBHOOK_REASON.format(service))
            else:
                webhook = False
        else:
            await ctx.send(
                "I would ask about whether you want me to send updates as a webhook (so they match the "
                "service), however I don't have the `manage webhooks` permission."
            )
            webhook = False

        await ctx.send(
            f"**Would you like to restrict access to {friendly} in the `{ctx.clean_prefix}status` command?** "
            "(yes or no answer)\nThis will reduce spam. If there's an incident, members will instead be redirected "
            f"to {channel.mention} and any other channels that you've set to receive {friendly} status updates. They "
            "will be redirected to all channels that have restrict - not all channels with the status update."
        )

        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out. Cancelling.")

        if pred.result == True:
            async with self.config.guild(ctx.guild).service_restrictions() as sr:
                try:
                    sr[service].append(channel.id)
                except ValueError:
                    sr[service] = [channel.id]

        settings = {"mode": mode, "webhook": webhook, "edit_id": {}}
        await self.config.channel(channel).feeds.set_raw(service, value=settings)
        self.used_feeds_cache.add_feed(service)

        if service in SPECIAL_INFO:
            await ctx.send(
                f"Note: {SPECIAL_INFO[service]}\n{channel.mention} will now receive {FEED_FRIENDLY_NAMES[service]} status updates."
            )
        else:
            await ctx.send(f"Done, {channel.mention} will now receive {FEED_FRIENDLY_NAMES[service]} status updates.")

    @statusset.command(name="remove", aliases=["del", "delete"])
    async def statusset_remove(self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel]):
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

        async with self.config.guild(ctx.guild).service_restrictions() as sr:
            try:
                sr[service].remove(channel.id)
            except ValueError:
                sr[service] = [channel.id]

        await ctx.send(f"Removed {FEED_FRIENDLY_NAMES[service]} status updates from {channel.mention}")

    @statusset.command(name="list", aliases=["show", "settings"])
    async def statusset_list(self, ctx: commands.Context, service: Optional[str]):
        """
        List that available services and ones are used in this server.

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
                restrictions = await self.config.guild(ctx.guild).service_restrictions()
                for name, settings in feeds.items():
                    if name != service:
                        continue
                    mode = settings["mode"]
                    webhook = settings["webhook"]
                    # TODO: improve this bit below
                    try:
                        if channel.id in restrictions[service]:
                            restrict = True
                        else:
                            restrict = False
                    except KeyError:
                        restrict = False
                    data.append([f"#{channel.name}", mode, webhook, restrict])
            table = box(tabulate(data, headers=["Channel", "Send mode", "Use webhooks", "Restrict"]))
            friendly = FEED_FRIENDLY_NAMES[service]
            await ctx.send(
                f"**Settings for {friendly}**: {table}\n`Restrict` is whether or not to restrict access for "
                f"{friendly} server-wide in the `status` command. Users are redirected to an appropriate "
                "channel when there's an incident."
            )

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
                    msg += box(tabulate(data, tablefmt="plain"), lang="arduino")  # cspell:disable-line
            if unused_feeds:
                msg += "**Other available services:** "
                msg += humanize_list(unused_feeds)
            msg += f"\nTo see settings for a specific service, run `{ctx.clean_prefix}statusset list <service>`"
            await ctx.send(msg)

    @statusset.command(name="preview")
    async def statusset_preview(self, ctx: commands.Context, service: str, mode: str, webhook: bool):
        """
        Preview what status updates will look like.

        __**Service**__
        The service you want to preview. There's a list of available services in the
        `[p]statusset list` command.

        **`<mode>`**
            **All**: Every time the service posts an update on an incident, I will send
            a new message containing the previous updates as well as the new update. Best
            used in a fast-moving channel with other users.

            **Latest**: Every time the service posts an update on an incident, I will send
            a new message containing only the latest update. Best used in a dedicated status
            channel.

            **Edit**: Naturally, edit mode can't have a preview so won't work with this command.
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
        if mode not in AVAILABLE_MODES[service]:
            return await ctx.send(f"That mode isn't available for {FEED_FRIENDLY_NAMES[service]}")

        if webhook and not ctx.channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.send(f"I don't have permission to manage webhooks.")

        feed = await self.config.feed_store()
        feeddict = feed.get(service)
        if feeddict is None or feeddict.get("link") is None or feeddict.get("time") is None:
            async with self.session.get(FEED_URLS[service]) as response:
                html = await response.text()
            feed = feedparser.parse(html)
            feeddict = await self.sendupdate._process_feed(service, feed)
        else:
            feeddict["time"] = datetime.datetime.fromtimestamp(feeddict["time"])
            feeddict = FeedDict.from_dict(None, feeddict)

        cache = await self.sendupdate._make_send_cache(feeddict, service, set_global=False)

        channel = (ctx.channel.id, {"mode": mode, "webhook": webhook})
        try:
            await self.sendupdate._channel_send_updated_feed(feeddict, channel, service, False, cache=cache)
        except KeyError:
            await ctx.send("Hmm, I couldn't preview that.")

    @guild_only()
    @statusset.group(name="edit")
    async def statusset_edit(self, ctx):
        """Edit services you've already set up."""

    @statusset_edit.command(name="mode")
    async def statusset_edit_mode(
        self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel], mode: str
    ):
        """Change what mode to use for status updates.

        **All**: Every time the service posts an update on an incident, I will send a new message
        containing the previous updates as well as the new update. Best used in a fast-moving
        channel with other users.

        **Latest**: Every time the service posts an update on an incident, I will send a new message
        containing only the latest update. Best used in a dedicated status channel.

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
        if mode not in AVAILABLE_MODES[service]:
            return await ctx.send(f"That mode isn't available for {FEED_FRIENDLY_NAMES[service]}")

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
        """Set whether or not to use webhooks for status updates.

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
            word = "use" if webhook else "don't use"
            return await ctx.send(
                f"It looks like I already {word} webhooks for {FEED_FRIENDLY_NAMES[service]} status updates in {channel.mention}"
            )

        if webhook and not ctx.channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.send("I don't have manage webhook permissions so I can't do that.")

        old_conf[service]["edit_id"] = {}
        old_conf[service]["webhook"] = webhook
        await self.config.channel(channel).feeds.set_raw(service, value=old_conf[service])

        word = "use" if webhook else "not use"
        await ctx.send(f"{FEED_FRIENDLY_NAMES[service]} status updates in {channel.mention} will now {word} webhooks.")

    @statusset_edit.command(name="restrict")
    async def statusset_edit_restrict(
        self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel], restrict: bool
    ):
        """Restrict access to the service in the `status` command.

        Enabling this will reduce spam. Instead of sending the whole update
        (if there's an incident) members will instead be redirected to channels
        that automatically receive the status updates, that they have permission to to view.

        Note if there is no ongoing incident they will not redirected.
        """
        channel = channel or ctx.channel
        service = service.lower()

        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")

        feed_settings = await self.config.channel(channel).feeds()
        if service not in feed_settings.keys():
            return await ctx.send(
                f"It looks like I don't send {FEED_FRIENDLY_NAMES[service]} status updates to {channel.mention}"
            )

        old_conf = (await self.config.guild(ctx.guild).service_restrictions()).get(service, [])
        old_bool = channel.id in old_conf
        if old_bool == restrict:
            word = "" if restrict else "don't "
            return await ctx.send(
                f"It looks like I already {word}restrict {FEED_FRIENDLY_NAMES[service]} status updates for the "
                "`status` command."
            )

        async with self.config.guild(ctx.guild).service_restrictions() as sr:
            if restrict:
                try:
                    sr[service].append(channel.id)
                except KeyError:
                    sr[service] = [channel.id]
                self.service_restrictions_cache.add_restriction(ctx.guild.id, service, channel.id)
            else:
                sr[service].remove(channel.id)
                self.service_restrictions_cache.remove_restriction(ctx.guild.id, service, channel.id)

        word = "" if restrict else "not "
        await ctx.send(f"{FEED_FRIENDLY_NAMES[service]} will now {word}be restricted in the `status` command.")

    # -------------------------
    # STARTING THE DEV COMMANDS
    # -------------------------

    async def _dev_com(self, ctx: commands.Context):
        """Returns whether to continue or not"""
        if ctx.author.id != 418078199982063626:  # vexed (my) id
            msg = await ctx.send(
                warning(
                    "\nTHIS COMMAND IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.\n\nUnintended things can "
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

        async with self.session.get(FEED_URLS[service]) as response:
            html = await response.text()
        fp_data = feedparser.parse(html)
        feeddict = self.sendupdate._process_feed(service, fp_data)
        real = await self.sendupdate._check_real_update(service, feeddict)
        await ctx.send(f"Real update: {len(real)}")
        for feeddict in real:
            if feeddict is None:
                continue
            channels = await self._get_channels(service)
            await self.sendupdate._make_send_cache(feeddict, service)
            await self.sendupdate._update_dispatch(feeddict, fp_data, service, channels, True)
            await asyncio.sleep(1)
            _base_log.debug(f"Sending to {len(channels)}")
            for channel in channels.items():
                await self.sendupdate._channel_send_updated_feed(feeddict, channel, service)

    @guild_only()
    @statusdev.command(aliases=["cf"], hidden=True)
    async def checkfeed(self, ctx: commands.Context, link, mode, service):
        if not await self._dev_com(ctx):
            return

        link = FEED_URLS.get(link, link)
        async with self.session.get(link) as response:
            html = await response.text()
        feed = feedparser.parse(html)

        feeddict = helper_process_feed(service, feed)[0]
        await self.sendupdate._make_send_cache(feeddict, service)
        await ctx.send(f"Timestamp: {feeddict.actual_time}")
        await self.sendupdate._channel_send_updated_feed(
            feeddict, (ctx.channel.id, {"mode": mode, "webhook": False}), service
        )

    @statusdev.command(aliases=["cfr"], hidden=True)
    async def checkfeedraw(self, ctx: commands.Context, link: str):
        if not await self._dev_com(ctx):
            return

        async with self.session.get(link) as response:
            html = await response.text()
        feed = feedparser.parse(html)

        feeds = helper_process_feed("zoom", feed)
        links = [feed.link for feed in feeds]

        pages = pagify(str(links))

        await ctx.send_interactive(pages, box_lang="")

    @statusdev.command(aliases=["cfc"], hidden=True)
    async def checkusedfeedcache(self, ctx: commands.Context):
        if not await self._dev_com(ctx):
            return

        raw = box(self.used_feeds_cache, lang="py")
        actual = box(self.used_feeds_cache.get_list(), lang="py")
        await ctx.send(f"**Raw data:**\n{raw}\n**Active:**\n{actual}")

    @statusdev.command(aliases=["cgr"], hidden=True)
    async def checkguildrestrictions(self, ctx: commands.Context):
        if not await self._dev_com(ctx):
            return

        await ctx.send(box(self.service_restrictions_cache.get_guild(ctx.guild.id)))

    @statusdev.command(aliases=["ri"], hidden=True)
    async def resetincidents(self, ctx: commands.Context):
        if not await self._dev_com(ctx):
            return
        await ctx.send("Starting")
        await self._migrate()
        await ctx.send("Done")
