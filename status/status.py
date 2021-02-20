import asyncio
import datetime
import logging
import re
from urllib.error import URLError
import discord
import feedparser
from discord.errors import Forbidden
from discord.ext import tasks
from discord.ext.commands.core import guild_only
from dateutil.parser import parse
from feedparser.util import FeedParserDict
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, pagify, warning
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from redbot.core.utils import deduplicate_iterables
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
}

log = logging.getLogger("red.vexed.status")


class Status(commands.Cog):
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

    @tasks.loop(minutes=3.0)
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
            log.warning("Loop timed out after 2.5 minutes. Some updates were likely skipped.")

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
        async with self.config.etags() as etags:
            for feed in self.used_feeds_cache:
                try:
                    try:
                        response = feedparser.parse(FEED_URLS[feed], etag=etags[feed])
                    except KeyError:
                        response = feedparser.parse(FEED_URLS[feed])
                        etags[feed] = "hello"

                    if response.status == 200:
                        etags[feed] = response.etag
                        feeddict = await self.process_feed(feed, response)
                        if not await self.check_real_update(feed, feeddict):
                            log.debug(f"Ghost status update for {feed} detected, skipping")
                            continue
                        log.debug(f"Feed dict for {feed}: {feeddict}")
                        channels = await self.get_channels(feed)
                        log.debug(f"Sending status update for {feed} to {len(channels)} channels...")
                        for channel in channels:
                            await self.send_updated_feed(feeddict, channel)
                        log.debug("Done")
                    else:
                        log.debug(f"No status update for {feed}")
                except (ConnectionRefusedError, URLError):
                    log.warning(f"Unable to connect to {feed}")
                    continue
                except KeyError:  # a new service has been added
                    etags[feed] = "hello"

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
        print(used_feeds)
        self.used_feeds_cache = used_feeds

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

    async def process_feed(self, service: str, feedparser: FeedParserDict):
        """Process a FeedParserDict into a nicer dict for embeds."""
        return await helper_process_feed(service, feedparser)

    async def get_channels(self, service: str) -> list:
        """Get the channels for a feed. The list is channel IDs from config, they may be invalid."""
        # TODO: make logic more efficient
        feeds = await self.config.all_channels()
        channels = []
        # example server: {'github': [], 'cloudflare': [133251234164375552, 171665724262055936]}
        for feed in feeds.items():
            if service in feed[1]["feeds"].keys():
                channels.append(feed[0])
        return channels

    async def send_updated_feed(self, feeddict: dict, channel: int):
        """Send a feeddict to the specified channel. Currently will only send embed."""
        # TODO: non-embed version
        channel = self.bot.get_channel(channel)
        if await self.bot.embed_requested(channel, None):
            # this will error in dms (or if core code changes), however add command doesn't work in dms so should be not an issue
            try:  # doesn't trigger much, but for some reason can happen
                embed = discord.Embed(
                    title=feeddict["title"],
                    description=feeddict["desc"],
                    timestamp=feeddict["time"],
                    colour=feeddict["colour"],
                )
            except TypeError:
                t = feeddict["time"]
                tt = type(feeddict["time"])
                log.warning(f"Error with timestamp: {t} and {tt}")
                embed = discord.Embed(
                    title=feeddict["title"],
                    description=feeddict["desc"],
                    colour=feeddict["colour"],
                )

            for field in reversed(feeddict["fields"]):
                embed.add_field(name=field["name"], value=field["value"], inline=False)
            try:
                await channel.send(embed=embed)
            except (Forbidden, AttributeError):
                # TODO: maybe remove the feed from config to stop this happening in future?
                log.debug(
                    f"Unable to send status update to channel {channel.id} in guild {channel.guild.id}"
                )

        else:
            regex = r"(?i)\b((?:https?:\/\/|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}\/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
            t = feeddict["title"]
            d = feeddict["desc"]

            msg = ""
            msg += f"**{t}**\n{d}\n\n"

            for i in reversed(feeddict["fields"]):
                n = i["name"]
                v = i["value"]
                msg += f"**{n}**\n{v}\n"

            msg = re.sub(regex, r"<\1>", msg)

            try:
                await channel.send(msg)
            except (Forbidden, AttributeError):
                # TODO: maybe remove the feed from config to stop this happening in future?
                log.debug(
                    f"Unable to send status update to channel {channel.id} in guild {channel.guild.id}"
                )

    async def dev_com(self, ctx):
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
    async def devforcestatus(self, ctx, service):
        """
        THIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.

        It will send the current status of the service to **all

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
        for channel in to_send:
            await self.send_updated_feed(feeddict, channel)

    @guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def statusset(self, ctx):
        """Base command for managing the Status cog."""

    @statusset.command(name="add")
    async def statusset_add(self, ctx, service: str, *channel: discord.TextChannel):
        """
        Start getting status updates for the choses service!

        There is a list of services you can use in the `[p]statusset list` command.

        If you don't specify a specific channel, I will use the current channel.
        """
        channel = channel or ctx.channel
        service = service.lower()

        if service not in FEED_URLS.keys():
            return await ctx.send("That's not a valid service. See `{ctx.clean_prefix}statusset list`.")
        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send(f"I don't have permission to send messages in {channel.mention}.")
        if not channel.permissions_for(ctx.me).embed_links:
            return await ctx.send(
                f"I don't have permission to send embeds in {channel.mention}. "
                "This is called `embed links` in Discord's permission system."
            )
        async with self.config.channel(channel).feeds() as feeds:
            if service in feeds.keys():
                return await ctx.send(
                    f"{channel.mention} already receives {FEED_FRIENDLY_NAMES[service]} status updates!"
                )

            feeds[service] = OLD_DEFAULTS

        if service not in self.used_feeds_cache:
            self.used_feeds_cache.append(service)

        await ctx.send(
            f"Done, {channel.mention} will now receive {FEED_FRIENDLY_NAMES[service]} status updates."
        )

    @statusset.command(name="remove", aliases=["del", "delete"])
    async def statusset_remove(self, ctx, service: str, *channel: discord.TextChannel):
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
    async def statusset_list(self, ctx):
        """List that available services and which ones are being used in this server"""
        unused_feeds = list(FEED_URLS.keys())

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
        await ctx.send(msg)

    # STARTING THE DEV COMMANDS

    @checks.is_owner()
    @commands.command(aliases=["dcf"], hidden=True)
    async def devcheckfeed(self, ctx, link: str):
        if not await self.dev_com(ctx):
            return
        feed = feedparser.parse(link).entries[0]
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
                parseddict["fields"].append(
                    {
                        "name": "Something went wrong with this section",
                        "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                    }
                )
                log.warning(
                    "Something went wrong while parsing the status for GitHub. You can report this to Vexed#3211."
                    f" Timestamp: {datetime.datetime.utcnow()}"
                )

        parseddict.update({"time": parse(feed["published"])})
        parseddict.update({"title": "{} - SERVICE Status Update".format(feed["title"])})
        parseddict.update({"desc": "Incident page: {}".format(feed["link"])})
        parseddict.update({"friendlyname": "SERVICE"})
        parseddict.update({"colour": 2985215})

        # end standard

        await self.send_updated_feed(parseddict, ctx.channel.id)

    @checks.is_owner()
    @commands.command(aliases=["dcfr"])
    async def devcheckfeedraw(self, ctx, link: str):
        feed = feedparser.parse(link).entries[0]

        pages = pagify(str(feed))

        for page in pages:
            await ctx.send(page)


# TODO: preview command
# REMEMBER TIME IS EPOCH IN JSON