from __future__ import annotations

from time import time
from typing import TYPE_CHECKING, Optional, Union

import discord
from discord.abc import GuildChannel
from discord.member import Member
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, humanize_list
from tabulate import tabulate

from ..commands.command import DynamicHelp, DynamicHelpGroup
from ..commands.components import AddServiceView
from ..commands.converters import ModeConverter, ServiceConverter
from ..core import FEEDS, SPECIAL_INFO
from ..core.abc import MixinMeta
from ..core.consts import SERVICE_LITERAL
from ..objects import SendCache, Update
from ..updateloop import SendUpdate, process_json
from ..vexutils.chat import inline_hum_list


class StatusSetCom(MixinMeta):
    @commands.guild_only()  # type:ignore
    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(cls=DynamicHelpGroup)
    async def statusset(self, ctx: commands.Context):
        """
        Get automatic status updates in a channel, eg Discord.

        Get started with `[p]statusset preview` to see what they look like,
        then `[p]statusset add` to set up automatic updates.
        """

    @statusset.command(name="add", usage="<service> [channel]", cls=DynamicHelp)
    async def statusset_add(
        self,
        ctx: commands.Context,
        service: ServiceConverter,
        chan: Optional[Union[discord.TextChannel, discord.Thread]],
    ):
        """
        Start getting status updates for the chosen service!

        There is a list of services you can use in the `[p]statusset list` command.

        This is an interactive command. It will ask what mode you want to use and if you
        want to use a webhook. You can use the `[p]statusset preview` command to see how
        different options look or take a look at
        https://go.vexcodes.com/c/statusref

        If you don't specify a specific channel, I will use the current channel.
        """
        # guild check on group
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.me, Member)
            assert isinstance(ctx.author, Member)
            assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))

        channel = chan or ctx.channel

        if not channel.permissions_for(ctx.me).send_messages:
            return await ctx.send(
                f"I don't have permissions to send messages in {channel.mention}"
            )

        existing_feeds = await self.config.channel(channel).feeds()
        if service in existing_feeds.keys():
            return await ctx.send(
                f"{channel.mention} already receives {service.friendly} status "
                f"updates. You can edit it with `{ctx.clean_prefix}statusset edit`."
            )

        view = AddServiceView(ctx.author)
        embed = discord.Embed(title="Options")
        embed.set_footer(text="If you don't see the options bellow, update your client.")
        embed.add_field(
            name="Mode",
            value=(
                "**All**: Every time the service posts an update on an incident, I will send a new"
                " message containing the previous updates as well as the new update. Best used in"
                " a fast-moving channel with other users.\n**Latest**: Every time the service"
                " posts an update on an incident, I will send a new message containing only the"
                " latest update. Best used in a dedicated status channel.\n**Edit**: When a new"
                " incident is created, I will sent a new message. When this incident is updated, I"
                " will then add the update to the original message. Best used in a dedicated"
                " status channel."
            ),
            inline=False,
        )
        embed.add_field(
            name="Webhook",
            value=(
                "If you choose yes, status updates will be sent by a webhook with"
                f" {service.friendly}'s logo and with the name if `{service.friendly} Status"
                " Update`, instead of my avatar and name."
            ),
            inline=False,
        )
        embed.add_field(
            name="Restrict",
            value=(
                f"Restrict access to {service.friendly} in the"
                f" `{ctx.clean_prefix}status` command. If there's an incident, members will"
                f" instead be redirected to {channel.mention} and any other channels that you've"
                f" set to receive {service.friendly} status updates which have restrict enabled."
            ),
            inline=False,
        )

        await ctx.send(embed=embed, view=view)
        timeout = await view.wait()

        if timeout:
            return

        if view.webhook:
            webhook_channel = channel.parent if isinstance(channel, discord.Thread) else channel
            if webhook_channel is None:  # Thread.parent can be None
                return await ctx.send("I can't create a webhook in this thread.")
            existing_webhook = any(
                hook.name == ctx.me.name for hook in await webhook_channel.webhooks()
            )
            if not existing_webhook:
                await webhook_channel.create_webhook(
                    name=ctx.me.name, reason="Created for status updates."
                )

        if view.restrict:
            async with self.config.guild(ctx.guild).service_restrictions() as sr:
                try:
                    sr[service.name].append(channel.id)
                except KeyError:
                    sr[service.name] = [channel.id]

            self.service_restrictions_cache.add_restriction(ctx.guild.id, service.name, channel.id)

        if service.name not in self.used_feeds.get_list():
            # need to get it up to date so no mass sending on add
            async with ctx.typing():
                await self.get_initial_data(service.name)

        settings = {"mode": view.mode, "webhook": view.webhook, "edit_id": {}}
        await self.config.channel(channel).feeds.set_raw(  # type:ignore
            service.name, value=settings
        )
        self.used_feeds.add_feed(service.name)

        if service in SPECIAL_INFO.keys():
            msg = f"NOTE: {SPECIAL_INFO[service.name]}\n"
        else:
            msg = ""

        await ctx.send(
            f"{msg}Done, {channel.mention} will now receive {service.friendly} status updates."
        )

    @statusset.command(name="remove", aliases=["del", "delete"], usage="<service> [channel]")
    async def statusset_remove(
        self,
        ctx: commands.Context,
        service: ServiceConverter,
        chan: Optional[Union[discord.TextChannel, discord.Thread]] = None,
    ):
        """
        Stop status updates for a specific service in this server.

        If you don't specify a channel, I will use the current channel.

        **Examples:**
        - `[p]statusset remove discord #testing`
        - `[p]statusset remove discord` (for using current channel)
        """
        # guild check on group
        if TYPE_CHECKING:
            assert isinstance(ctx.channel, (GuildChannel, discord.Thread))
            assert ctx.guild is not None

        channel = chan or ctx.channel

        async with self.config.channel(channel).feeds() as feeds:
            if not feeds.pop(service.name, None):
                return await ctx.send(
                    f"It looks like I don't send {service.friendly} updates in {channel.mention}."
                )

        self.used_feeds.remove_feed(service.name)

        sr: dict[str, list[int]]
        async with self.config.guild(ctx.guild).service_restrictions() as sr:
            try:
                sr[service.name].remove(channel.id)
            except (ValueError, KeyError):
                pass

            self.service_restrictions_cache.remove_restriction(
                channel.id, service.name, channel.id
            )

        await ctx.send(f"Removed {service.friendly} status updated from {channel.mention}")

    @statusset.command(name="list", aliases=["show", "settings"])
    async def statusset_list(self, ctx: commands.Context, service: Optional[ServiceConverter]):
        """
        List that available services and ones are used in this server.

        Optionally add a service at the end of the command to view detailed settings for that
        service.

        **Examples:**
        - `[p]statusset list discord`
        - `[p]statusset list`
        """
        # this needs refactoring
        # i basically copied and pasted in rewrite
        # maybe stick the two sections in .utils
        # TODO: rewrite ^

        # guild check on group
        if TYPE_CHECKING:
            assert ctx.guild is not None

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
                    restrict = channel.id in restrictions.get(service, [])
                    data.append([f"#{channel.name}", mode, webhook, restrict])

            table = box(
                tabulate(data, headers=["Channel", "Send mode", "Use webhooks", "Restrict"])
            )
            await ctx.send(
                f"**Settings for {service.name}**: {table}\n`Restrict` is whether or not to "
                f"restrict access for {service.name} server-wide in the `status` command. Members "
                "are redirected to an appropriate channel."
            )

        else:
            guild_feeds: dict[SERVICE_LITERAL, list[str]] = {}
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
                    msg += box(
                        tabulate(data, tablefmt="plain"), lang="arduino"
                    )  # cspell:disable-line
            if unused_feeds:
                msg += "**Other available services:** "
                msg += inline_hum_list(unused_feeds)
            msg += (
                f"\nTo see settings for a specific service, run `{ctx.clean_prefix}statusset "
                "list <service>`"
            )
            await ctx.send(msg)

    @statusset.command(name="preview")
    async def statusset_preview(
        self, ctx: commands.Context, service: ServiceConverter, mode: ModeConverter, webhook: bool
    ):
        """
        Preview what status updates will look like.

        You can also see this at https://go.vexcodes.com/c/statusref

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

        **Examples:**
        - `[p]statusset preview discord all true`
        - `[p]statusset preview discord latest false`
        """
        # guild check on group
        if TYPE_CHECKING:
            assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
            assert isinstance(ctx.me, Member)

        if webhook and not ctx.channel.permissions_for(ctx.me).manage_messages:
            return await ctx.send("I don't have permission to manage webhook.")

        incidentdata, extra_info = await self.config_wrapper.get_latest(service.name)

        if (
            incidentdata is None
            or extra_info is None
            or (time() - extra_info.get("checked", 0) > 300)  # its older than 3 mins
        ):
            try:
                json_resp, etag, status = await self.statusapi.incidents(service.id)
            except Exception:
                return await ctx.send("Hmm, I couldn't preview that.")
            if status != 200:
                return await ctx.send("Hmm, I couldn't preview that.")
            incidentdata_list = process_json(json_resp, "incidents")
            await self.config_wrapper.update_incidents(service.name, incidentdata_list[0])
            incidentdata = incidentdata_list[0]

        update = Update(incidentdata, [incidentdata.fields[-1]])

        await SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            False,
            True,
        ).send({ctx.channel.id: {"mode": mode, "webhook": webhook, "edit_id": {}}})

    @statusset.command(name="clear", aliases=["erase"], usage="[channel]")
    async def statusset_clear(
        self, ctx: commands.Context, *, chan: Optional[Union[discord.TextChannel, discord.Thread]]
    ):
        """
        Remove all feeds from a channel.

        If you don't specify a channel, I will use the current channel

        **Examples:**
        - `[p]statusset clear #testing`
        - `[p]statusset clear` (for using current channel)
        """
        # guild check on group
        if TYPE_CHECKING:
            assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
            assert ctx.guild is not None

        channel = chan or ctx.channel

        feeds = await self.config.channel(channel).feeds()
        if not feeds:
            return await ctx.send(f"It looks like I don't send any updates in {channel.mention}.")
        for feed in feeds.keys():  # First removing all feeds from cache, feed will be the name
            self.used_feeds.remove_feed(feed)
            self.service_restrictions_cache.remove_restriction(ctx.guild.id, feed, channel.id)
        await self.config.channel(channel).clear()
        await ctx.send(f"Done, I have removed {len(feeds)} feeds from {channel.mention}")

    # ########################################### EDIT ############################################

    @statusset.group()
    async def edit(self, ctx: commands.Context):
        """Edit services you've already set up."""

    @edit.command(name="mode", usage="[channel] <service> <mode>")
    async def edit_mode(
        self,
        ctx: commands.Context,
        chan: Optional[Union[discord.TextChannel, discord.Thread]],
        service: ServiceConverter,
        mode: ModeConverter,
    ):
        """Change what mode to use for status updates.

        **All**: Every time the service posts an update on an incident, I will send a new message
        containing the previous updates as well as the new update. Best used in a fast-moving
        channel with other users.

        **Latest**: Every time the service posts an update on an incident, I will send a new
        message containing only the latest update. Best used in a dedicated status channel.

        **Edit**: When a new incident is created, I will sent a new message. When this incident is
        updated, I will then add the update to the original message. Best used in a dedicated
        status channel.

        If you don't specify a channel, I will use the current channel.

        **Examples:**
        - `[p]statusset edit mode #testing discord latest`
        - `[p]statusset edit mode discord edit` (for current channel)
        """
        # guild check on group
        if TYPE_CHECKING:
            assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))

        channel = chan or ctx.channel

        old_conf = await self.config.channel(channel).feeds()
        if service.name not in old_conf.keys():
            return await ctx.send(
                f"It looks like I don't send {service.friendly} status updates to "
                f"{channel.mention}"
            )

        if old_conf[service.name]["mode"] == mode:
            return await ctx.send(
                f"It looks like I already use that mode for {service.friendly} updates in "
                f"{channel.mention}"
            )

        old_conf[service.name]["mode"] = mode
        await self.config.channel(channel).feeds.set_raw(  # type:ignore
            service.name, value=old_conf[service.name]
        )

        await ctx.send(
            f"{service.friendly} status updates in {channel.mention} will now use the {mode} mode."
        )

    @edit.command(name="webhook", usage="[channel] <service> <webhook>")
    async def edit_webhook(
        self,
        ctx: commands.Context,
        chan: Optional[Union[discord.TextChannel, discord.Thread]],
        service: ServiceConverter,
        webhook: bool,
    ):
        """Set whether or not to use webhooks for status updates.

        Using a webhook means that the status updates will be sent with the avatar as the service's
        logo and the name will be `[service] Status Update`, instead of my avatar and name.

        If you don't specify a channel, I will use the current channel.

        **Examples:**
        - `[p]statusset edit webhook #testing discord true`
        - `[p]statusset edit webhook discord false` (for current channel)
        """
        # guild check on group
        if TYPE_CHECKING:
            assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
            assert isinstance(ctx.me, Member)

        channel = chan or ctx.channel

        old_conf = await self.config.channel(channel).feeds()
        if service.name not in old_conf.keys():
            return await ctx.send(
                f"It looks like I don't send {service.friendly} status updates to "
                f"{channel.mention}"
            )

        if service.name == "discord":
            return await ctx.send(
                'Discord does not allow webhook names to contain "Discord" to prevent '
                "impersonation and potential scams. Therefore, webhooks are unavailable for "
                "Discord status updates."
            )

        if old_conf[service.name]["webhook"] == webhook:
            word = "use" if webhook else "don't use"
            return await ctx.send(
                f"It looks like I already {word} webhooks for {service.friendly} status updates "
                f"in {channel.mention}"
            )

        if webhook and not channel.permissions_for(ctx.me).manage_webhooks:
            return await ctx.send("I don't have manage webhook permissions so I can't do that.")

        old_conf[service.name]["edit_id"] = {}
        old_conf[service.name]["webhook"] = webhook
        await self.config.channel(channel).feeds.set_raw(  # type:ignore
            service.name, value=old_conf[service.name]
        )

        word = "use" if webhook else "not use"
        await ctx.send(
            f"{service.friendly} status updates in {channel.mention} will now {word} webhooks."
        )

    @edit.command(name="restrict", usage="[channel] <service> <restrict>")
    async def edit_restrict(
        self,
        ctx: commands.Context,
        chan: Optional[Union[discord.TextChannel, discord.Thread]],
        service: ServiceConverter,
        restrict: bool,
    ):
        """
        Restrict access to the service in the `status` command.

        Enabling this will reduce spam. Instead of sending the whole update
        (if there's an incident) members will instead be redirected to channels
        that automatically receive the status updates, that they have permission to to view.

        **Examples:**
        - `[p]statusset edit restrict #testing discord true`
        - `[p]statusset edit restrict discord false` (for current channel)
        """
        # guild check on group
        if TYPE_CHECKING:
            assert isinstance(ctx.channel, (discord.TextChannel, discord.Thread))
            assert ctx.guild is not None

        channel = chan or ctx.channel

        feed_settings = await self.config.channel(channel).feeds()
        if service.name not in feed_settings.keys():
            return await ctx.send(
                f"It looks like I don't send {service.friendly} status updates to "
                f"{channel.mention}"
            )

        old_conf = (await self.config.guild(ctx.guild).service_restrictions()).get(
            service.name, []
        )
        old_bool = channel.id in old_conf
        if old_bool == restrict:
            word = "" if restrict else "don't "
            return await ctx.send(
                f"It looks like I already {word}restrict {service.friendly} status updates for "
                "the `status` command."
            )

        sr: dict[SERVICE_LITERAL, list[int]]
        async with self.config.guild(ctx.guild).service_restrictions() as sr:
            if restrict:
                try:
                    sr[service.name].append(channel.id)
                except KeyError:
                    sr[service.name] = [channel.id]
                self.service_restrictions_cache.add_restriction(
                    ctx.guild.id, service.name, channel.id
                )
            else:
                sr[service.name].remove(channel.id)
                self.service_restrictions_cache.remove_restriction(
                    ctx.guild.id, service.name, channel.id
                )

        word = "" if restrict else "not "
        await ctx.send(f"{service.friendly} will now {word}be restricted in the `status` command.")
