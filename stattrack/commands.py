import datetime
from io import StringIO
from typing import Iterable, Optional, Union

import discord
from discord.ext.commands.cooldowns import BucketType
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, humanize_timedelta

from stattrack.abc import MixinMeta
from stattrack.converters import (
    ChannelGraphConverter,
    StatusGraphConverter,
    TimespanConverter,
    UserGraphConverter,
)

DEFAULT_DELTA = datetime.timedelta(days=1)


class StatTrackCommands(MixinMeta):
    async def all_in_one(
        self,
        ctx: commands.Context,
        delta: datetime.timedelta,
        label: Union[str, Iterable[str]],
        title: str,
        ylabel: Optional[str] = None,
        *,
        more_options: bool = False,
    ):
        if self.df_cache is None:
            return await ctx.send("This command isn't ready yet. Try again in a few seconds.")
        await ctx.trigger_typing()  # wont be that long
        if ylabel is None:
            ylabel = title
        df = self.df_cache[label]
        if len(df) < 2:
            return await ctx.send("I need a little longer to collect data. Try again in a minute.")

        graph = await self.plot(df, delta, ylabel)

        if delta == datetime.timedelta(days=9000):  # "all" was entered and was replaced with 9k
            str_delta = " all time"
        else:
            str_delta = " for the last " + humanize_timedelta(timedelta=delta)

        embed = discord.Embed(
            title=title + str_delta,
            colour=await ctx.embed_colour(),
        )
        if more_options:
            embed.description = (
                "You can choose to only display certian metrics with "
                f"`{ctx.clean_prefix}stattrack {ctx.command.name} <metrics>`, see "
                f"`{ctx.clean_prefix}help stattrack {ctx.command.name}` for details."
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

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack latency 3w2d`
            - `[p]stattrack latency 5d`
            - `[p]stattrack latency all`
        """
        await self.all_in_one(ctx, timespan, "ping", "Latency", "Latency (ms)")

    @stattrack.command(aliases=["time", "loop"])
    async def looptime(self, ctx: commands.Context, timespan: TimespanConverter = DEFAULT_DELTA):
        """
        Get my loop time stats.

        **Arguments**

        `<timespan>` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        **Examples:**
            - `[p]stattrack looptime 3w2d`
            - `[p]stattrack looptime 5d`
            - `[p]stattrack looptime all`
        """
        await self.all_in_one(ctx, timespan, "loop_time_s", "Loop time", "Loop time (seconds)")

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

    @stattrack.command(usage="[timespan=1d] [metrics]")
    async def status(
        self,
        ctx: commands.Context,
        timespan: Optional[TimespanConverter] = DEFAULT_DELTA,
        *metrics: StatusGraphConverter,
    ):
        """
        Get status stats.

        You can just run this command on its own to see all metrics,
        or specify some metrics - see below.

        **Arguments**

        `[timespan]` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        `[metrics]` The metrics to show. Valid options: `online`, `idle`, `offline`, `dnd`.
        Defaults to all of them.

        **Examples:**
            - `[p]stattrack status` - show all metrics, 1 day
            - `[p]stattrack status 3w2d` - show all metrics, 3 weeks 2 days
            - `[p]stattrack status 5d dnd online` - show dnd & online, 5 days
            - `[p]stattrack status all online idle` - show online & idle, all time
        """
        if timespan is None:
            timespan = DEFAULT_DELTA

        if not metrics:
            metrics = ("online", "idle", "offline", "dnd")

        await self.all_in_one(
            ctx, timespan, ["status_" + g for g in metrics], "User status", more_options=True
        )

    @stattrack.command(usage="[timespan=1d] [metrics]")
    async def users(
        self,
        ctx: commands.Context,
        timespan: Optional[TimespanConverter] = DEFAULT_DELTA,
        *metrics: UserGraphConverter,
    ):
        """
        Get user stats.

        You can just run this command on its own to see all metrics,
        or specify some metrics - see below.

        **Arguments**

        `[timespan]` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        `[metrics]` The metrics to show. Valid options: `total`, `unique`, `humans`, `bots`.
        Defaults to all of them.

        Note that `total` will count users multiple times if they share multiple servers with the
        [botname], while `unique` will only count them once.

        **Examples:**
            - `[p]stattrack user` - show all metrics, 1 day
            - `[p]stattrack user 3w2d` - show all metrics, 3 weeks 2 days
            - `[p]stattrack user 5d dnd online` - show dnd & online, 5 days
            - `[p]stattrack user all online idle` - show online & idle, all time
        """
        if timespan is None:
            timespan = DEFAULT_DELTA

        if not metrics:
            metrics = ("total", "unique", "humans", "bots")

        await self.all_in_one(
            ctx, timespan, ["users_" + g for g in metrics], "Users", more_options=True
        )

    @stattrack.command(usage="[timespan=1d] [metrics]")
    async def channels(
        self,
        ctx: commands.Context,
        timespan: Optional[TimespanConverter] = DEFAULT_DELTA,
        *metrics: ChannelGraphConverter,
    ):
        """
        Get channel stats.

        You can just run this command on its own to see all metrics,
        or specify some metrics - see below.

        **Arguments**

        `[timespan]` How long to look for, or `all` for all-time data. Defaults to 1 day. Must be
        at least 1 hour.

        `[metrics]` The metrics to show.
        Valid options: `total`, `text`, `voice`, `stage`, `category`.
        Defaults to all of them.

        Note that `total` will count users multiple times if they share multiple servers with the
        [botname], while `unique` will only count them once.

        **Examples:**
            - `[p]stattrack channels` - show all metrics, 1 day
            - `[p]stattrack channels 3w2d` - show all metrics, 3 weeks 2 days
            - `[p]stattrack channels 5d dnd online` - show dnd & online, 5 days
            - `[p]stattrack channels all online idle` - show online & idle, all time
        """
        if timespan is None:
            timespan = DEFAULT_DELTA

        if "category" in metrics:
            l_metrics = list(metrics)
            l_metrics.remove("category")
            l_metrics.append("cat")
            metrics = tuple(l_metrics)

        if not metrics:
            metrics = ("total", "text", "voice", "cat", "stage")

        await self.all_in_one(
            ctx, timespan, ["channels_" + g for g in metrics], "Channels", more_options=True
        )

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
