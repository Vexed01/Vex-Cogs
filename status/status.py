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
from redbot.core.utils import deduplicate_iterables
from redbot.core.utils.chat_formatting import box, humanize_list, pagify, warning
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
from tabulate import tabulate

from .rsshelper import _strip_html
from .rsshelper import process_feed as _helper_process_feed

ALL = "all"
LATEST = "latest"
EDIT = "edit"

OLD_DEFAULTS = {"mode": ALL, "webhook": False}


FEED_URLS = {
    "discord": "https://discordstatus.com/history.atom",
    "github": "https://www.githubstatus.com/history.atom",
    "cloudflare": "https://www.cloudflarestatus.com/history.atom",
    "python": "https://status.python.org/history.atom",
    "twitter_api": "https://api.twitterstat.us/history.atom",
    "statuspage": "https://metastatuspage.com/history.atom",
    "zoom": "https://status.zoom.us/history.atom",
    "oracle_cloud": "https://ocistatus.oraclecloud.com/history.atom",
    "twitter": "https://status.twitterstat.us/pages/564314ae3309c22c3b0002fa/rss",
    "epic_games": "https://status.epicgames.com/history.atom",
    "digitalocean": "https://status.digitalocean.com/history.atom",
    "reddit": "https://www.redditstatus.com/history.atom",
    "aws": "https://status.aws.amazon.com/rss/all.rss",
    "gcp": "https://status.cloud.google.com/feed.atom",
    "smartthings": "https://status.smartthings.com/history.atom",
}

FEED_FRIENDLY_NAMES = {
    "discord": "Discord",
    "github": "GitHub",
    "cloudflare": "Cloudflare",
    "python": "Python",
    "twitter_api": "Twitter API",
    "statuspage": "Statuspage",
    "zoom": "Zoom",
    "oracle_cloud": "Oracle Cloud",
    "twitter": "Twitter",
    "epic_games": "Epic Games",
    "digitalocean": "DigitalOcean",
    "reddit": "Reddit",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "smartthings": "SmartThings",
}

AVALIBLE_MODES = {  # not rly needed atm but will be later with feeds such as aws, google
    "discord": [ALL, LATEST],
    "github": [ALL, LATEST],
    "cloudflare": [ALL, LATEST],
    "python": [ALL, LATEST],
    "twitter_api": [ALL, LATEST],
    "statuspage": [ALL, LATEST],
    "zoom": [ALL, LATEST],
    "oracle_cloud": [ALL, LATEST],
    "twitter": [ALL, LATEST],
    "epic_games": [ALL, LATEST],
    "digitalocean": [ALL, LATEST],
    "reddit": [ALL, LATEST],
    "aws": [LATEST],
    "gcp": [LATEST],
    "smartthings": [ALL, LATEST],
}

AVATAR_URLS = {  # TODO: unify these
    "discord": "https://cdn.discordapp.com/attachments/813140082989989918/813140277367144458/discord.png",
    "github": "https://cdn.discordapp.com/attachments/813140082989989918/813140279120232488/github.png",
    "cloudflare": "https://cdn.discordapp.com/attachments/813140082989989918/813140275714195516/cloudflare.png",
    "python": "https://cdn.discordapp.com/attachments/813140082989989918/814490148917608458/unknown.png",
    "twitter_api": "https://cdn.discordapp.com/attachments/813140082989989918/814863181033898084/aaaaaaaaaaaaaa.png",
    "statuspage": "https://cdn.discordapp.com/attachments/813140082989989918/813140261987024976/statuspage.png",
    "zoom": "https://cdn.discordapp.com/attachments/813140082989989918/813140273751523359/zoom.png",
    "oracle_cloud": "https://media.discordapp.net/attachments/813140082989989918/813140282538721310/oracle_cloud.png",
    "twitter": "https://cdn.discordapp.com/attachments/813140082989989918/814863181033898084/aaaaaaaaaaaaaa.png",
    "epic_games": "https://cdn.discordapp.com/attachments/813140082989989918/813454141514317854/unknown.png",
    "digitalocean": "https://cdn.discordapp.com/attachments/813140082989989918/813454051613999124/gnlwek2zwhq369yryrzv.png",
    "reddit": "https://cdn.discordapp.com/attachments/813140082989989918/813466098040176690/reddit-logo-16.png",
    "aws": "https://cdn.discordapp.com/attachments/813140082989989918/813730858951245854/aws.png",
    "gcp": "https://cdn.discordapp.com/attachments/813140082989989918/814488794585235517/unknown.png",
    "smartthings": "https://cdn.discordapp.com/attachments/813140082989989918/814600450832859193/zbO2ggF6K2YVII3qOfr0Knj3P0H7OdtTjZAcGBo3kK0vJppGoYsG4TMZINqyPlLa9vI.png",
}

SPECIAL_INFO = {
    "aws": "AWS frequently posts status updates in both English and the language local to where the incident affects.",
    "oracle_cloud": (
        "Oracle is frequently very slow to update their status page. Sometimes, they also only update itwhen the "
        "incident is resolved."
    ),
}

DONT_REVERSE = ["twitter"]

log = logging.getLogger("red.vexed.status")


class Status(commands.Cog):
    """
    Automatically check for status updates.

    When there is one, it will send the update to all channels that
    have registered to revieve updates from that service.

    If there's a service that you want added, contact Vexed#3211 or
    make an issue on the GitHub repo (or even better a PR!).
    """

    __version__ = "1.1.5"
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

        self.config = Config.get_conf(self, identifier="Vexed-status")
        default = {}
        self.config.register_global(etags=default)
        self.config.register_global(feed_store=default)
        self.config.register_global(latest=default)
        self.config.register_global(migrated=False)
        self.config.register_channel(feeds=default)

        self.used_feeds_cache = []
        self.send_cache = {}

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

        if not self.used_feeds_cache:
            log.debug("No channels have registered a feed!")
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
        For more information on this event, take a look at the docs:
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

    async def _channel_send_dispatch(self, feed, service, channel, webhook, embed):
        """
        For more information on this event, take a look at the docs:
        https://vex-cogs.readthedocs.io/en/latest/statusdev.html
        """
        self.bot.dispatch(
            "vexed_status_channel_send",
            feed=feed,
            service=service,
            channel=channel,
            webhook=webhook,
            embed=embed,
        )

    async def _make_used_feeds(self):
        feeds = await self.config.all_channels()
        used_feeds = []
        for channel in feeds.items():
            used_feeds.extend(channel[1]["feeds"].keys())

            used_feeds = deduplicate_iterables(used_feeds)
            if len(used_feeds) == len(FEED_URLS):  # no point checking more channels now
                break
        self.used_feeds_cache = used_feeds

    async def _migrate(self):
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
        async with aiohttp.ClientSession() as session:
            for service in self.used_feeds_cache:
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
                    log.debug(f"Sending status update for {service} to {len(channels)} channels...")
                    for channel in channels.items():
                        await self._send_updated_feed(feeddict, channel, service)
                    self.send_cache = None
                    log.debug("Done")
                else:
                    log.debug(f"No status update for {service}")
        await session.close()

    async def _process_feed(self, service: str, feedparser: FeedParserDict) -> dict:
        """Process a FeedParserDict into a nicer dict for embeds."""
        return await _helper_process_feed(service, feedparser)

    async def _check_real_update(self, service: str, feeddict: dict) -> bool:
        """
        Check that there has been an actual update to the status against last known.
        If so, will update the feed store.
        """
        async with self.config.feed_store() as feed_store:
            old_fields = feed_store["discord"].get("fields")
            prev_titles = []
            for title in old_fields:
                prev_titles.append(title.get("name"))
            new_fields = feeddict["fields"]
            if service in DONT_REVERSE and old_fields[-1]["name"] in prev_titles:
                return False
            elif service not in DONT_REVERSE and old_fields[0]["name"] in prev_titles:
                return False
            else:
                to_store = feeddict.copy()
                to_store["time"] = to_store["time"].timestamp()
                feed_store[service] = to_store
                return True

    async def _get_channels(self, service: str) -> dict:
        """Get the channels for a feed. The list is channel IDs from config, they may be invalid."""
        feeds = await self.config.all_channels()
        channels = {}
        for feed in feeds.items():
            if service in feed[1]["feeds"].keys():
                channels[feed[0]] = feed[1]["feeds"][service]
        return channels

    async def _make_send_cache(self, feeddict, service: str):
        """Make the cache used in send_updated_feed"""
        try:
            base = discord.Embed(
                title=feeddict["title"],
                timestamp=feeddict["time"],
                colour=feeddict["colour"],
                url=feeddict["link"],
            )
        except TypeError:  # can happen with timestamps, should be fixed
            log.error(
                "Failed with timestamp {} on {}. Updates were still sent. Please report this to Vexed.".format(
                    feeddict["time"], service
                )
            )
            base = discord.Embed(
                title=feeddict["title"],
                colour=feeddict["colour"],
                url=feeddict["link"],
            )

        embed_latest = base.copy()
        embed_all = base.copy()
        webhook_latest = base.copy()
        webhook_all = base.copy()

        # ALL
        if service in DONT_REVERSE:
            for field in feeddict["fields"]:
                embed_all.add_field(name=field["name"], value=field["value"], inline=False)
                webhook_all.add_field(name=field["name"], value=field["value"], inline=False)
        else:
            for field in reversed(feeddict["fields"]):
                embed_all.add_field(name=field["name"], value=field["value"], inline=False)
                webhook_all.add_field(name=field["name"], value=field["value"], inline=False)

        # LATEST
        if service in DONT_REVERSE:
            embed_latest.add_field(  # TODO: if two are published in quick succession could miss one
                name=feeddict["fields"][-1]["name"],
                value=feeddict["fields"][-1]["value"],
                inline=False,
            )
            webhook_latest.add_field(  # TODO: if two are published in)
                name=feeddict["fields"][-1]["name"],
                value=feeddict["fields"][-1]["value"],
                inline=False,
            )
        else:
            embed_latest.add_field(  # TODO: if two are published in quick succession could miss one
                name=feeddict["fields"][0]["name"],
                value=feeddict["fields"][0]["value"],
                inline=False,
            )
            webhook_latest.add_field(  # TODO: if two are published in)
                name=feeddict["fields"][0]["name"],
                value=feeddict["fields"][0]["value"],
                inline=False,
            )

        t = feeddict["title"]
        l = feeddict["link"]
        n = FEED_FRIENDLY_NAMES[service]
        plain_latest = f"**{n} Status Update\n{t}**\nIncident link: {l}\n\n"
        plain_all = f"**{n} Status Update\n{t}**\nIncident link: {l}\n\n"

        if service in DONT_REVERSE:
            for i in feeddict["fields"]:
                n = i["name"]
                v = i["value"]
                plain_all += f"**{n}**\n{v}\n"
        else:
            for i in reversed(feeddict["fields"]):
                n = i["name"]
                v = i["value"]
                plain_all += f"**{n}**\n{v}\n"

        if service in DONT_REVERSE:
            n = feeddict["fields"][-1]["name"]
            v = feeddict["fields"][-1]["value"]
            plain_latest += f"**{n}**\n{v}\n"

        else:
            n = feeddict["fields"][0]["name"]
            v = feeddict["fields"][0]["value"]
            plain_latest += f"**{n}**\n{v}\n"

        regex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
        # regex from https://stackoverflow.com/a/28187496
        plain_all = re.sub(regex, r"<\1>", plain_all)  # wrap links in <> for no previews
        plain_latest = re.sub(regex, r"<\1>", plain_latest)

        self.send_cache = {
            "plain_latest": plain_latest,
            "plain_all": plain_all,
            "embed_latest": embed_latest,
            "embed_all": embed_all,
            "webhook_latest": webhook_latest,
            "webhook_all": webhook_all,
        }

    async def _send_updated_feed(self, feeddict: dict, channel: tuple, service: str):
        """Send a feeddict to the specified channel."""
        mode = channel[1]["mode"]
        use_webhook = channel[1]["webhook"]
        c_id = channel[0]
        channel = self.bot.get_channel(c_id)
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
            if mode == "all" and use_webhook == False:
                embed = self.send_cache.get("embed_all")
            elif mode == "latest" and use_webhook == False:
                embed = self.send_cache.get("embed_latest")
            elif mode == "all" and use_webhook == True:
                embed = self.send_cache.get("webhook_all")
            elif mode == "latest" and use_webhook == True:
                embed = self.send_cache.get("webhook_latest")

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
                        webhook = await channel.create_webhook(name=channel.guild.me.name)
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
                    await channel.send(embed=embed)
            except Exception as e:
                log.info(  # TODO: remove from config
                    f"Somehting went wrong with {c_id} in guild {channel.guild.id} - skipping", exc_info=e
                )
                return

        else:
            if mode == "all":
                msg = self.send_cache.get("plain_all")
            elif mode == "latest":
                msg = self.send_cache.get("plain_latest")

            try:
                await channel.send(msg)
            except Exception as e:
                log.info(  # TODO: remove from config
                    f"Something went wrong with {c_id} in guild {channel.guild.id} - skipping", exc_info=e
                )

        await self._channel_send_dispatch(feeddict, service, channel, use_webhook, use_embed)

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
        )
        if ALL not in AVALIBLE_MODES[service]:
            unsupported.append(ALL)
        if LATEST not in AVALIBLE_MODES[service]:
            unsupported.append(LATEST)

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
            else:
                webhook = False
        else:
            await ctx.send(
                "I would ask about whether you want me to send updates as a webhook (so they match the "
                "service), however I don't have the `manage webhooks` permission."
            )
            webhook = False

        settings = {"mode": mode, "webhook": webhook}
        await self.config.channel(channel).feeds.set_raw(service, value=settings)

        if service not in self.used_feeds_cache:
            self.used_feeds_cache.append(service)

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

        If you don't specify a channel, I will use the current channel
        """
        channel = channel or ctx.channel

        # TODO: multiple services in one command
        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")

        channel_conf = self.config.channel(channel)
        async with channel_conf.feeds() as feeds:
            if service not in feeds.keys():
                return await ctx.send(
                    f"It looks like I don't send {FEED_FRIENDLY_NAMES[service]} status updates to {channel.mention}"
                )
            feeds.pop(service)
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
                for feed in feeds.items():
                    if feed[0] != service:
                        continue
                    mode = feed[1]["mode"]
                    webhook = feed[1]["webhook"]
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
                for feed in guild_feeds.items():
                    if not feed[1]:
                        continue
                    data.append([feed[0], humanize_list(feed[1])])
                    try:
                        unused_feeds.remove(feed[0])
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

        **`<webhook>`**
            Using a webhook means that the status updates will be sent with the avatar
            as the service's logo and the name will be `[service] Status Update`, instead
            of my avatar and name.
        """
        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")
        mode = mode.lower()
        if mode not in [ALL, LATEST, EDIT]:
            return await ctx.send("That's not a valid mode. Valid ones are `all` and `latest`")
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
            await self._check_real_update(service, feeddict)  # this will add it to the feed_store
        else:
            feeddict["time"] = datetime.datetime.fromtimestamp(feeddict["time"])

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
            f"{FEED_FRIENDLY_NAMES[service]} status upadtes in {channel.mention} will now use the {mode} mode."
        )

    @statusset_edit.command(name="webhook")
    async def statusset_edit_webhook(
        self, ctx: commands.Context, service: str, channel: Optional[discord.TextChannel], webhook: bool
    ):
        """Set whether or not to use webhooks to send the status update

        Using a webhook means that the status updates will be sent with the avatar as the service's
        logo and the name will be `[service] Status Update`, instead of my avatar and name.
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

        old_conf[service]["webhook"] = webhook
        await self.config.channel(channel).feeds.set_raw(service, value=old_conf[service])

        if webhook:
            word = "not use"
        else:
            word = "use"
        await ctx.send(
            f"{FEED_FRIENDLY_NAMES[service]} status updates in {channel.mention} will now {word} webhooks."
        )

    # STARTING THE DEV COMMANDS

    async def dev_com(self, ctx: commands.Context):
        """Returns whether to continue or not"""
        if ctx.author.id != 418078199982063626:  # vexed (my) id
            msg = await ctx.send(
                warning(
                    "\nTHIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.\n\nUnintended things are likely to"
                    "happen.\n\nRepeat: THIS COMMAND IS NOT SUPPORTED.\nAre you sure you want to continue?"
                )
            )
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            await ctx.bot.wait_for("reaction_add", check=pred)
            if pred.result is not True:
                await ctx.send("Aborting.")
                return False
        return True

    @checks.is_owner()
    @commands.command(hidden=True, aliases=["dfs"])
    async def devforcestatus(self, ctx: commands.Context, service):
        if not await self.dev_com(ctx):
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
        await self._update_dispatch(feeddict, fp_data, service, channels, True)
        await self._make_send_cache(feeddict, service)
        for channel in channels.items():
            await self._send_updated_feed(feeddict, channel, service)

    @checks.is_owner()
    @commands.command(aliases=["dcf"], hidden=True)
    async def devcheckfeed(self, ctx: commands.Context, link: str, mode):
        if not await self.dev_com(ctx):
            return
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                html = await response.text()
            await session.close()
        feed = feedparser.parse(html)
        feed = feed["entries"][0]
        # standard below:

        strippedcontent = await _strip_html(feed["content"][0]["value"])
        sections = strippedcontent.split("=-=SPLIT=-=")
        parseddict = {"fields": []}

        for data in sections:
            try:
                if data != "":
                    current = data.split(" - ", 1)
                    content = current[1]
                    tt = current[0].split("\n")
                    time = tt[0]
                    title = tt[1]
                    parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
            except IndexError:  # this would be a likely error if something didn't format as expected
                try:
                    if data.startswith("THIS IS A SCHEDULED EVENT"):
                        split = data.split("EVENT", 1)
                        value = split[1]
                        parseddict["fields"].append(
                            {"name": "THIS IS A SCHEDULED EVENT", "value": f"It is scheduled for {value}"}
                        )
                        continue
                except IndexError:
                    pass
                parseddict["fields"].append(
                    {
                        "name": "Something went wrong with this section",
                        "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                    }
                )
                log.warning(
                    "Something went wrong while parsing a status feed. You can report this to Vexed#3211."
                    f" Timestamp: {datetime.datetime.utcnow()}"
                )

        parseddict.update({"time": datetime.datetime.strptime(feed["published"], "%Y-%m-%dT%H:%M:%S%z")})
        parseddict.update({"title": feed["title"]})
        parseddict.update({"link": feed["link"]})
        parseddict.update({"colour": 7308754})

        # end standard

        # return await ctx.send("done")

        await self._make_send_cache(parseddict, "discord")

        await self._send_updated_feed(
            parseddict, (ctx.channel.id, {"mode": mode, "webhook": False}), "oracle_cloud"
        )  # discord is just a place holder

    @checks.is_owner()
    @commands.command(aliases=["dcfr"], hidden=True)
    async def devcheckfeedraw(self, ctx: commands.Context, link: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(link) as response:
                html = await response.text()
            await session.close()
        feed = feedparser.parse(html)

        pages = pagify(str(feed))

        await ctx.send_interactive(pages, box_lang="")
