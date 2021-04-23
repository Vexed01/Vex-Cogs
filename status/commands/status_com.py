import datetime
from collections import defaultdict
from typing import Dict, List, NamedTuple, Optional

import discord
from discord.channel import TextChannel
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_list, humanize_timedelta

from status.commands.converters import ServiceConverter
from status.core.abc import MixinMeta
from status.objects import IncidentData, SendCache, Update
from status.updateloop import SendUpdate, process_json


class Comps(NamedTuple):
    groups: Dict[str, str]
    degraded_comps: Dict[str, List[str]]


def process_components(json_data: dict) -> Comps:
    components: List[dict] = json_data["components"]

    groups: Dict[str, str] = {}
    for comp in components:
        if comp.get("group"):
            groups[comp.get("id", "uh oh")] = comp.get("name", "")

    degraded_comps: Dict[str, List[str]] = defaultdict(list)
    for comp in components:
        if comp.get("status") == "operational":
            continue

        name: str = comp.get("name", "")
        status: str = comp.get("status", "").replace("_", " ")

        degraded_comps[groups.get(comp.get("group_id", "")) or "No group"].append(
            f"{name}: {status.capitalize()}"
        )

    return Comps(groups, degraded_comps)


class StatusCom(MixinMeta):

    # TODO: support DMs
    @commands.guild_only()
    @commands.cooldown(10, 120, commands.BucketType.user)
    @commands.command()
    async def status(self, ctx: commands.Context, service: ServiceConverter):
        """
        Check for the status of a variety of services, eg Discord.

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

        if restrictions := self.service_restrictions_cache.get_guild(
            ctx.guild.id, service.name  # type:ignore  # guild check
        ):
            channels = [self.bot.get_channel(channel) for channel in restrictions]
            channel_list = humanize_list(
                [channel.mention for channel in channels if isinstance(channel, TextChannel)],
                style="or",
            )
            if channel_list:
                return await ctx.send(
                    f"You can check updates for {service.friendly} in {channel_list}."
                )

        await ctx.trigger_typing()

        summary, etag, status = await self.statusapi.summary(service.id)

        if status != 200:
            return await ctx.send(f"Hmm, I can't get {service.friendly}'s status at the moment.")

        incidents_incidentdata_list = process_json(summary, "incidents")
        all_scheduled = process_json(summary, "scheduled")
        components = process_components(summary)
        now = datetime.datetime.now(datetime.timezone.utc)
        scheduled_incidentdata_list = [
            i for i in all_scheduled if i.scheduled_for and i.scheduled_for < now
        ]  # only want ones happening

        to_send: Optional[IncidentData]
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
            msg = (
                "\N{WHITE HEAVY CHECK MARK} There are no ongoing incidents or scheduled "
                "maintenace."
            )
        else:
            msg = ""

        if components.degraded_comps:
            embed = discord.Embed(
                title="Components",
                timestamp=datetime.datetime.utcnow(),
                colour=await ctx.embed_colour(),
            )
            for group, comps in components.degraded_comps.items():
                value = ""
                for comp in comps:
                    value += comp + "\n"
                embed.add_field(name=group, value=value, inline=False)

            await ctx.send(msg, embed=embed)
        else:
            msg += "\n\N{WHITE HEAVY CHECK MARK} All components are operational."

            await ctx.send(msg)

        if to_send:
            msg = ""

            update = Update(to_send, to_send.fields)
            await SendUpdate(
                self.bot,
                self.config_wrapper,
                update,
                service.name,
                SendCache(update, service.name),
                dispatch=False,
                force=True,
            ).send(
                {ctx.channel.id: {"mode": "all", "webhook": False, "edit_id": {}}},
            )

            if other_incidents:
                msg += f"{len(other_incidents)} other incidents are live at the moment:\n"
                for incident in other_incidents:
                    msg += f"{incident.title} (<{incident.link}>)\n"
                msg += "\n"

            if other_scheduled:
                msg += (
                    f"{len(other_scheduled)} other scheduled maintenance events are live at the "
                    "moment:\n"
                )
                for incident in other_scheduled:
                    msg += f"{incident.title} (<{incident.link}>)\n"
                msg += "\n"

            if msg:
                await ctx.send(msg)
