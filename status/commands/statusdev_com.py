import logging
from time import time

from aiohttp import ClientSession
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils.chat_formatting import box, pagify, warning
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import ReactionPredicate
from tabulate import tabulate

from ..commands.converters import ModeConverter, ServiceConverter
from ..core.statusapi import StatusAPI
from ..objects.caches import (LastChecked, ServiceCooldown,
                              ServiceRestrictionsCache, UsedFeeds)
from ..objects.configwrapper import ConfigWrapper
from ..objects.incidentdata import Update
from ..objects.sendcache import SendCache
from ..updateloop.processfeed import process_incidents, process_scheduled
from ..updateloop.sendupdate import SendUpdate
from ..updateloop.updatechecker import UpdateChecker

_log = logging.getLogger("red.vexed.status.dev")


class StatusDevCom:
    def __init__(self):
        self.bot: Red
        self.config: Config
        self.config_wrapper: ConfigWrapper
        self.last_checked: LastChecked
        self.service_cooldown: ServiceCooldown
        self.session: ClientSession
        self.used_feeds: UsedFeeds
        self.service_restrictions_cache: ServiceRestrictionsCache
        self.update_checker: UpdateChecker
        self.statusapi: StatusAPI

    def super_unsupported():
        async def predicate(ctx: commands.Context):
            if ctx.author.id == 418078199982063626:  # vexed (my) id
                return True

            msg = await ctx.send(
                warning(
                    "\nTHIS COMMAND IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.\n\nUnintended things can "
                    "happen.\n\nRepeat: THIS COMMAND IS NOT SUPPORTED.\nAre you sure you want to continue?"
                )
            )
            start_adding_reactions(msg, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(msg, ctx.author)
            await ctx.bot.wait_for("reaction_add", check=pred, timeout=15)
            if pred.result is not True:
                await ctx.send("Aborting.")
                return False
            return True

        return commands.check(predicate)

    @commands.guild_only()
    @commands.is_owner()
    @commands.group(hidden=True)
    async def statusdev(self, ctx: commands.Context):
        """Don't use this; hidden for a reason; stuff _might_ break."""

    @super_unsupported()
    @statusdev.command(aliases=["cf"], hidden=True)
    async def checkfeed(
        self, ctx: commands.Context, service: ServiceConverter, mode: ModeConverter = "all", webhook: bool = False
    ):
        """Check the current status of a feed in the current channel"""
        json_resp, etag, status = await self.statusapi.incidents(service.id)
        incidentdata = process_incidents(json_resp)[0]

        update = Update(incidentdata, [incidentdata.fields[-1]])
        SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            {ctx.channel.id: {"mode": mode, "webhook": webhook}},
            True,
            True,
        )

        json_resp, _, _ = await self.statusapi.scheduled_maintenance(service.id)
        incidentdata_list = process_scheduled(json_resp)  # some have no scheduled maintenance
        if incidentdata_list:
            incidentdata = incidentdata_list[0]
        else:
            return
        update = Update(incidentdata, [incidentdata.fields[-1]])
        SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            {ctx.channel.id: {"mode": mode, "webhook": webhook}},
            True,
            True,
        )

    @super_unsupported()
    @statusdev.command(aliases=["cfr"], hidden=True)
    async def checkfeedraw(self, ctx: commands.Context, service: ServiceConverter):
        """Get raw JSON data"""
        resp, etag, status = await self.statusapi.incidents(service.id)

        await ctx.send(f"Status: `{status}`\nETag: `{etag}`\nResponse:")
        await ctx.send_interactive(pagify(str(resp)), box_lang="")

    @super_unsupported()
    @statusdev.command(aliases=["fs"], hidden=True)
    async def forcestatus(self, ctx: commands.Context, service: ServiceConverter):
        """Simulate latest incident. SENDS TO ALL CHANNELS IN ALL REGISTERED GUILDS."""
        json_resp, etag, status = await self.statusapi.incidents(service.id)
        incidentdata = process_incidents(json_resp)[0]

        update = Update(incidentdata, [incidentdata.fields[-1]])

        channels = await self.config_wrapper.get_channels(service.name)
        sendcache = SendCache(update, service)

        SendUpdate(
            bot=self.bot,
            config_wrapper=self.config_wrapper,
            update=update,
            service=service.name,
            sendcache=sendcache,
            channels=channels,
            dispatch=True,
            force=True,
        )

    @statusdev.command(aliases=["cd"], hidden=True)
    async def cooldown(self, ctx: commands.Context, user_id: int = None):
        """Get custom cooldown info for a user"""
        await ctx.send(box(self.service_cooldown.get_from_id(user_id or ctx.author.id)))

    @statusdev.command(aliases=["cfc"], hidden=True)
    async def checkusedfeedcache(self, ctx: commands.Context):
        """Check what feeds this is checking"""
        raw = box(self.used_feeds, lang="py")
        actual = box(self.used_feeds.get_list(), lang="py")
        await ctx.send(f"**Raw data:**\n{raw}\n**Active:**\n{actual}")

    @statusdev.command(aliases=["cgr"], hidden=True)
    async def checkguildrestrictions(self, ctx: commands.Context):
        """Check guild restrictins for current guild"""
        await ctx.send(box(self.service_restrictions_cache.get_guild(ctx.guild.id)))

    @statusdev.command(aliases=["ri"], hidden=True)
    async def refreshincidentids(self, ctx: commands.Context):
        """Regenerate the cache of past incident IDs."""
        await ctx.send("Starting.")
        await self._get_initial_data()  # not typehinted, promise me it works
        await ctx.send("Done.")

    @statusdev.command(aliases=["l"], hidden=True)
    async def loopstatus(self, ctx: commands.Context):
        """Check status of the loop"""
        loop = self.update_checker.loop

        data1 = [
            ["next_iteration", loop.next_iteration],
            ["_last_iteration", loop._last_iteration],
            ["is_running", loop.is_running()],
            ["failed", loop.failed()],
            ["_last_iteration_failed", loop._last_iteration_failed],
            ["current_loop", loop.current_loop],
        ]

        data2 = [
            ["Seconds until next", loop.next_iteration.timestamp() - time()],
            ["Seconds since last", time() - loop._last_iteration.timestamp()],
        ]

        await ctx.send("**Attributes:**\n{}\n**Parsed:**\n{}".format(box(tabulate(data1)), box(tabulate(data2))))

    @super_unsupported()
    @statusdev.command(aliases=["rl"], hidden=True)
    async def restartloop(self, ctx: commands.Context):
        """Restart the loop (if `statusdev loopstatus` is all positive DO NOT DO THIS)"""
        self.update_checker.loop.restart()
        await ctx.tick()

    @super_unsupported()
    @statusdev.command(aliases=["dev"], hidden=True)
    async def devenvvars(self, ctx: commands.Context):
        """
        Add some dev env vars

        Adds `status`, `loop`, `statusapi`, `sendupdate`.

        These will be removed on cog unload.
        """
        try:
            self.bot.add_dev_env_value("status", lambda x: self)
            self.bot.add_dev_env_value("loop", lambda x: self.update_checker.loop)
            self.bot.add_dev_env_value("statusapi", lambda _: self.statusapi)
            self.bot.add_dev_env_value("sendupdate", lambda _: SendUpdate)
            await ctx.send(
                "Added dev env vars `status`, `loop`, `statusapi`, `sendupdate`. They will be removed on cog unload."
            )
        except Exception:
            _log.exception("Unable to add dev env vars.")
            await ctx.send("I was unable to add them. Check the logs.")
