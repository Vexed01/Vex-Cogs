import functools
import io
from concurrent.futures.thread import ThreadPoolExecutor
from typing import TYPE_CHECKING

import discord
import pandas as pd
from plotly import express as px

from .abc import MixinMeta
from .consts import TRACE_FRIENDLY_NAMES

if TYPE_CHECKING:
    from plotly.graph_objs._figure import Figure
else:
    from plotly.graph_objs import Figure
# yes i am using a private import from plotly, atm plotly does dynamic imports which are not
# supported by mypy


ONE_DAY_SECONDS = 86400


class StatPlot(MixinMeta):
    def __init__(self) -> None:
        self.plot_executor = ThreadPoolExecutor(5, "stattrack_plot")

    async def plot(self, df: pd.DataFrame, ylabel: str, status_colours: bool) -> discord.File:
        """Plot the standard dataframe to the specified parameters. Returns a discord file"""
        func = functools.partial(
            self._plot,
            df=df,
            ylabel=ylabel,
            status_colours=status_colours,
        )

        return await self.bot.loop.run_in_executor(self.plot_executor, func)

    def _plot(
        self,
        df: pd.DataFrame,
        ylabel: str,
        status_colours: bool,
    ) -> discord.File:
        """Do not use on own - blocking."""
        colour_map = (
            {
                "status_online": "#3ba55d",
                "status_idle": "#FAA81A",
                "status_offline": "#747f8d",
                "status_dnd": "#ed4245",
            }
            if status_colours
            else None
        )
        fig: Figure = px.line(
            df,
            template="plotly_dark",
            labels={"index": "Date", "value": ylabel, "variable": "Metric"},
            color_discrete_map=colour_map,
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

        # rename the legend item of each trace in fig
        for trace in fig.data:
            trace.name = TRACE_FRIENDLY_NAMES[trace.name]  # type:ignore

        bytes = fig.to_image(format="png", width=800, height=500, scale=1)
        buffer = io.BytesIO(bytes)
        buffer.seek(0)
        file = discord.File(buffer, filename="plot.png")
        buffer.close()
        return file
