import datetime
from io import StringIO

import discord
from discord.ext.commands.cooldowns import BucketType
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, humanize_timedelta

from stattrack.abc import MixinMeta
from stattrack.converters import TimespanConverter

DEFAULT_DELTA = datetime.timedelta(days=1)


class StatTrackCommands(MixinMeta):
    async def all_in_one(
        self,
        ctx: commands.Context,
        delta: datetime.timedelta,
        label: str,
        title: str,
        ylabel: str = None,
    ):
        if self.df_cache is None:
            return await ctx.send("This command isn't ready yet. Try again in a few seconds.")
        await ctx.trigger_typing()  # wont be that long
        if ylabel is None:
            ylabel = title
        sr = self.df_cache[label]
        if len(sr) < 2:
            return await ctx.send("I need a little longer to collect data. Try again in a minute.")
        graph = await self.plot(sr, delta, ylabel)

        if delta == datetime.timedelta(days=9000):  # "all" was entered and was replaced with 9k
            str_delta = " all time"
        else:
            str_delta = " for the last " + humanize_timedelta(timedelta=delta)

        embed = discord.Embed(
            title=title + str_delta,
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(text="Times are in UTC")
        embed.set_image(url="attachment://plot.png")
        await ctx.send(file=graph, embed=embed)

    @commands.cooldown(10, 60.0, BucketType.user)
    @commands.group()
    async def stattrack(self, ctx: commands.Context):
        """View my stats."""

    @stattrack.command(hidden=True)
    async def raw(self, ctx, var):
        await ctx.send(box(str(self.df_cache[var])))

    @commands.is_owner()
    @stattrack.group()
    async def export(self, ctx: commands.Context):
        """Export stattrack data."""

    @export.command(name="json")
    async def export_json(self, ctx: commands.Context):
        """Export as JSON with pandas orient "split" """
        data = self.df_cache.to_json(orient="split")
        fp = StringIO()
        fp.write(data)
        size = fp.tell()
        if ctx.guild:
            assert isinstance(ctx.guild, discord.Guild)
            max_size = ctx.guild.filesize_limit
        else:
            max_size = 8388608
        if size > max_size:
            await ctx.send(
                "Sorry, this file is too big to send here. Try a server with a higher upload file "
                "size limit."
            )
            return
        fp.seek(0)
        await ctx.send(
            "Here is your file.", file=discord.File(fp, "stattrack.json")  # type:ignore
        )

    @export.command(name="csv")
    async def export_csv(self, ctx: commands.Context):
        """Export as CSV"""
        data = self.df_cache.to_csv()
        fp = StringIO()
        fp.write(data)
        size = fp.tell()
        if ctx.guild:
            assert isinstance(ctx.guild, discord.Guild)
            max_size = ctx.guild.filesize_limit
        else:
            max_size = 8388608
        if size > max_size:
            await ctx.send(
                "Sorry, this file is too big to send here. Try a server with a higher upload file "
                "size limit."
            )
            return
        fp.seek(0)
        await ctx.send("Here is your file.", file=discord.File(fp, "stattrack.csv"))  # type:ignore

    @stattrack.command(aliases=["ping"])
    async def latency(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get my latency stats.

        Get command usage stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack latency 3w2d`
            - `[p]stattrack latency 5d`
            - `[p]stattrack latency all`
        """
        await self.all_in_one(ctx, timespan, "ping", "Latency", "Latency (ms)")

    @stattrack.command(name="commands")
    async def com(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get command usage stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack commands 3w2d`
            - `[p]stattrack commands 5d`
            - `[p]stattrack commands all`
        """
        await self.all_in_one(
            ctx,
            timespan,
            "command_count",
            "Commands per minute",
        )

    @stattrack.command()
    async def messages(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get message stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack messages 3w2d`
            - `[p]stattrack messages 5d`
            - `[p]stattrack messages all`
        """
        await self.all_in_one(ctx, timespan, "message_count", "Messages per minute")

    @stattrack.command(aliases=["guilds"])
    async def servers(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get server stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack servers 3w2d`
            - `[p]stattrack servers 5d`
            - `[p]stattrack servers all`
        """
        await self.all_in_one(ctx, timespan, "guilds", "Server count")

    @stattrack.group(name="status")
    async def group_status(self, ctx: commands.Context):
        """See stats about user's statuses."""

    @group_status.command()
    async def online(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get online stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack status online 3w2d`
            - `[p]stattrack status online 5d`
            - `[p]stattrack status online all`
        """
        await self.all_in_one(ctx, timespan, "status_online", "Users online")

    @group_status.command()
    async def idle(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get idle stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack status idle 3w2d`
            - `[p]stattrack status idle 5d`
            - `[p]stattrack status idle all`
        """
        await self.all_in_one(ctx, timespan, "status_idle", "Users idle")

    @group_status.command()
    async def offline(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get offline stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack status offline 3w2d`
            - `[p]stattrack status offline 5d`
            - `[p]stattrack status offline all`
        """
        await self.all_in_one(ctx, timespan, "status_offline", "Users offline")

    @group_status.command()
    async def dnd(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get dnd stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack status dnd 3w2d`
            - `[p]stattrack status dnd 5d`
            - `[p]stattrack status dnd all`
        """
        await self.all_in_one(ctx, timespan, "status_dnd", "Users dnd")

    @stattrack.group(name="users")
    async def users_group(sef, ctx: commands.Context):
        """See stats about user counts"""

    @users_group.command(name="total")
    async def users_total(
        self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA
    ):
        """
        Get total user stats.

        This includes humans and bots and counts users/bots once per server they share with me.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack users total 3w2d`
            - `[p]stattrack users total 5d`
            - `[p]stattrack users total all`
        """
        await self.all_in_one(ctx, timespan, "users_total", "Total users")

    @users_group.command()
    async def unique(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get total user stats.

        This includes humans and bots and counts them once, reagardless of how many servers they
        share with me.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack users unique 3w2d`
            - `[p]stattrack users unique 5d`
            - `[p]stattrack users unique all`
        """
        await self.all_in_one(ctx, timespan, "users_unique", "Unique users")

    @users_group.command()
    async def humans(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get human user stats.

        This is the count of unique humans. They are counted once, regardless of how many servers
        they share with me.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack users humans 3w2d`
            - `[p]stattrack users humans 5d`
            - `[p]stattrack users humans all`
        """
        await self.all_in_one(ctx, timespan, "users_humans", "Humans")

    @users_group.command()
    async def bots(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get bot user stats.

        This is the count of unique bots. They are counted once, regardless of how many servers
        they share with me.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack users bots 3w2d`
            - `[p]stattrack users bots 5d`
            - `[p]stattrack users bots all`
        """
        await self.all_in_one(ctx, timespan, "users_bots", "Bots")

    @stattrack.group(name="channels")
    async def channels_group(self, ctx: commands.Context):
        """See how many channels there are in all my guilds"""

    @channels_group.command(name="total")
    async def chan_total(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get total channel stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack channels total 3w2d`
            - `[p]stattrack channels total 5d`
            - `[p]stattrack channels total all`
        """
        await self.all_in_one(ctx, timespan, "channels_total", "Total channels")

    @channels_group.command()
    async def text(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get text channel stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack channels text 3w2d`
            - `[p]stattrack channels text 5d`
            - `[p]stattrack channels text all`
        """
        await self.all_in_one(ctx, timespan, "channels_text", "Text channels")

    @channels_group.command()
    async def voice(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get voice channel stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack channels voice 3w2d`
            - `[p]stattrack channels voice 5d`
            - `[p]stattrack channels voice all`
        """
        await self.all_in_one(ctx, timespan, "channels_voice", "Voice channels")

    @channels_group.command()
    async def categories(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get categories stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack channels categories 3w2d`
            - `[p]stattrack channels categories 5d`
            - `[p]stattrack channels categories all`
        """
        await self.all_in_one(ctx, timespan, "channels_cat", "Categories")

    @channels_group.command()
    async def stage(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get stage channel stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack channels stage 3w2d`
            - `[p]stattrack channels stage 5d`
            - `[p]stattrack channels stage all`
        """
        await self.all_in_one(ctx, timespan, "channels_stage", "Stage channels")

    @stattrack.group(aliases=["sys"])
    async def system(self, ctx: commands.Context):
        """Get system metrics."""

    @system.command()
    async def cpu(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get CPU stats.

        **Arguments**

        <timespan> How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack system cpu 3w2d`
            - `[p]stattrack system cpu 5d`
            - `[p]stattrack system cpu all`
        """
        await self.all_in_one(ctx, timespan, "sys_cpu", "CPU Usage", "Percentage CPU Usage")

    @system.command(aliases=["memory", "ram"])
    async def mem(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get memory usage stats.

        **Arguments**

        <timespan> How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack system mem 3w2d`
            - `[p]stattrack system mem 5d`
            - `[p]stattrack system mem all`
        """
        await self.all_in_one(ctx, timespan, "sys_mem", "RAM Usage", "Percentage RAM Usage")
