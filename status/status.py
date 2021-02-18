import asyncio
import logging
from urllib.error import URLError

import discord
import feedparser
from discord.errors import Forbidden
from discord.ext import tasks
from discord.ext.commands.core import guild_only
from feedparser.exceptions import ThingsNobodyCaresAboutButMe
from feedparser.util import FeedParserDict
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, warning
import datetime
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from tabulate import tabulate

from .rsshelper import parse_cloudflare, parse_discord, parse_github

FEED_URLS = {
    "discord": "https://discordstatus.com/history.atom",
    "github": "https://www.githubstatus.com/history.atom",
    "cloudflare": "https://www.cloudflarestatus.com/history.atom",
}

FEED_FRIENDLY_NAMES = {
    "discord": "Discord",
    "github": "GitHub",
    "cloudflare": "Cloudflare",
}


log = logging.getLogger("red.vexed.status")


class Status(commands.Cog):
    def __init__(self, bot: Red):
        self.config = Config.get_conf(self, identifier="Vexed-status", force_registration=True)
        default_global = {
            "discord": "hello",
            "github": "hello",
            "cloudflare": "hello",
        }
        feed_store = {
            "discord": {"fields": "hello"},
            "github": {"fields": "hello"},
            "cloudflare": {"fields": "hello"},
        }

        default_guild = {}
        self.config.register_global(etags=default_global)
        self.config.register_global(feed_store=feed_store)
        self.config.register_guild(feeds=default_guild)

        self.check_for_updates.start()

        self.bot = bot

    def cog_unload(self):
        self.check_for_updates.cancel()

    @tasks.loop(minutes=3.0)
    async def check_for_updates(self):
        """Loop that checks for updates and if needed triggers other functions to send them."""
        # TODO: as more services get added, start only checking ones that have registered servers
        await asyncio.sleep(0.1)  # this stops some weird behaviour on loading the cog
        try:
            await asyncio.wait_for(self.actually_check_updates(), timeout=150.0)  # 2.5 mins
        except TimeoutError:
            log.warning("Loop timed out after 2.5 minutes. Some updates were likely skiped.")

    async def actually_check_updates(self):
        async with self.config.etags() as etags:
            for feed in FEED_URLS.items():  # change to await self.config.to_check()
                try:
                    response = feedparser.parse(feed[1], etag=etags[feed[0]])
                    if response.status == 200:
                        etags[feed[0]] = response.etag
                        feeddict = await self.process_feed(feed[0], response)
                        if not await self.check_real_update(feed[0], feeddict):
                            log.debug(f"Ghost status update for {feed[0]} detected, skipping")
                            continue
                        log.debug(f"Feed dict for {feed[0]}: {feeddict}")
                        channels = await self.get_channels(feed[0])
                        log.debug(f"Sending status update for {feed[0]} to {len(channels)} channels...")
                        for channel in channels:
                            await self.send_updated_feed(feeddict, channel)
                        log.debug("Done")
                    else:
                        log.debug(f"No status update for {feed[0]}")
                except (ConnectionRefusedError, URLError):
                    log.warning(f"Unable to connect to {feed[0]}")
                    continue
                except KeyError:  # a new service has been added
                    etags[feed[0]] = "hello"

    @check_for_updates.before_loop
    async def before_start(self):
        await self.bot.wait_until_red_ready()

    async def check_real_update(self, service: str, feeddict: dict) -> bool:
        """
        Check that there has been an actual update to the status against last known.
        If so, will update the feed store.
        """
        async with self.config.feed_store() as feed_store:
            old_fields = feed_store[service][
                "fields"
            ]  # not comparing whole feed as time is in feeddict and that could ghost update
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
        # TODO: maybe improve this bit somehow?
        if service == "discord":
            feeddict = await parse_discord(feedparser.entries[0])
        elif service == "github":
            feeddict = await parse_github(feedparser.entries[0])
        elif service == "cloudflare":
            feeddict = await parse_cloudflare(feedparser.entries[0])
        else:
            feeddict = None
        return feeddict

    async def get_channels(self, service: str) -> list:
        """Get the channels for a feed. The list is channel IDs from config, they may be invalid."""
        # TODO: make logic more efficient
        feeds = await self.config.all_guilds()
        target_service = service
        channels = []
        # example server: {'github': [], 'cloudflare': [133251234164375552, 171665724262055936]}
        for server in feeds.items():
            try:
                to_append = server[1]["feeds"][target_service]
            except KeyError:
                continue
            try:
                channels.extend(to_append)
            except TypeError:
                channels.append(to_append)
        return channels

    async def send_updated_feed(self, feeddict: dict, channel: int):
        """Send a feeddict to the specified channel. Currently will only send embed."""
        # TODO: non-embed version
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

        channel = self.bot.get_channel(channel)
        for field in reversed(feeddict["fields"]):
            embed.add_field(name=field["name"], value=field["value"], inline=False)
        try:
            await channel.send(embed=embed)
        except Forbidden:
            # TODO: maybe remove the feed from config to stop this happening in future?
            log.debug("Unable to send status update to guild")

    @checks.is_owner()
    @commands.command(hidden=True, aliases=["dfs"])
    async def devforcestatus(self, ctx, service):
        """
        THIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.

        It will send the current status of the service to **all

        Repeat: THIS COMMAND IS NOT SUPPORTED.
        """
        msg = await ctx.send(
            warning(
                "\nTHIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.\n\nIt will send the"
                " current status of the service to **all registered channels in all servers**.\n\n"
                "This has a high change of causing the main task to skip a status update if you time this "
                "command correctly.\n\nRepeat: THIS COMMAND IS NOT SUPPORTED.\nAre you sure you want to continue?"
            )
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result is not True:
            return await ctx.send("Aborting.")
        if service not in FEED_URLS.keys():
            return await ctx.send("Hmm, that doesn't look like a valid service.")

        feed = feedparser.parse(FEED_URLS[service])
        if service == "discord":
            feeddict = await parse_discord(feed.entries[0])
        elif service == "github":
            feeddict = await parse_github(feed.entries[0])
        elif service == "cloudflare":
            feeddict = await parse_cloudflare(feed.entries[0])
        else:
            return await ctx.send("Hmm, that doesn't look like a valid service. (2)")

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
    async def statusset_add(self, ctx, service: str, channel: discord.TextChannel):
        """
        Start getting status updates for the choses service!

        There is a list of services you can use in the `[p]statusset list` command.

        If you don't specify a specific channel, I will use the current channel.
        """
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
        async with self.config.guild(ctx.guild).feeds() as feeds:
            try:
                if isinstance(feeds[service], int):  # config migration
                    feeds[service] = [feeds[service]]
            except KeyError:
                feeds[service] = []

            feeds[service].append(channel.id)

        await ctx.send(
            f"Done, {channel.mention} will now receive {FEED_FRIENDLY_NAMES[service]} status updates."
        )

    @statusset.command(name="remove", aliases=["del", "delete"])
    async def statusset_remove(self, ctx, service: str, channel: discord.TextChannel):
        """Stop status updates for a specific service in this server"""
        # TODO: multiple services in one command
        if service not in FEED_URLS.keys():
            return await ctx.send(f"That's not a valid service. See `{ctx.clean_prefix}statusset list`.")
        async with self.config.guild(ctx.guild).feeds() as feeds:
            print(feeds)
            try:
                if channel.id not in feeds[service]:
                    return await ctx.send(
                        f"It looks like I don't send {FEED_FRIENDLY_NAMES[service]} status updates to {channel.mention}"
                    )
                feeds[service].remove(channel.id)
            except TypeError:
                channel = self.bot.get_channel(feeds[service])
                feeds[service] = []
            await ctx.send(f"Removed {FEED_FRIENDLY_NAMES[service]} status updates from {channel.mention}")

    @statusset.command(name="list", aliases=["show"])
    async def statusset_list(self, ctx):
        """List that available services and which ones are being used in this server"""
        guild_feeds = await self.config.guild(ctx.guild).feeds()
        pos_feeds = list(FEED_URLS.keys())

        if not guild_feeds:
            msg = "There are no status updates set up in this server.\n"
        else:
            msg = ""
            data = []
            for feed in guild_feeds.items():
                print(feed)
                if not feed[1]:
                    continue
                if isinstance(feed[1], int):
                    channel_ids = [feed[1]]
                else:
                    channel_ids = feed[1]
                channel_names = []
                for channel in channel_ids:
                    channel_names.append(f"#{self.bot.get_channel(channel).name}")
                channel_names = humanize_list(channel_names)
                data.append([feed[0], channel_names])
                try:
                    pos_feeds.remove(feed[0])
                except Exception as e:
                    print(feed[0])
                    print(pos_feeds)
                    print(e)
            if data:
                msg += "**Services used in this server:**"
                msg += box(tabulate(data, tablefmt="plain"), lang="arduino")
        if pos_feeds:
            msg += "**Other available services:** "
            msg += humanize_list(pos_feeds)
        await ctx.send(msg)


# TODO: preview command
# REMEMBER TIME IS EPOCH IN JSON