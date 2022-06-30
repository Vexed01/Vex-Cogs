from typing import Iterable, Optional
from urllib.parse import quote, urlencode

import discord
from pytrends.exceptions import ResponseError
from redbot.core import commands
from redbot.core.utils import deduplicate_iterables

from .abc import CompositeMetaClass
from .consts import GEOS, TIMEFRAMES
from .converters import GeoConverter, TimeframeConverter
from .errors import NoData
from .plot import TrendsPlot
from .vexutils import url_buttons
from .vexutils.meta import format_help, format_info


class GoogleTrends(commands.Cog, TrendsPlot, metaclass=CompositeMetaClass):
    """
    Find what the world is searching, right from Discord.

    Please note that there is no Google Trends API, so this is a web scraper and may break at
    any time.
    """

    __version__ = "1.1.0"
    __author__ = "Vexed#0714"

    def __init__(self, bot):
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        self.executor.shutdown(wait=False)

    @commands.command(hidden=True)
    async def trendsinfo(self, ctx: commands.Context):
        await ctx.send(await (format_info(ctx, self.qualified_name, self.__version__)))

    @commands.cooldown(10, 60, commands.BucketType.user)
    @commands.command(usage="[timeframe=7d] [geo=world] <query...>")
    async def trends(
        self,
        ctx: commands.Context,
        timeframe: Optional[TimeframeConverter] = "now 7-d",
        geo: Optional[GeoConverter] = "",
        *query: str,
    ):
        """
        Find what the world is searching, right from Discord.

        **Get started with `[p]trends discord` for a basic example!**

        **Optional**

        `timeframe`:
            You can specify either the long (eg `4hours`) or short (`eg 4h`) version of the
            timeframes. All other values not listed below are invalid.

            `hour`/`1h`
            `4hours`/`4h`
            `day`/`1d`
            `week`/`7d`
            `month`/`1m`
            `3months`/`3m`
            `12months`/`12m`
            `5years`/`5y`
            `all`

        `geo`:
            Defaults to `world`
            You can specify a two-letter geographic code, such as `US`, `GB` or `FR`.
            Sometimes, you can also add a sub-region. See
            https://go.vexcodes.com/trends_geo for a list.

        **Required**

        `trends`:
            Whatever you want! You can add multiple trends, and separate them with a space.
            If your trend has spaces in it, you can use `+` instead of a space or enclose it
            in quotes, for example `Card games` to `Card+games` or `"Card games"`.

        **Examples:**
            The help message is so long that examples wouldn't fit! Run `[p]trendsexamples`
            to see some.
        """
        if timeframe is None or geo is None:
            # should never happen
            return

        query = deduplicate_iterables(query)  # type:ignore

        if len(query) == 0 and geo != "" and timeframe != "now 7-d":  # not defaults
            await ctx.send("You must specify at least one query. For example, `[p]trends discord`")
            return
        elif len(query) == 0:
            await ctx.send_help()
            return

        if len(query) > 5:
            await ctx.send("Sorry, the maximum about of queries is 5")
            return

        async with ctx.typing():
            try:
                request = await self.get_trends_request(list(query), timeframe, geo)
            except ResponseError as e:
                if e.response.status_code == 400:
                    await ctx.send("Your request failed. It looks like something's invalid.")
                elif e.response.status_code in (403, 429):
                    await ctx.send(
                        "Your request failed. It looks like we've hit a rate limit. "
                        "Try again in a minute."
                    )
                else:
                    await ctx.send("Your request failed for an unexpected reason.")
                return

            try:
                file = await self.plot_graph(request, timeframe, geo)
            except NoData:
                await ctx.send(
                    "Sorry, there's no significant data for that. Check your spelling or choose "
                    "another query."
                )
                return

        full_location = [k for k, v in GEOS.items() if v == geo][0]
        full_timeframe = TIMEFRAMES.get(timeframe, "")

        url = self.get_trends_url(timeframe, geo, query)

        embed = discord.Embed(
            title=f"Interest over time, {full_location}, {full_timeframe}",
            colour=await ctx.embed_colour(),
        )
        embed.set_footer(
            text=f"Times are in UTC\nSee {ctx.clean_prefix}help trends for advanced usage\n"
            + "Data sourced from Google Trends."
        )
        embed.set_image(url="attachment://plot.png")

        button = url_buttons.URLButton("View on Google Trends", url)
        await url_buttons.send_message(
            self.bot, ctx.channel.id, embed=embed, file=file, url_button=button
        )

    def get_trends_url(self, timeframe: str, geo: str, query: Iterable[str]) -> str:
        """Get the Google Trends URL for a given timeframe, geo, and query."""
        trends_params = {}
        if timeframe != "today 12-m":
            trends_params["date"] = timeframe
        if geo != "":
            trends_params["geo"] = geo
        trends_params["q"] = ",".join(query)
        return "https://trends.google.com/trends/explore?" + urlencode(
            trends_params, quote_via=quote
        )

    @commands.command()
    async def trendsexamples(self, ctx: commands.Context):
        """These are some examples of how to use the `[p]trends` command,
        for details see `[p]help trends`"""
        p = ctx.clean_prefix
        await ctx.send(
            "**Examples**\n\n"
            f"`{p}trends discord`\n"
            "    The simple one! Trends for Discord, 7 days, worldwide\n"
            f"- `{p}trends 1d US discord twitter youtube`\n"
            "    1 day, United Stats searching for Discord, Twitter and YouTube\n"
            f"- `{p}trends 1y COVID-19`\n"
            "    Trend for COVID-19 in the last year in the world\n"
            f"- `{p}trends all GB discord`\n"
            "    Trend for Discord in the United Kingdom for all time\n"
            f'- `{p}trends all US-NY "Donald Trump" "Joe Biden"`\n'
            "    A trend with spaces - Donald Trump and Joe Biden in New York State for all time\n"
            f"\nTo see more detailed usage information, see `{p}help trends`"
        )
