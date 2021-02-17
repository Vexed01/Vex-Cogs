import asyncio
import logging
from urllib.error import URLError

import discord
import feedparser
from discord.errors import Forbidden
from discord.ext import tasks
from discord.ext.commands.core import guild_only
from feedparser.util import FeedParserDict
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list, warning
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
        second_default_global = []
        default_guild = {}
        self.config.register_global(etags=default_global)
        self.config.register_global(to_check=second_default_global)
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
        async with self.config.etags() as etags:
            for feed in FEED_URLS.items():  # change to await self.config.to_check()
                try:
                    response = feedparser.parse(feed[1], etag=etags[feed[0]])
                    if response.status == 200:
                        etags[feed[0]] = response.etag
                        feeddict = await self.process_feed(feed[0], response)
                        channels = await self.get_channels(feed[0])
                        log.debug(
                            f"Sending status update for {feed[0]} to {len(channels)} servers..."
                        )
                        for channel in channels:
                            await self.send_updated_feed(feeddict, channel)
                        log.debug("Done")
                    else:
                        log.debug(f"No status update for {feed[0]}")
                except (ConnectionRefusedError, URLError):
                    log.warning(f"Unable to connect to {feed[0]}")
                    continue
                except KeyError:  # a new service has been aded, cba to be proper config migtation. will
                    etags[feed[0]] = "hello"

    @check_for_updates.before_loop
    async def before_start(self):
        await self.bot.wait_until_red_ready()

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
        """Get the channels for a feed. The list is channel IDs, they may be invalid."""
        feeds = await self.config.all_guilds()
        target_service = service
        channels = []
        # example: {133049272517001216: {'feeds': {'discord': 133251234164375552, 'github': 133251234164375552}}}
        for server in feeds.items():
            for service in server[1]["feeds"].items():
                if service[0] == target_service:
                    channels.append(service[1])
        return channels

    async def send_updated_feed(self, feeddict: dict, channel: int):
        # TODO: non-embed version
        embed = discord.Embed(
            title=feeddict["title"],
            description=feeddict["desc"],
            timestamp=feeddict["time"],
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
    @commands.command(hidden=True)
    async def devforcestatus(self, ctx, service):
        """
        THIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.

        It will send the current status of the service to the current channel.

        Repeat: THIS COMMAND IS NOT SUPPORTED.
        """
        msg = await ctx.send(
            warning(
                "\nTHIS COMMNAD IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.\n\nIt will send the"
                " current status of the service to the current channel.\n\n"
                "Repeat: THIS COMMAND IS NOT SUPPORTED.\nAre you sure you want to continue?"
            )
        )
        start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(msg, ctx.author)
        await ctx.bot.wait_for("reaction_add", check=pred)
        if pred.result is not True:
            return await ctx.send("Aborting.")
        if service not in FEED_URLS.keys():
            return await ctx.send("Hmm, that doensn't look like a valid service.")

        feed = feedparser.parse(FEED_URLS[service])
        if service == "discord":
            feeddict = await parse_discord(feed.entries[0])
        elif service == "github":
            feeddict = await parse_github(feed.entries[0])
        elif service == "cloudflare":
            feeddict = await parse_cloudflare(feed.entries[0])

        await self.send_updated_feed(feeddict, ctx.channel.id)

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

        If you don't specify a specifc channel, I will use the current channel.
        """
        channel = channel or ctx.channel
        service = service.lower()
        if service not in FEED_URLS.keys():
            return await ctx.send(
                "That's not a valid service. See `{ctx.clean_prefix}statusset list`."
            )
        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send(
                f"I don't have permission to send messages in {channel.mention}."
            )
        if not channel.permissions_for(ctx.me).embed_links:
            return await ctx.send(
                f"I don't have permission to send embeds in {channel.mention}. "
                "This is called `embed links` in Discord's permission system."
            )
        async with self.config.guild(ctx.guild).feeds() as feeds:
            if service in feeds.keys():
                used_channel = feeds[service]
                if used_channel == channel.id:
                    return await ctx.send(
                        f"I'm already sending {FEED_FRIENDLY_NAMES[service]} status updates in this channel!"
                    )
                else:
                    return await ctx.send(  # maybe instead ask if they want to move it
                        f"It look like I'm already sending {FEED_FRIENDLY_NAMES[service]} status updates"
                        f" in {used_channel.mention}. I can only send to one channel. Use "
                        f"the `{ctx.clean_prefix}statusset remove {service}` command, then try"
                        f" adding it to {channel.mention}again."
                    )

            feeds[service] = channel.id

        await ctx.send(
            f"Done, {channel.mention} will now recieve {FEED_FRIENDLY_NAMES[service]} status updates."
        )

    @statusset.command(name="remove", aliases=["del", "delete"])
    async def statusset_remove(self, ctx, service: str):
        """Stop staus updates for a specifc service in this server"""
        # TODO: multiple services in one command
        if service not in FEED_URLS.keys():
            return await ctx.send(
                f"That's not a valid service. See `{ctx.clean_prefix}statusset list`."
            )
        async with self.config.guild(ctx.guild).feeds() as feeds:
            if service not in feeds.keys():
                return await ctx.send(
                    "It looks like I already don't send status updates for that service in this server!"
                )
            removed = feeds.pop(service, None)
            mention = self.bot.get_channel(removed).mention or "unknown"
            await ctx.send(f"Removed {FEED_FRIENDLY_NAMES[service]} status updates from {mention}")

    @statusset.command(name="list", aliases=["show"])
    async def statusset_list(self, ctx):
        """List that avalible services and which ones are being used in this server"""
        guild_feeds = await self.config.guild(ctx.guild).feeds()
        pos_feeds = list(FEED_URLS.keys())

        if not guild_feeds:
            msg = "There are no status updates set up in this server.\n"
        else:
            data = []
            for feed in guild_feeds.items():
                channel_name = self.bot.get_channel(feed[1]).name
                data.append([feed[0], f"#{channel_name}"])
                try:
                    pos_feeds.remove(feed[0])
                except Exception as e:
                    print(feed[0])
                    print(pos_feeds)
                    print(e)
            msg = "**Services used in this server:**"
            msg += box(tabulate(data, tablefmt="plain"), lang="arduino")
        if pos_feeds:
            msg += "**Other avalible services:** "
            msg += humanize_list(pos_feeds)
        await ctx.send(msg)
