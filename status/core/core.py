import asyncio
import logging
from copy import deepcopy
from typing import Optional

import aiohttp
import sentry_sdk
import vexcogutils
from redbot.core import Config, commands
from redbot.core.bot import Red
from vexcogutils import format_help, format_info
from vexcogutils.meta import out_of_date_check

from status.commands.status_com import StatusCom
from status.commands.statusdev_com import StatusDevCom
from status.commands.statusset_com import StatusSetCom
from status.core import FEEDS
from status.core.abc import CompositeMetaClass
from status.core.statusapi import StatusAPI
from status.objects import (
    ConfigWrapper,
    LastChecked,
    ServiceCooldown,
    ServiceRestrictionsCache,
    UsedFeeds,
)
from status.updateloop import SendUpdate, StatusLoop

log = logging.getLogger("red.vex.status.core")


class Status(
    commands.Cog, StatusLoop, StatusCom, StatusDevCom, StatusSetCom, metaclass=CompositeMetaClass
):
    """
    Automatically check for status updates.

    When there is one, it will send the update to all channels that
    have registered to recieve updates from that service.

    There's also the `status` command which anyone can use to check
    updates whereever they want.

    If there's a service that you want added, contact Vexed#3211 or
    make an issue on the GitHub repo (or even better a PR!).
    """

    __version__ = "2.4.0"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        # config
        default: dict = {}  # pointless typehint but hey
        self.config: Config = Config.get_conf(
            self, identifier="Vexed-status"  # type:ignore
        )  # shit idntfr... bit late to change it... even mypy agrees...
        self.config.register_global(version=2)
        self.config.register_global(feed_store=default)
        self.config.register_global(old_ids=[])
        self.config.register_global(latest=default)  # this is unused? i think? remove soonish
        self.config.register_channel(feeds=default)
        self.config.register_guild(service_restrictions=default)

        # other stuff
        self.session = aiohttp.ClientSession()
        self.last_checked = LastChecked()
        self.config_wrapper = ConfigWrapper(self.config, self.last_checked)
        self.service_cooldown = ServiceCooldown()

        self.statusapi = StatusAPI(self.session)

        self.ready = False

        asyncio.create_task(self._async_init())

        if 418078199982063626 in self.bot.owner_ids:  # type:ignore  # im lazy
            try:
                self.bot.add_dev_env_value("status", lambda _: self)
                self.bot.add_dev_env_value("statusapi", lambda _: self.statusapi)
                self.bot.add_dev_env_value("sendupdate", lambda _: SendUpdate)
                log.debug("Added dev env vars.")
            except Exception:
                log.exception("Unable to add dev env vars.", exc_info=True)

        # =========================================================================================
        # NOTE: IF YOU ARE EDITING MY COGS, PLEASE ENSURE SENTRY IS DISBALED BY FOLLOWING THE INFO
        # IN async_init(...) BELOW (SENTRY IS WHAT'S USED FOR TELEMETRY + ERROR REPORTING)
        self.sentry_hub: Optional[sentry_sdk.Hub] = None
        # =========================================================================================

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        self.loop.cancel()
        asyncio.create_task(self.session.close())

        if self.sentry_hub and self.sentry_hub.client:
            self.sentry_hub.end_session()
            self.sentry_hub.client.close()  # type:ignore

        try:
            self.bot.remove_dev_env_value("status")
            self.bot.remove_dev_env_value("statusapi")
            self.bot.remove_dev_env_value("sendupdate")
        except KeyError:
            log.debug("Unable to remove dev env vars. They probably weren't added.")

        log.info("Status unloaded.")

    async def _async_init(self) -> None:
        await out_of_date_check("status", self.__version__)

        await self.bot.wait_until_red_ready()

        if await self.config.version() != 3:
            log.info("Getting initial data from services...")
            await self.migrate_to_v3()
            await self.get_initial_data()
            await self.config.incidents.clear()
            await self.config.version.set(3)
            log.info("Done!")
            self.actually_send = False
        else:
            self.actually_send = True

        self.used_feeds = UsedFeeds(await self.config.all_channels())
        self.service_restrictions_cache = ServiceRestrictionsCache(await self.config.all_guilds())

        # this will start the loop
        self.ready = True

        # =========================================================================================
        # TO DISABLE SENTRY FOR THIS COG (EG IF YOU ARE EDITING THIS COG) EITHER DISABLE SENTRY
        # WITH THE `[p]vextelemetry` COMMAND, OR UNCOMMENT THE LINE BELOW, OR REMOVE IT COMPLETELY:
        # return

        while vexcogutils.sentryhelper.ready is False:
            await asyncio.sleep(0.1)

        await vexcogutils.sentryhelper.maybe_send_owners("status")

        if vexcogutils.sentryhelper.sentry_enabled is False:
            log.debug("Sentry detected as disabled.")
            return

        log.debug("Sentry detected as enabled.")
        self.sentry_hub = await vexcogutils.sentryhelper.get_sentry_hub("status", self.__version__)
        # =========================================================================================

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.bot.on_command_error(ctx, error, unhandled_by_cog=True)  # type:ignore

        if self.sentry_hub is None:  # sentry disabled
            return

        with self.sentry_hub:
            sentry_sdk.add_breadcrumb(
                category="command", message="Command used was " + ctx.command.qualified_name
            )
            sentry_sdk.capture_exception(error.original)  # type:ignore
            log.debug("Above exception successfully reported to Sentry")

    async def get_initial_data(self) -> None:
        """Start with initial data from services."""
        old_ids = []
        for service, settings in FEEDS.items():
            log.debug(f"Starting {service}.")
            try:
                incidents, etag, status = await self.statusapi.incidents(settings["id"])
                if status != 200:
                    log.warning(f"Unable to get initial data from {service}: HTTP status {status}")
                incs = incidents["incidents"]
                for inc in incs:
                    old_ids.append(inc["id"])
                    old_ids.extend([i["id"] for i in inc["incident_updates"]])
            except Exception:
                log.warning(f"Unable to get initial data from {service}.", exc_info=True)
                continue

            try:
                scheduled, etag, status = await self.statusapi.scheduled_maintenance(
                    settings["id"]
                )
                if status != 200:
                    log.warning(f"Unable to get initial data from {service}: HTTP status {status}")
                incs = scheduled["scheduled_maintenances"]
                for inc in incs:
                    old_ids.append(inc["id"])
                    old_ids.extend([i["id"] for i in inc["incident_updates"]])
            except Exception:
                log.warning(f"Unable to get initial data from {service}.", exc_info=True)
                continue

        await self.config.old_ids.set(old_ids)

    async def migrate_to_v3(self) -> None:
        """Set up conifg for version 3"""
        # ik this is a mess
        really_old = await self.config.all_channels()
        log.debug("Config migration in progress. Old data is below in case something goes wrong.")
        log.debug(really_old)
        for c_id, data in really_old.items():
            c_old = deepcopy(data)["feeds"]
            for service in data.get("feeds", {}).keys():
                if service in ["twitter", "status.io", "aws", "gcp", "smartthings"]:
                    c_old.pop(service, None)
                else:
                    c_old[service]["edit_id"] = {}

            await self.config.channel_from_id(c_id).feeds.set(c_old)

    @commands.command(name="statusinfo", hidden=True)
    async def command_statusinfo(self, ctx: commands.Context):
        await ctx.send(
            await format_info(self.qualified_name, self.__version__, loops=[self.loop_meta])
        )
