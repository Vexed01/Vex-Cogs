from concurrent.futures.thread import ThreadPoolExecutor
from typing import Optional

import discord
from aiohttp.client import ClientSession
from redbot.core import commands

from .abc import CompositeMetaClass
from .data import CovidData
from .errors import CovidError
from .plot import GraphPlot
from .vexutils.meta import format_help, format_info


class CovidGraph(commands.Cog, GraphPlot, CovidData, metaclass=CompositeMetaClass):
    """
    Get COVID-19 graphs.
    """

    __version__ = "1.2.0"
    __author__ = "Vexed#0714"

    def __init__(self, bot):
        self.bot = bot
        self.executor = ThreadPoolExecutor(16, thread_name_prefix="covidgraph")
        self.session = ClientSession()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    async def cog_unload(self) -> None:
        self.executor.shutdown(wait=False)

    @commands.command(hidden=True)
    async def covidgraphinfo(self, ctx: commands.Context):
        await ctx.send(await (format_info(ctx, self.qualified_name, self.__version__)))

    @commands.cooldown(2, 10, commands.BucketType.user)  # 2 per 10 seconds
    @commands.group()
    async def covidgraph(self, ctx: commands.Context):
        """Get graphs of COVID-19 data."""

    @covidgraph.command(aliases=["c"], usage="[days] <country>")
    async def cases(self, ctx: commands.Context, days: Optional[int], *, country: str):
        """
        Get the number of confirmed cases in a country.

        You can optionally specify the number of days to get data for,
        otherwise it will be all-time.

        `country` can also be `world` to get the worldwide data.

        **Examples:**
            - `[p]covidgraph cases US` - All time data for the US
            - `[p]covidgraph cases 7 US` - Last 7 days for the US
            - `[p]covidgraph cases world` - Worldwide data
        """
        if days and days < 7:
            await ctx.send("`days` must be at least 7.")
            return

        async with ctx.typing():
            try:
                country, ts = await self.get_cases(country, days)
            except CovidError:
                await ctx.send("Something went wrong. It's probably an invalid country.")
                return

            file = await self.plot_graph(ts, "Daily cases")

        embed = discord.Embed(
            title=f"Daily COVID-19 cases - {country}",
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(text="Times are in UTC\nData from disease.sh and John Hopkins University")
        embed.set_image(url="attachment://plot.png")
        await ctx.send(file=file, embed=embed)

    @covidgraph.command(aliases=["d"], usage="[days] <country>")
    async def deaths(self, ctx: commands.Context, days: Optional[int], *, country: str):
        """
        Get the number of deaths in a country.

        You can optionally specify the number of days to get data for,
        otherwise it will be all-time.

        `country` can also be `world` to get the worldwide data.

        **Examples:**
            - `[p]covidgraph deaths US` - All time data for the US
            - `[p]covidgraph deaths 7 US` - Last 7 days for the US
            - `[p]covidgraph deaths world` - Worldwide data
        """
        if days and days < 7:
            await ctx.send("`days` must be at least 7.")
            return

        async with ctx.typing():
            try:
                country, ts = await self.get_deaths(country, days)
            except CovidError:
                await ctx.send("Something went wrong. It's probably an invalid country.")
                return

            file = await self.plot_graph(ts, "Daily deaths")

        embed = discord.Embed(
            title=f"Daily COVID-19 deaths - {country}",
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(text="Times are in UTC\nData from disease.sh and John Hopkins University")
        embed.set_image(url="attachment://plot.png")
        await ctx.send(file=file, embed=embed)

    @covidgraph.command(aliases=["v"], usage="[days] <country>")
    async def vaccines(self, ctx: commands.Context, days: Optional[int], *, country: str):
        """
        Get the number of vaccine doses administered in a country.

        You can optionally specify the number of days to get data for,
        otherwise it will be all-time.

        `country` can also be `world` to get the worldwide data.

        **Examples:**
            - `[p]covidgraph vaccines US` - All time data for the US
            - `[p]covidgraph vaccines 7 US` - Last 7 days for the US
            - `[p]covidgraph vaccines world` - Worldwide data
        """
        if days and days < 7:
            await ctx.send("`days` must be at least 7.")
            return

        async with ctx.typing():
            try:
                country, ts = await self.get_vaccines(country, days)
            except CovidError:
                await ctx.send("Something went wrong. It's probably an invalid country.")
                return

            file = await self.plot_graph(ts, "Total vaccine doses")

        embed = discord.Embed(
            title=f"Total COVID-19 vaccine doses - {country}",
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(text="Times are in UTC\nData from disease.sh and Our World in Data")
        embed.set_image(url="attachment://plot.png")
        await ctx.send(file=file, embed=embed)
