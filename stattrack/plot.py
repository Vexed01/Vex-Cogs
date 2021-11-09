import datetime
import functools
import io
from asyncio.events import AbstractEventLoop
from concurrent.futures.thread import ThreadPoolExecutor

import discord
import pandas
from plotly import express as px
from plotly.graph_objs._figure import Figure

from stattrack.abc import MixinMeta

# yes i am using a private import from plotly, atm plotly does dynamic imports which are not
# supported by mypy


ONE_DAY_SECONDS = 86400


class StatPlot(MixinMeta):
    def __init__(self) -> None:
        self.plot_executor = ThreadPoolExecutor(5, "stattrack_plot")

    async def plot(
        self, sr: pandas.Series, delta: datetime.timedelta, ylabel: str
    ) -> discord.File:
        """Plot the standard dataframe to the specified parameters. Returns a discord file"""
        func = functools.partial(
            self._plot,
            sr=sr,
            delta=delta,
            ylabel=ylabel,
        )

        assert isinstance(self.bot.loop, AbstractEventLoop)
        return await self.bot.loop.run_in_executor(self.plot_executor, func)

    def _plot(
        self,
        sr: pandas.Series,
        delta: datetime.timedelta,
        ylabel: str,
    ) -> discord.File:
        """Do not use on own - blocking."""
        now = datetime.datetime.utcnow().replace(microsecond=0, second=0)
        start = now - delta
        start = max(start, sr.first_valid_index())
        expected_index = pandas.date_range(start=start, end=now, freq="min")
        sr = sr.reindex(expected_index)  # ensure all data is present or set to NaN

        fig: Figure = px.line(
            sr,
            template="plotly_dark",
            labels={"index": "Date", "value": ylabel, "variable": "Metric"},
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
        bytes = fig.to_image(format="png", width=800, height=500, scale=1)
        buffer = io.BytesIO(bytes)
        buffer.seek(0)
        file = discord.File(buffer, filename="plot.png")
        buffer.close()
        return file
