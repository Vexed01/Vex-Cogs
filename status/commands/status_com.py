import asyncio
import datetime

from aiohttp.client import ClientSession
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, humanize_timedelta

from ..commands.converters import ServiceConverter
from ..core.statusapi import StatusAPI
from ..objects.caches import (LastChecked, ServiceCooldown,
                              ServiceRestrictionsCache)
from ..objects.configwrapper import ConfigWrapper
from ..objects.incidentdata import Update
from ..objects.sendcache import SendCache
from ..updateloop.processfeed import process_incidents, process_scheduled
from ..updateloop.sendupdate import SendUpdate


class StatusCom:
    def __init__(self):
        self.bot: Red
        self.config: Config
        self.config_wrapper: ConfigWrapper
        self.last_checked: LastChecked
        self.session: ClientSession
        self.service_restrictions_cache: ServiceRestrictionsCache
        self.statusapi: StatusAPI

        self.service_cooldown: ServiceCooldown

    # TODO: support DMs
    @commands.guild_only()
    @commands.cooldown(10, 120, commands.BucketType.user)
    @commands.command()
    async def status(self, ctx: commands.Context, service: ServiceConverter):
        """
        Check for incidents for a variety of services, eg Discord.

        **Available Services:**

        discord, github, zoom, reddit, epic_games, cloudflare, statuspage,
        python, twitter_api, oracle_cloud, twitter, digitalocean, sentry,
        geforcenow
        """
        if time_until := self.service_cooldown.handle(ctx.author.id, service.name):
            message = "Status updates for {} are on cooldown. Try again in {}.".format(
                service.friendly, humanize_timedelta(seconds=time_until)
            )
            return await ctx.send(message, delete_after=time_until)

        if restrictions := self.service_restrictions_cache.get_guild(ctx.guild.id, service.name):
            channels = [self.bot.get_channel(channel) for channel in restrictions]
            channels = humanize_list([channel.mention for channel in channels if channel], style="or")
            if channels:
                return await ctx.send(f"You can check updates for {service.friendly} in {channels}.")

        await ctx.trigger_typing()

        summary, etag, status = await self.statusapi.summary(service.id)

        if status != 200:
            return await ctx.send(f"Hmm, I can't get {service.friendly}'s status at the moment.")

        incidents_incidentdata_list = process_incidents(summary)
        all_scheduled = process_scheduled(summary)
        now = datetime.datetime.now(datetime.timezone.utc)
        scheduled_incidentdata_list = [i for i in all_scheduled if i.scheduled_for < now]  # only want ones happening

        other_incidents, other_scheduled = [], []
        if incidents_incidentdata_list:
            to_send = incidents_incidentdata_list[0]
            other_incidents = incidents_incidentdata_list[1:]
        elif scheduled_incidentdata_list:  # only want to send 1 thing
            to_send = scheduled_incidentdata_list[0]
            other_scheduled = scheduled_incidentdata_list[1:]
        else:
            to_send = None

        if not to_send:
            msg = "\N{WHITE HEAVY CHECK MARK} There are currently no live incidents."
            return await ctx.send(msg)

        update = Update(to_send, to_send.fields)
        SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            {ctx.channel.id: {"mode": "all", "webhook": False}},
            dispatch=False,
            force=True,
        )
        await asyncio.sleep(0.2)

        msg = ""

        if other_incidents:
            msg += f"{len(other_incidents)} other incidents are live at the moment:\n"
            for incident in other_incidents:
                msg += f"{incident.title} (<{incident.link}>)\n"

        if other_scheduled:
            msg += f"\n{len(other_scheduled)} other scheduled maintenance events are live at the moment:\n"
            for incident in other_scheduled:
                msg += f"{incident.title} (<{incident.link}>)"

        if msg:
            await ctx.send(msg)
