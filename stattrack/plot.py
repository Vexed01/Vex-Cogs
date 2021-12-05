import functools
import io
from asyncio.events import AbstractEventLoop
from concurrent.futures.thread import ThreadPoolExecutor

import discord
import pandas as pd
from plotly import express as px
from plotly.graph_objs._figure import Figure

from stattrack.abc import MixinMeta

# yes i am using a private import from plotly, atm plotly does dynamic imports which are not
# supported by mypy


ONE_DAY_SECONDS = 86400

TRACE_FRIENDLY_NAMES = {
    "ping": "Latency",
    "loop_time_s": "Loop time",
    "users_unique": "Unique",
    "users_total": "Total",
    "users_humans": "Humans",
    "users_bots": "Bots",
    "guilds": "Servers",
    "channels_total": "Total",
    "channels_text": "Text",
    "channels_voice": "Voice",
    "channels_stage": "Stage",
    "channels_cat": "Categories",
    "sys_mem": "Memory usage",
    "sys_cpu": "CPU Usage",
    "command_count": "Commands",
    "message_count": "Messages",
    "status_online": "Online",
    "status_idle": "Idle",
    "status_offline": "Offline",
    "status_dnd": "DnD",
}


class StatPlot(MixinMeta):
    def __init__(self) -> None:
        self.plot_executor = ThreadPoolExecutor(5, "stattrack_plot")

    async def plot(self, df: pd.DataFrame, ylabel: str) -> discord.File:
        """Plot the standard dataframe to the specified parameters. Returns a discord file"""
        func = functools.partial(
            self._plot,
            df=df,
            ylabel=ylabel,
        )

        assert isinstance(self.bot.loop, AbstractEventLoop)
        return await self.bot.loop.run_in_executor(self.plot_executor, func)

    def _plot(
        self,
        df: pd.DataFrame,
        ylabel: str,
    ) -> discord.File:
        """Do not use on own - blocking."""
        fig: Figure = px.line(
            df,
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

        # rename the legend item of each trace in fig
        for trace in fig.data:
            trace.name = TRACE_FRIENDLY_NAMES[trace.name]

        bytes = fig.to_image(format="png", width=800, height=500, scale=1)
        buffer = io.BytesIO(bytes)
        buffer.seek(0)
        file = discord.File(buffer, filename="plot.png")
        buffer.close()
        return file
