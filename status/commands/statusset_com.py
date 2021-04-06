import asyncio
from time import time
from typing import Optional

import discord
from aiohttp import ClientSession
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_list
from redbot.core.utils.predicates import MessagePredicate
from tabulate import tabulate

from ..core.consts import FEEDS, SPECIAL_INFO
from ..core.statusapi import StatusAPI
from ..objects.caches import (LastChecked, ServiceCooldown,
                              ServiceRestrictionsCache, UsedFeeds)
from ..objects.configwrapper import ConfigWrapper
from ..objects.incidentdata import Update
from ..objects.sendcache import SendCache
from ..updateloop.processfeed import process_incidents
from ..updateloop.sendupdate import SendUpdate
from ..updateloop.updatechecker import UpdateChecker
from .converters import ModeConverter, ServiceConverter


class StatusSetCom:
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

    @commands.guild_only()
    @checks.admin_or_permissions(manage_guild=True)
    @commands.group()
    async def statusset(self, ctx: commands.Context):
        """
        Get automatic status updates in a channel, eg Discord.

        Get started with `[p]statusset preview` to see what they look like,
        then `[p]statusset add` to set up automatic updates.

        **Available services:**
        discord, github, zoom, reddit, epic_games, cloudflare, statuspage,
        python, twitter_api, oracle_cloud, twitter, digitalocean, sentry,
        geforcenow
        """

    @statusset.command(name="add")
    async def statusset_add(
        self, ctx: commands.Context, service: ServiceConverter, channel: Optional[discord.TextChannel]
    ):
        """
        Start getting status updates for the chosen service!

        There is a list of services you can use in the `[p]statusset list` command.

        This is an interactive command. It will ask what mode you want to use and if you
        want to use a webhook. You can use the `[p]statusset preview` command to see how
        different options look or take a look at https://vex-cogs.rtfd.io/en/latest/cogs/statusref.html

        If you don't specify a specific channel, I will use the current channel.
        """
        channel = channel or ctx.channel

        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send(f"I don't have permissions to send messages in {channel.mention}")

        existing_feeds = await self.config.channel(channel).feeds()
        if service in existing_feeds.keys():
            return await ctx.send(
                f"{channel.mention} already receives {service.friendly} status updates. You can edit it with "
                f"`{ctx.clean_prefix}statusset edit`."
            )

        modes = (
            "**All**: Every time the service posts an update on an incident, I will send a new message "
            "containing the previous updates as well as the new update. Best used in a fast-moving "
            "channel with other users.\n\n"
            "**Latest**: Every time the service posts an update on an incident, I will send a new message "
            "containing only the latest update. Best used in a dedicated status channel.\n\n"
            "**Edit**: When a new incident is created, I will sent a new message. When this incident is "
            "updated, I will then add the update to the original message. Best used in a dedicated status "
            "channel.\n\n"
        )

        # === MODE ===

        await ctx.send(
            "This is an interactive configuration. You have 2 minutes to answer each question.\n"
            f"If you aren't sure what to choose, just say `cancel` and take a look at the **`{ctx.clean_prefix}"
            f"statusset preview`** command.\n\n**What mode do you want to use?**\n\n{modes}"
        )

        try:
            # really shouldn't monkey patch this
            mode = await ModeConverter.convert(
                None,
                ctx,
                (await self.bot.wait_for("message", check=MessagePredicate.same_context(ctx), timeout=120)).content,
            )
        except asyncio.TimeoutError:
            return await ctx.send("Timed out. Cancelling.")
        except commands.BadArgument as e:
            return await ctx.send(e)

        # === WEBHOOK ===

        if channel.permissions_for(ctx.me).manage_webhooks:
            await ctx.send(
                "**Would you like to use a webhook?** (yes or no answer)\nUsing a webhook means that the status "
                f"updates will be sent with the avatar as {service.friendly}'s logo and the name will be "
                f"`{service.friendly} Status Update`, instead of my avatar and name."
            )

            pred = MessagePredicate.yes_or_no(ctx)
            try:
                await self.bot.wait_for("message", check=pred, timeout=120)
            except asyncio.TimeoutError:
                return await ctx.send("Timed out. Cancelling.")

            webhook = pred.result
            if webhook:
                # already checked for perms to create
                # thanks flare for your webhook logic (redditpost) (or trusty?)
                existing_webhook = False
                for hook in await channel.webhooks():
                    if hook.name == channel.guild.me.name:
                        existing_webhook = True
                if not existing_webhook:
                    await channel.create_webhook(name=channel.guild.me.name, reason="Created for status updates.")
        else:
            await ctx.send(
                "I would ask about whether you want me to send updates as a webhook (so they match the "
                "service), however I don't have the `manage webhooks` permission."
            )
            webhook = False

        # === RESTRICT ===

        await ctx.send(
            f"**Would you like to restrict access to {service.friendly} in the `{ctx.clean_prefix}status` command?** "
            "(yes or no answer)\nThis will reduce spam. If there's an incident, members will instead be redirected "
            f"to {channel.mention} and any other channels that you've set to receive {service.friendly} status updates"
            " which have restrict enabled."
        )

        pred = MessagePredicate.yes_or_no(ctx)
        try:
            await self.bot.wait_for("message", check=pred, timeout=120)
        except asyncio.TimeoutError:
            return await ctx.send("Timed out. Cancelling.")

        if pred.result is True:
            async with self.config.guild(ctx.guild).service_restrictions() as sr:
                try:
                    sr[service.name].append(channel.id)
                except KeyError:
                    sr[service.name] = [channel.id]

                self.service_restrictions_cache.add_restriction(ctx.guild.id, service.name, channel.id)

        # === FINISH ===

        settings = {"mode": mode, "webhook": webhook, "edit_id": {}}
        await self.config.channel(channel).feeds.set_raw(service.name, value=settings)
        self.used_feeds.add_feed(service.name)

        if service in SPECIAL_INFO.keys():
            msg = f"NOTE: {SPECIAL_INFO[service.name]}\n"
        else:
            msg = ""

        await ctx.send(f"{msg}Done, {channel.mention} will now receive {service.friendly} status updates.")

    @statusset.command(name="remove", aliases=["del", "delete"])
    async def statusset_remove(
        self, ctx: commands.Context, service: ServiceConverter, channel: Optional[discord.TextChannel]
    ):
        """
        Stop status updates for a specific service in this server.

        If you don't specify a channel, I will use the current channel.
        """
        channel = channel or ctx.channel

        async with self.config.channel(ctx.channel).feeds() as feeds:
            feeds: dict
            if not feeds.pop(service.name, None):
                return await ctx.send(f"It looks like I don't send {service.friendly} updates in {channel.mention}.")

        self.used_feeds.remove_feed(service.name)

        async with self.config.guild(ctx.guild).service_restrictions() as sr:
            try:
                sr[service.name].remove(channel.id)
            except KeyError:
                pass

            self.service_restrictions_cache.remove_restriction(self.guild.id, service.name, channel.id)

        await ctx.send(f"Removed {service.friendly} status updated from {channel.mention}")

    @statusset.command(name="list", aliases=["show", "settings"])
    async def statusset_list(self, ctx: commands.Context, service: Optional[ServiceConverter]):
        """
        List that available services and ones are used in this server.

        Optionally add a service at the end of the command to view detailed settings for that service.
        """
        # this needs refactoring
        # i basically copied and pasted in rewrite
        # maybe stick the two sections in .utils

        unused_feeds = list(FEEDS.keys())

        if service:
            data = []
            for channel in ctx.guild.channels:
                feeds = await self.config.channel(channel).feeds()
                restrictions = await self.config.guild(ctx.guild).service_restrictions()
                for name, settings in feeds.items():
                    if name != service.name:
                        continue
                    mode = settings["mode"]
                    webhook = settings["webhook"]
                    if channel.id in restrictions.get(service, []):
                        restrict = True
                    else:
                        restrict = False
                    data.append([f"#{channel.name}", mode, webhook, restrict])

            table = box(tabulate(data, headers=["Channel", "Send mode", "Use webhooks", "Restrict"]))
            await ctx.send(
                f"**Settings for {service.name}**: {table}\n`Restrict` is whether or not to restrict access for "
                f"{service.name} server-wide in the `status` command. Users are redirected to an appropriate channel."
            )

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
    async def statusset_preview(
        self, ctx: commands.Context, service: ServiceConverter, mode: ModeConverter, webhook: bool
    ):
        """
        Preview what status updates will look like.

        You can also see this at https://vex-cogs.rtfd.io/en/latest/cogs/statusref.html

        **<service>**

            The service you want to preview. There's a list of available services in the
            `[p]help statusset` command.

        **<mode>**

            **all**: Every time the service posts an update on an incident, I will send
            a new message containing the previous updates as well as the new update. Best
            used in a fast-moving channel with other users.

            **latest**: Every time the service posts an update on an incident, I will send
            a new message containing only the latest update. Best used in a dedicated status
            channel.

            **edit**: Naturally, edit mode can't have a preview so won't work with this command.
            The message content is the same as the `all` mode.
            When a new incident is created, I will sent a new message. When this
            incident is updated, I will then add the update to the original message. Best
            used in a dedicated status channel.

        **<webhook>**

            Using a webhook means that the status updates will be sent with the avatar
            as the service's logo and the name will be `[service] Status Update`, instead
            of my avatar and name.
        """
        if webhook and not ctx.channel.permissions_for(ctx.me).manage_messages:
            return await ctx.send("I don't have permission to manage webhook.")

        incidentdata, extra_info = await self.config_wrapper.get_latest(service.name)

        if incidentdata is None or (time() - extra_info.get("checked", 0) > 300):  # its older than 3 mins
            try:
                json_resp, etag, status = await self.statusapi.incidents(service.id)
            except Exception:
                return await ctx.send("Hmm, I couldn't preview that.")
            if status != 200:
                return await ctx.send("Hmm, I couldn't preview that.")
            incidentdata_list = process_incidents(json_resp)
            await self.config_wrapper.update_incidents(service.name, incidentdata_list[0])

        incidentdata = incidentdata_list[0]
        update = Update(incidentdata, [incidentdata.fields[-1]])

        SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            {ctx.channel.id: {"mode": mode, "webhook": webhook}},
            False,
            True,
        )

    # ################################### EDIT ###################################################

    @statusset.group()
    async def edit(self, ctx: commands.Context):
        """Edit services you've already set up."""

    @edit.command(name="mode")
    async def edit_mode(
        self,
        ctx: commands.Context,
        channel: Optional[discord.TextChannel],
        service: ServiceConverter,
        mode: ModeConverter,
    ):
        """Change what mode to use for status updates.

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

        old_conf = await self.config.channel(channel).feeds()
        if service.name not in old_conf.keys():
            return await ctx.send(f"It looks like I don't send {service.friendly} status updates to {channel.mention}")

        if old_conf[service.name]["mode"] == mode:
            return await ctx.send(
                f"It looks like I already use that mode for {service.friendly} updates in {channel.mention}"
            )

        old_conf[service.name]["mode"] = mode
        await self.config.channel(channel).feeds.set_raw(service.name, value=old_conf[service.name])

        await ctx.send(f"{service.friendly} status updates in {channel.mention} will now use the {mode} mode.")

    @edit.command(name="webhook")
    async def edit_webhook(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel], service: ServiceConverter, webhook: bool
    ):
        """Set whether or not to use webhooks for status updates.

        Using a webhook means that the status updates will be sent with the avatar as the service's
        logo and the name will be `[service] Status Update`, instead of my avatar and name.

        If you don't specify a channel, I will use the current channel.
        """
        channel = channel or ctx.channel

        old_conf = await self.config.channel(channel).feeds()
        if service.name not in old_conf.keys():
            return await ctx.send(f"It looks like I don't send {service.friendly} status updates to {channel.mention}")

        if old_conf[service.name]["webhook"] == webhook:
            word = "use" if webhook else "don't use"
            return await ctx.send(
                f"It looks like I already {word} webhooks for {service.friendly} status updates in {channel.mention}"
            )

        if webhook and not ctx.channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.send("I don't have manage webhook permissions so I can't do that.")

        old_conf[service.name]["edit_id"] = {}
        old_conf[service.name]["webhook"] = webhook
        await self.config.channel(channel).feeds.set_raw(service.name, value=old_conf[service.name])

        word = "use" if webhook else "not use"
        await ctx.send(f"{service.friendly} status updates in {channel.mention} will now {word} webhooks.")

    @edit.command(name="restrict")
    async def edit_restrict(
        self, ctx: commands.Context, channel: Optional[discord.TextChannel], service: ServiceConverter, restrict: bool
    ):
        """
        Restrict access to the service in the `status` command.

        Enabling this will reduce spam. Instead of sending the whole update
        (if there's an incident) members will instead be redirected to channels
        that automatically receive the status updates, that they have permission to to view.
        """
        channel = channel or ctx.channel

        feed_settings = await self.config.channel(channel).feeds()
        if service.name not in feed_settings.keys():
            return await ctx.send(f"It looks like I don't send {service.friendly} status updates to {channel.mention}")

        old_conf = (await self.config.guild(ctx.guild).service_restrictions()).get(service.name, [])
        old_bool = channel.id in old_conf
        if old_bool == restrict:
            word = "" if restrict else "don't "
            return await ctx.send(
                f"It looks like I already {word}restrict {service.friendly} status updates for the " "`status` command."
            )

        async with self.config.guild(ctx.guild).service_restrictions() as sr:
            if restrict:
                try:
                    sr[service.name].append(channel.id)
                except KeyError:
                    sr[service.name] = [channel.id]
                self.service_restrictions_cache.add_restriction(ctx.guild.id, service.name, channel.id)
            else:
                sr[service.name].remove(channel.id)
                self.service_restrictions_cache.remove_restriction(ctx.guild.id, service.name, channel.id)

        word = "" if restrict else "not "
        await ctx.send(f"{service.friendly} will now {word}be restricted in the `status` command.")
