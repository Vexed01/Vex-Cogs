import datetime
import json
import logging
from io import StringIO
from time import monotonic
from typing import Optional

import discord
import pandas as pd
from discord.ext.commands.cooldowns import BucketType
from redbot.core import commands
from redbot.core.commands.converter import TimedeltaConverter
from redbot.core.utils.chat_formatting import box, humanize_timedelta

from channeltrack.table import TableType

from .abc import MixinMeta

log = logging.getLogger("red.vex.channeltrack.coms")

DEFAULT_DELTA = datetime.timedelta(days=1)
MAX_POINTS = 25_000


class ChannelTrackCommands(MixinMeta):
    async def gen_and_send_graph(
        self,
        ctx: commands.Context,
        df: pd.DataFrame,
        title: str,
        delta: datetime.timedelta,
        *,
        ylabel: Optional[str] = None,
        more_options: bool = False,
    ):
        comstart = monotonic()

        if ylabel is None:
            ylabel = title

        if len(df) < 2:
            return await ctx.send(
                "I need a little longer to collect data for the graph. Try again in a few minutes."
            )

        df = df.fillna(0)

        now = datetime.datetime.utcnow().replace(microsecond=0, second=0)
        start = now - delta
        start = max(start, df.first_valid_index())

        delta_max_points = (now - df.first_valid_index()).total_seconds() / 600

        if delta_max_points > 1440 and MAX_POINTS != -1:  # 1 day
            frequency = int(delta_max_points // MAX_POINTS)
            if frequency < 1:
                frequency = 1
        else:
            frequency = 1

        expected_index = pd.date_range(start=start, end=now, freq=f"{frequency}min")
        df = df.reindex(index=expected_index)

        total_before_avg = df.sum().values[0]

        df = df.rolling(3, min_periods=1).mean()

        async with ctx.typing():
            graph = await self.plot(df, ylabel)

        if delta == datetime.timedelta(days=9000):  # "all" was entered and was replaced with 9k
            str_delta = " all time"
        else:
            str_delta = " for the last " + humanize_timedelta(timedelta=delta)

        embed = discord.Embed(
            title=title + str_delta + " (30 min averages)",
            colour=await ctx.embed_colour(),
        )

        if len(df.columns) == 1:
            embed.add_field(name="Min", value=df.min().values[0])
            embed.add_field(name="Max", value=df.max().values[0])
            embed.add_field(name="Average", value=round(df.mean().values[0], 2))
            if more_options:
                embed.add_field(name="Total", value=total_before_avg)

        if more_options:
            embed.description = (
                "You can choose to only display certian channels with "
                f"`{ctx.clean_prefix}channeltrack {ctx.command.name} <channels...>`, see "
                f"`{ctx.clean_prefix}help channeltrack {ctx.command.name}` for details."
            )

        embed.set_footer(text="Times are in UTC")
        embed.set_image(url="attachment://plot.png")

        msg = await ctx.send(file=graph, embed=embed)

        end = monotonic()
        debug_info = {
            "plot_msg": msg.id,  # message id of sent plot
            "alldatapoints": len(df),  # datapoints in the all-time dataframe
            "possible_points": delta_max_points,  # the amount points in the data if 100% uptime
            "points_plotted": len(df),  # valid datapoints in the delta dataframe
            "wanted_frequency": frequency,  # wanted frequency of the plot
            "comtime": end - comstart,  # time taken to plot the graph
        }

        log.debug(f"Plot finished, info: {debug_info}")
        self.last_plot_debug = debug_info

    @commands.cooldown(10, 60.0, BucketType.user)
    @commands.group()
    async def channeltrack(self, ctx: commands.Context):
        """View my stats."""

    @commands.is_owner()
    @channeltrack.command(hidden=True)
    async def devimport(self, ctx: commands.Context, table: str):
        """
        Import data from a JSON string, orient "split".

        This is for development purposes only.

        Please attack a `.json` file.
        """
        async with ctx.typing():
            self.loop.cancel()
            old_df = await self.driver.read(table)
            df = old_df.append(
                pd.read_json(await ctx.message.attachments[0].read(), orient="split")
            )
            await self.driver.write(df, table)
        await ctx.send("Done. Please reload the cog.")

    @commands.is_owner()
    @channeltrack.command(hidden=True)
    async def debug(self, ctx: commands.Context):
        """
        View debug info for the last plot.

        This is for development purposes only.
        """
        if self.last_plot_debug is None:
            await ctx.send("No plot has been made yet.")
        await ctx.send(box(json.dumps(self.last_plot_debug, indent=4), "json"))

    @commands.is_owner()
    @channeltrack.group()
    async def export(self, ctx: commands.Context):
        """Export channeltrack data."""

    @export.command(name="json")
    async def export_json(self, ctx: commands.Context, timeframe: TimedeltaConverter):
        """Export as JSON with pandas orient "split" """
        async with ctx.typing():
            files = []
            for type in (TableType.MESSAGES, TableType.COMMANDS):
                df = await self.driver.read(self.get_table_name(type, ctx.guild.id))
                df = df.loc[df.index > (datetime.datetime.utcnow() - timeframe)]
                fp = StringIO()
                fp.write(df.to_json(na_rep=0, orient="split"))
                size = fp.tell()
                if ctx.guild:
                    max_size = ctx.guild.filesize_limit  # type:ignore
                else:
                    max_size = 8388608
                if size > max_size:
                    await ctx.send(
                        "Sorry, this file is too big to send here. Try a shorter timeframe."
                    )
                    return
                fp.seek(0)

                files.append(
                    discord.File(
                        fp,
                        f"{'cmd' if type == TableType.MESSAGES else 'msg'}_"
                        f"{str(ctx.guild.id)}.json",
                    )
                )
            await ctx.send("Here is your file.", files=files)

    @export.command(name="csv")
    async def export_csv(self, ctx: commands.Context, timeframe: TimedeltaConverter):
        """Export as CSV"""
        async with ctx.typing():
            files = []
            for type in (TableType.MESSAGES, TableType.COMMANDS):
                df = await self.driver.read(self.get_table_name(type, ctx.guild.id))
                df = df.loc[df.index > (datetime.datetime.utcnow() - timeframe)]
                fp = StringIO()
                fp.write(df.to_csv(na_rep=0))
                size = fp.tell()
                if ctx.guild:
                    max_size = ctx.guild.filesize_limit  # type:ignore
                else:
                    max_size = 8388608
                if size > max_size:
                    await ctx.send(
                        "Sorry, this file is too big to send here. Try a shorter timeframe."
                    )
                    return
                fp.seek(0)

                files.append(
                    discord.File(
                        fp,
                        f"{'cmd' if type == TableType.MESSAGES else 'msg'}_"
                        f"{str(ctx.guild.id)}.json",
                    )
                )
            await ctx.send("Here is your file.", files=files)

    @channeltrack.command(aliases=["msgraph"])
    async def msggraph(
        self,
        ctx: commands.Context,
        timeframe: TimedeltaConverter = DEFAULT_DELTA,
        *channels: discord.TextChannel,
    ):
        """
        View a graph of messages per channel.

        The graph will show the amount of messages over time.
        """
        df = await self.driver.read(self.get_table_name(TableType.MESSAGES, ctx.guild.id))
        if channels:
            chan_ids = [c.id for c in channels]
            df = df.loc[chan_ids]

        await self.gen_and_send_graph(
            ctx, df, "Command usage", timeframe, more_options=not bool(channels)
        )
