# HELLO!
# This file is formatted with black, line length 120
# If you are looking for an event your cog can listen to, take a look here:
# https://vex-cogs.readthedocs.io/en/latest/statusdev.html

import asyncio
import datetime
import logging
from typing import List, Optional

import aiohttp
import discord
import feedparser
from discord.ext import tasks
from discord.ext.commands.core import guild_only
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, pagify, warning
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
from tabulate import tabulate

from .consts import *
from .objects import FeedDict, UsedFeeds
from .rsshelper import process_feed as helper_process_feed
from .sendupdate import SendUpdate

log = logging.getLogger("red.vexed.status")


# cspell:ignore DONT sourcery


class Status(commands.Cog):
    """
    Automatically check for status updates.

    When there is one, it will send the update to all channels that
    have registered to recieve updates from that service.

    If there's a service that you want added, contact Vexed#3211 or
    make an issue on the GitHub repo (or even better a PR!).
    """

    __version__ = "1.3.0"
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
        self.config: Config = Config.get_conf(self, identifier="Vexed-status")
        self.config.register_global(etags=default)
        self.config.register_global(feed_store=default)
        self.config.register_global(latest=default)  # this is unused? i think? remove soonish
        self.config.register_global(migrated=False)
        self.config.register_channel(feeds=default)

        # objects
        self.sendupdate = SendUpdate(config=self.config, bot=self.bot)
        self.session = aiohttp.ClientSession()

        # the loop!
        self._check_for_updates.start()

    def cog_unload(self):
        self._check_for_updates.cancel()
        asyncio.create_task(self.session.close())

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    @tasks.loop(minutes=2.0)
    async def _check_for_updates(self):
        """Loop dealing with automatic updates."""
        if self._check_for_updates.current_loop == 0:
            self.used_feeds_cache = UsedFeeds(await self.config.all_channels())
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
                    log.warning(f"Timeout checking for {service} update")
                    continue
                except Exception as e:
                    log.warning(f"Unable to check for an update for {service}", exc_info=e)
                    continue

            if status == 200:
                await self.sendupdate._maybe_send_update(html, service)
            elif status == 304:  # not modified
                log.debug(f"No new status update for {service}")
            elif status == 429:
                log.warning(
                    f"Unable to get an update for {service}. It looks like we're being rate limited (429). This "
                    "should never happen; therefore this cog does not handle rate limits. Please tell Vexed about "
                    "this and for ways to mitigate this."
                )
            elif str(status)[0] == "5":  # 500 status code
                log.info(f"Unable to get an update for {service} - internal server error (HTTP Error {status})")
            else:
                log.info(f"Abnormal status code received from {service}: {status}\nPlease report this to Vexed.")

    async def _migrate(self):
        """Migrate config format"""
        # why didn't i start with using a good config layout...
        # oh, i know why: i'd never used config before!
        # note to self - this was implemented on 20 feb only 3 days after release
        # -> remove around 20 may

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
                        await self.config.channel_from_id(channels).feeds.set_raw(feed_name, value=OLD_DEFAULTS)
            except KeyError:
                continue
        await self.config.migrated.set(True)

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

        await ctx.send(f"Removed {FEED_FRIENDLY_NAMES[service]} status updates from {channel.mention}")

    @statusset.command(name="list", aliases=["show", "settings"])
    async def statusset_list(self, ctx: commands.Context, service: Optional[str]):
        # sourcery no-metrics
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
                for name, settings in feeds.items():
                    if name != service:
                        continue
                    mode = settings["mode"]
                    webhook = settings["webhook"]
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

        await self.sendupdate._make_send_cache(feeddict, service)

        channel = (ctx.channel.id, {"mode": mode, "webhook": webhook})
        try:
            await self.sendupdate._channel_send_updated_feed(feeddict, channel, service, False)
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
        """Change what mode to use for updates

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
            log.debug(f"Sending to {len(channels)}")
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

        # feed = helper_process_feed("twitter", feed)
        # feed = feed.to_dict()

        pages = pagify(str(feed.entries[0]))

        await ctx.send_interactive(pages, box_lang="")

    @statusdev.command(aliases=["cfc"], hidden=True)
    async def checkusedfeedcache(self, ctx: commands.Context):
        if not await self._dev_com(ctx):
            return

        raw = box(self.used_feeds_cache.__data, lang="py")
        actual = box(self.used_feeds_cache.get_list(), lang="py")
        await ctx.send(f"**Raw data:**\n{raw}\n**Active:**\n{actual}")
