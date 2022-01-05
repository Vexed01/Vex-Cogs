import functools
import io
from concurrent.futures.thread import ThreadPoolExecutor
from typing import Iterable

import discord
import pandas
import plotly.express as px
from plotly.graph_objs._figure import Figure
from pytrends.request import TrendReq

from googletrends.errors import NoData

from .abc import MixinMeta

# yes i am using private import, atm plotly does dynamic imports which are not supported by mypy


# pytrends is not async and there is no maintained alternative.
# pytrends itself seems maintained atm, though the last commit was half a year ago,
# however it is currently functional
# pytrends and plotting are therefore wrapped in executors
# and thank you kowlin for sorta introducing me to plotly


class TrendsPlot(MixinMeta):
    def __init__(self) -> None:
        self.executor = ThreadPoolExecutor(16, thread_name_prefix="googletrends")

    async def get_trends_request(
        self, keywords: Iterable[str], timeframe: str, geo: str
    ) -> TrendReq:
        """Get a TrendsReq object ready for use in plotting."""
        func = functools.partial(
            self._get_trends_request, keywords=keywords, timeframe=timeframe, geo=geo
        )

        return await self.bot.loop.run_in_executor(self.executor, func)

    def _get_trends_request(self, keywords: list, timeframe: str, geo: str) -> TrendReq:
        """Blocking"""
        trend = TrendReq(hl="en-US", tz=0, retries=1)
        trend.build_payload(
            kw_list=keywords,
            timeframe=timeframe,
            geo=geo,
        )
        return trend

    async def plot_graph(self, trend: TrendReq, timeframe: str, geo: str) -> discord.File:
        """Get a graph of the trends."""
        func = functools.partial(self._plot_graph, trend=trend, timeframe=timeframe, geo=geo)

        return await self.bot.loop.run_in_executor(self.executor, func)

    def _plot_graph(self, trend: TrendReq, timeframe: str, geo: str) -> discord.File:
        """Blocking"""
        df = trend.interest_over_time()
        assert isinstance(df, pandas.DataFrame)

        try:
            del df["isPartial"]
        except KeyError:
            pass

        if df.empty:
            raise NoData

        fig: Figure = px.line(
            df,
            template="plotly_dark",
            labels={"date": "Date", "value": "Interest, 0-100", "variable": "Query"},
        )
        fig.update_layout(
            title_x=0.5,
            font_size=14,
            legend={
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
        )
        fig.update_yaxes(rangemode="tozero")
        bytes = fig.to_image(format="png", width=800, height=500, scale=1)
        buffer = io.BytesIO(bytes)
        buffer.seek(0)
        file = discord.File(buffer, filename="plot.png")
        buffer.close()
        return file
