import asyncio
import logging
from typing import TYPE_CHECKING

import discord
from discord.ext.commands.errors import CheckFailure
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, pagify, warning
from redbot.core.utils.menus import start_adding_reactions

from ..commands.converters import ModeConverter, ServiceConverter
from ..core.abc import MixinMeta
from ..objects import SendCache, Update
from ..updateloop import SendUpdate, process_json

if discord.__version__.startswith("1"):
    from redbot.core.utils.predicates import ReactionPredicate
else:
    from ..vexutils.button_pred import wait_for_yes_no

_log = logging.getLogger("red.vex.status.dev")


class StatusDevCom(MixinMeta):
    @commands.guild_only()  # type:ignore
    @commands.is_owner()
    @commands.group(hidden=True)
    async def statusdev(self, ctx: commands.Context):
        """Don't use this; hidden for a reason; stuff _might_ break."""

    async def unsupported(self, ctx: commands.Context) -> None:
        if ctx.author.id == 418078199982063626:  # vexed (my) id
            return

        msg = warning(
            "\nTHIS COMMAND IS INTENDED FOR DEVELOPMENT PURPOSES ONLY.\n\nUnintended "
            "things can happen.\n\nRepeat: THIS COMMAND IS NOT SUPPORTED.\nAre you sure "
            "you want to continue?"
        )
        try:
            if discord.__version__.startwith("1"):
                m = await ctx.send(msg)
                start_adding_reactions(m, ReactionPredicate.YES_OR_NO_EMOJIS)
                pred = ReactionPredicate.yes_or_no(m, ctx.author)  # type:ignore
                await ctx.bot.wait_for("reaction_add", check=pred, timeout=15)
                result = pred.result
            else:
                result = await wait_for_yes_no(ctx, msg, timeout=15)
        except asyncio.TimeoutError:
            await ctx.send("Timeout, aborting.")
            raise CheckFailure("Reactions timed out")
        if result is not True:
            await ctx.send("Aborting.")
            raise CheckFailure("User choose no.")

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["cf"], hidden=True)
    async def checkfeed(
        self,
        ctx: commands.Context,
        service: ServiceConverter,
        mode: ModeConverter = "all",
        webhook: bool = False,
    ):
        """Check the current status of a feed in the current channel"""
        json_resp, etag, status = await self.statusapi.incidents(service.id)
        incidentdata = process_json(json_resp, "incidents")[0]

        update = Update(incidentdata, [incidentdata.fields[-1]])
        await SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            True,
            True,
        ).send({ctx.channel.id: {"mode": mode, "webhook": webhook, "edit_id": {}}})

        json_resp, _, _ = await self.statusapi.scheduled_maintenance(service.id)
        incidentdata_list = process_json(
            json_resp, "scheduled"
        )  # some have no scheduled maintenance
        if incidentdata_list:
            incidentdata = incidentdata_list[0]
        else:
            return
        update = Update(incidentdata, [incidentdata.fields[-1]])
        await SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            True,
            True,
        ).send({ctx.channel.id: {"mode": mode, "webhook": webhook, "edit_id": {}}})

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["cid"], hidden=True)
    async def checkid(self, ctx: commands.Context, service: ServiceConverter, id: str):
        inc, _, _ = await self.statusapi.incidents(service.id)
        maint, _, _ = await self.statusapi.scheduled_maintenance(service.id)

        data_list = process_json(inc, "incidents")
        data_list.extend(process_json(maint, "scheduled"))

        incidentdata_list = [i for i in data_list if i.incident_id == id]
        if not incidentdata_list:
            return await ctx.send("Cant find that.")

        update = Update(incidentdata_list[0], [incidentdata_list[0].fields[-1]])
        await SendUpdate(
            self.bot,
            self.config_wrapper,
            update,
            service.name,
            SendCache(update, service.name),
            True,
            True,
        ).send({ctx.channel.id: {"mode": "all", "webhook": False, "edit_id": {}}})

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["cfr"], hidden=True)
    async def checkfeedraw(self, ctx: commands.Context, service: ServiceConverter):
        """Get raw JSON data"""
        resp, etag, status = await self.statusapi.incidents(service.id)

        await ctx.send(f"Status: `{status}`\nETag: `{etag}`\nResponse:")
        await ctx.send_interactive(pagify(str(resp)), box_lang="")

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["fs"], hidden=True)
    async def forcestatus(self, ctx: commands.Context, service: ServiceConverter):
        """Simulate latest incident. SENDS TO ALL CHANNELS IN ALL REGISTERED GUILDS."""
        json_resp, etag, status = await self.statusapi.incidents(service.id)
        incidentdata = process_json(json_resp, "incidents")[0]

        update = Update(incidentdata, [incidentdata.fields[-1]])

        channels = await self.config_wrapper.get_channels(service.name)
        sendcache = SendCache(update, service.name)

        await SendUpdate(
            bot=self.bot,
            config_wrapper=self.config_wrapper,
            update=update,
            service=service.name,
            sendcache=sendcache,
            dispatch=True,
            force=True,
        ).send(channels)

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["cd"], hidden=True)
    async def cooldown(self, ctx: commands.Context, user_id: int = None):
        """Get custom cooldown info for a user"""
        await ctx.send(box(str(self.service_cooldown.get_from_id(user_id or ctx.author.id))))

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["cfc"], hidden=True)
    async def checkusedfeedcache(self, ctx: commands.Context):
        """Check what feeds this is checking"""
        raw = box(str(self.used_feeds), lang="py")
        actual = box(str(self.used_feeds.get_list()), lang="py")
        await ctx.send(f"**Raw data:**\n{raw}\n**Active:**\n{actual}")

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["cgr"], hidden=True)
    async def checkguildrestrictions(self, ctx: commands.Context):
        """Check guild restrictins for current guild"""
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None

        await ctx.send(box(str(self.service_restrictions_cache.get_guild(ctx.guild.id))))

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["ri"], hidden=True)
    async def refreshincidentids(self, ctx: commands.Context):
        """Regenerate the cache of past incident IDs."""
        await ctx.send("Starting.")
        await self.get_initial_data()
        await ctx.send("Done.")

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["l"], hidden=True)
    async def loopstatus(self, ctx: commands.Context):
        """Check status of the loop"""
        embed = self.loop_meta.get_debug_embed()
        await ctx.send(embed=embed)

    @commands.before_invoke(unsupported)  # type:ignore
    @statusdev.command(aliases=["dev"], hidden=True)
    async def devenvvars(self, ctx: commands.Context):
        """
        Add some dev env vars

        Adds `status`, `loop`, `statusapi`, `sendupdate`.

        These will be removed on cog unload.
        """
        try:
            self.bot.add_dev_env_value("status", lambda _: self)
            self.bot.add_dev_env_value("statusapi", lambda _: self.statusapi)
            self.bot.add_dev_env_value("sendupdate", lambda _: SendUpdate)
            await ctx.send(
                "Added dev env vars `status`, `statusapi`, `sendupdate`. They will be "
                "removed on cog unload."
            )
        except Exception:
            _log.exception("Unable to add dev env vars.")
            await ctx.send("I was unable to add them. Check the logs.")
