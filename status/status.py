import asyncio
import datetime
import logging
import re
from typing import Optional
from urllib.error import URLError

import discord
import feedparser
from dateutil.parser import parse
from discord.errors import Forbidden
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
from .rsshelper import process_feed as helper_process_feed

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
}

AVATAR_URLS = {
    "discord": "https://cdn.discordapp.com/attachments/813140082989989918/813140277367144458/discord.png",
    "github": "https://cdn.discordapp.com/attachments/813140082989989918/813140279120232488/github.png",
    "cloudflare": "https://cdn.discordapp.com/attachments/813140082989989918/813140275714195516/cloudflare.png",
    "python": "https://cdn.discordapp.com/attachments/813140082989989918/813140283767783424/python.png",
    "twitter_api": "https://cdn.discordapp.com/attachments/813140082989989918/813140272027926528/twitter_api.jpg",
    "statuspage": "https://cdn.discordapp.com/attachments/813140082989989918/813140261987024976/statuspage.png",
    "zoom": "https://cdn.discordapp.com/attachments/813140082989989918/813140273751523359/zoom.png",
    "oracle_cloud": "https://cdn.discordapp.com/attachments/813140082989989918/813140282538721310/oracle_cloud.png",
    "twitter": "https://cdn.discordapp.com/attachments/813140082989989918/813140272027926528/twitter_api.jpg",
    "epic_games": "https://cdn.discordapp.com/attachments/813140082989989918/813454141514317854/unknown.png",
    "digitalocean": "https://cdn.discordapp.com/attachments/813140082989989918/813454051613999124/gnlwek2zwhq369yryrzv.png",
    "reddit": "https://cdn.discordapp.com/attachments/813140082989989918/813466098040176690/reddit-logo-16.png",
}

DONT_REVERSE = ["twitter"]

log = logging.getLogger("red.vexed.status")


class Status(commands.Cog):
    """Automatically check for status updates"""

    __version__ = "0.2.3"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**"

    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, identifier="Vexed-status")
        default = {}
        self.config.register_global(etags=default)
        self.config.register_global(feed_store=default)
        self.config.register_global(migrated=False)
        self.config.register_channel(feeds=default)

        self.used_feeds_cache = []

        self.check_for_updates.start()

    def cog_unload(self):
        self.check_for_updates.cancel()

    @tasks.loop(minutes=2.5)
    async def check_for_updates(self):
        """Loop that checks for updates and if needed triggers other functions to send them."""
        await asyncio.sleep(0.1)  # this stops some weird behaviur on loading the cog

        if self.check_for_updates.current_loop == 0:
            await self.make_used_feeds()
            if await self.config.migrated() is False:
                log.info("Migrating to new config format...")
                await self.migrate()
                await self.config.clear_all_guilds()
                log.info("Done!")

        if not self.used_feeds_cache:
            log.debug("No channels have registered a feed!")
            return

        try:
            await asyncio.wait_for(self.actually_check_updates(), timeout=150.0)  # 2.5 mins
        except TimeoutError:
            log.warning("Loop timed out after 2.5 minutes. Multiple updates were likely disrupted.")

    @check_for_updates.before_loop
    async def before_start(self):
        await self.bot.wait_until_red_ready()

    async def make_used_feeds(self):
        feeds = await self.config.all_channels()
        used_feeds = []
        for channel in feeds.items():
            used_feeds.extend(channel[1]["feeds"].keys())

            used_feeds = deduplicate_iterables(used_feeds)
            if len(used_feeds) == len(FEED_URLS):  # no point checking more channels now
                break
        self.used_feeds_cache = used_feeds

    async def migrate(self):
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

    async def actually_check_updates(self):
        for feed in self.used_feeds_cache:
            async with self.config.etags() as etags:
                try:
                    response = feedparser.parse(FEED_URLS[feed], etag=etags[feed])
                    if response.status == 200:
                        etags[feed] = response.etag
                except KeyError:
                    response = feedparser.parse(FEED_URLS[feed])
                    etags[feed] = response.etag
                except (ConnectionRefusedError, URLError):
                    log.warning(f"Unable to connect to {feed}. Will try again at next check.")

            if response.status == 200:
                feeddict = await self.process_feed(feed, response)
                if not await self.check_real_update(feed, feeddict):
                    log.debug(f"Ghost status update for {feed} detected, skipping")
                    continue
                log.debug(f"Feed dict for {feed}: {feeddict}")
                channels = await self.get_channels(feed)
                log.debug(f"Sending status update for {feed} to {len(channels)} channels...")
                for channel in channels.items():
                    await self.send_updated_feed(feeddict, channel, feed)
                log.debug("Done")
            else:
                log.debug(f"No status update for {feed}")

    async def process_feed(self, service: str, feedparser: FeedParserDict):
        """Process a FeedParserDict into a nicer dict for embeds."""
        return await helper_process_feed(service, feedparser)

    async def check_real_update(self, service: str, feeddict: dict) -> bool:
        """
        Check that there has been an actual update to the status against last known.
        If so, will update the feed store.
        """
        async with self.config.feed_store() as feed_store:
            try:
                old_fields = feed_store[service][
                    "fields"
                ]  # not comparing whole feed as time is in feeddict and that could ghost update
            except KeyError:
                old_fields = "hello"
            new_fields = feeddict["fields"]
            log.debug(f"Old fields: {old_fields}")
            log.debug(f"New fields: {new_fields}")
            if old_fields == new_fields:
                return False
            else:
                feeddict["time"] = feeddict["time"].timestamp()
                feed_store[service] = feeddict
                return True

    async def get_channels(self, service: str) -> dict:
        """Get the channels for a feed. The list is channel IDs from config, they may be invalid."""
        # TODO: maybe logic more efficient
        feeds = await self.config.all_channels()
        channels = {}
        for feed in feeds.items():
            if service in feed[1]["feeds"].keys():
                channels[feed[0]] = feed[1]["feeds"][service]
        return channels

    async def send_updated_feed(self, feeddict: dict, channel: tuple, service: str):
        """Send a feeddict to the specified channel."""
        # TODO: cache the embed/message
        mode = channel[1]["mode"]
        use_webhook = channel[1]["webhook"]
        channel = self.bot.get_channel(channel[0])
        if channel is None:  # guilds can creep in here, blame core for giving guilds from all_channels() /s
            return
        if not use_webhook:
            embed = await self.bot.embed_requested(channel, None)
        if use_webhook:
            embed = True
        if mode == "all" or mode == "latest":
            if embed:
                try:
                    embed = discord.Embed(
                        title=feeddict["title"],
                        timestamp=feeddict["time"],
                        colour=feeddict["colour"],
                        url=feeddict["link"],
                    )
                except TypeError:  # can happen with timezone
                    t = feeddict["time"]
                    tt = type(feeddict["time"])
                    log.debug(f"Error with timestamp: {t} and {tt}")
                    embed = discord.Embed(
                        title=feeddict["title"],
                        colour=feeddict["colour"],
                        url=feeddict["link"],
                    )
                if mode == "all":
                    if service in DONT_REVERSE:
                        for field in feeddict["fields"]:
                            embed.add_field(name=field["name"], value=field["value"], inline=False)
                    else:
                        for field in reversed(feeddict["fields"]):
                            embed.add_field(name=field["name"], value=field["value"], inline=False)
                elif mode == "latest":
                    if service in DONT_REVERSE:
                        embed.add_field(  # TODO: if two are published in quick succession could miss one
                            name=feeddict["fields"][-1]["name"],
                            value=feeddict["fields"][-1]["value"],
                            inline=False,
                        )
                    else:
                        embed.add_field(  # TODO: if two are published in quick succession could miss one
                            name=feeddict["fields"][0]["name"],
                            value=feeddict["fields"][0]["value"],
                            inline=False,
                        )
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
                    # TODO: maybe remove the feed from config to stop this happening in future?
                    log.warning(
                        f"Unable to send status update to channel {channel.id} in guild {channel.guild.id}. All other updates WILL be sent.",
                        exc_info=e,
                    )

            else:
                msg = self
                t = feeddict["title"]
                d = feeddict["desc"]

                msg = ""
                msg += f"**{t}**\n{d}\n\n"

                if mode == "all":
                    for i in reversed(feeddict["fields"]):
                        n = i["name"]
                        v = i["value"]
                        msg += f"**{n}**\n{v}\n"

                    regex = r"(?i)\b((?:https?:\/\/|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
                    msg = re.sub(regex, r"<\1>", msg)  # wrap links in <> for no previews

                elif mode == "latest":
                    n = feeddict["fields"][0]["name"]
                    v = feeddict["fields"][0]["value"]
                    msg += f"**{n}**\n{v}\n"

                    regex = r"(?i)\b((?:https?:\/\/|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
                    msg = re.sub(regex, r"<\1>", msg)  # wrap links in <> for no previews

                try:
                    await channel.send(msg)
                except (Forbidden, AttributeError):
                    # TODO: maybe remove the feed from config to stop this happening in future?
                    log.debug(
                        f"Unable to send status update to channel {channel.id} in guild {channel.guild.id}"
                    )
        elif mode == "edit":
            pass  # TODO: this

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
        if ALL in AVALIBLE_MODES[service]:
            modes += (
                "**All**: Every time the service posts an update on an incident, I will send a new message "
                "contaning the previus updates as well as the new update. Best used in a fast-moving "
                "channel with other users.\n\n"
            )
        else:
            unsupported.append(ALL)
        if LATEST in AVALIBLE_MODES[service]:
            modes += (
                "**Latest**: Every time the service posts an update on an incident, I will send a new message "
                "contanint only the latest update. Best used in a dedicated status channel.\n\n"
            )
        else:
            unsupported.append(LATEST)
        if unsupported:
            unsupported = humanize_list(unsupported)
            if len(unsupported) > 1:
                extra = "s"
            modes += f"Due to {friendly} limitations, I can't support the {unsupported} mode{extra}\n\n"

        await ctx.send(
            "This is an interactive configuration. You have 2 minutes to answer each question.\n"
            f"**What mode do you want to use?**\n\n{modes}"
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
                "Status Update`, instead of my avatar and name."
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

    @statusset.command(name="list", aliases=["show"])
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

    # TODO: preview command

    # STARTING THE DEV COMMANDS

    async def dev_com(self, ctx: commands.Context):
        """Returns whether to continue or not"""
        if ctx.author.id != 418078199982063626:  # my id
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
        """
        THIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.

        It will send the current status of the service to **all channels in all servers**
        that haver registered for alerts.

        Repeat: THIS COMMAND IS NOT SUPPORTED.
        """
        if not await self.dev_com(ctx):
            return

        if service not in FEED_URLS.keys():
            return await ctx.send("Hmm, that doesn't look like a valid service.")

        feed = feedparser.parse(FEED_URLS[service])
        feeddict = await self.process_feed(service, feed)

        real = await self.check_real_update(service, feeddict)
        await ctx.send(f"Real update: {real}")
        to_send = await self.get_channels(service)
        for channel in to_send.items():
            await self.send_updated_feed(feeddict, channel, service)

    @checks.is_owner()
    @commands.command(aliases=["dcf"], hidden=True)
    async def devcheckfeed(self, ctx: commands.Context, link: str, mode):
        if not await self.dev_com(ctx):
            return
        feed = feedparser.parse(link).entries[0]
        # standard below:

        strippedcontent = await _strip_html(feed["description"])

        sections = strippedcontent.split("=-=SPLIT=-=")
        parseddict = {"fields": []}

        parseddict.update({"time": parse(feed["published"])})
        parseddict.update({"title": "{} - SERVICE Status Update".format(feed["title"])})
        parseddict.update({"desc": "Incident page: {}".format(feed["link"])})
        parseddict.update({"rtitle": feed["title"]})
        parseddict.update({"colour": 27134})

        # end standard

        self.feed_embed_cache = {"base": None, "latest": None, "all": None}
        self.feed_plain_cache = {"latest": None, "all": None}

        # return await ctx.send("done")

        await self.send_updated_feed(
            parseddict, (ctx.channel.id, {"mode": mode, "webhook": False}), "oracle_cloud"
        )  # discord is just a place holder

    @checks.is_owner()
    @commands.command(aliases=["dcfr"])
    async def devcheckfeedraw(self, ctx: commands.Context, link: str):
        feed = feedparser.parse(link).entries[0]

        pages = pagify(str(feed))

        for page in pages:
            await ctx.send(page)
