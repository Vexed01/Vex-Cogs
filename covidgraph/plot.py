import functools
import io

import discord
import pandas as pd
import plotly.express as px
from asyncache import cached
from cachetools import TTLCache
from plotly.graph_objs._figure import Figure

from .abc import MixinMeta

# yes i am using private import, atm plotly does dynamic imports which are not supported by mypy


# need to specially handle pandas' series because it is unhashable with hash()
def custom_key(*args, **kwargs):
    ret = []
    everything = args + tuple(kwargs.values())
    for arg in everything:
        if isinstance(arg, pd.Series):
            ret.append(str(arg))  # a series is unhashable, so we need to convert it to a string
            # and the string will contain the first few and last few elements of the series
            # which is good enough for our purposes
        else:
            ret.append(arg)
    return tuple(ret)


class GraphPlot(MixinMeta):
    # the graph generation can be cached but the discord.File returned is single use
    # cacheing is deffo faster.
    async def plot_graph(self, data: pd.Series, label: str) -> discord.File:
        """Get a graph of the trends."""
        func = functools.partial(self._plot_graph, ts=data, label=label)
        b = await self.bot.loop.run_in_executor(self.executor, func)
        return self.bytes_to_file(b)

    @cached(TTLCache(maxsize=64, ttl=86400), custom_key)
    # graphs are ~50KB so this is only 3 MB which is basically nothing for the speed improvement
    # and 1 day TTL should mean new data is available when it stops being used
    def _plot_graph(self, ts: pd.Series, label: str) -> bytes:
        """Blocking"""
        ts.name = "Raw data"
        df = pd.DataFrame(ts)
        df["7-day avg"] = ts.rolling(7, center=True).mean()

        fig: Figure = px.line(
            df,
            template="plotly_dark",
            color_discrete_map={
                "Raw data": "#3d3e59",
                "7-day avg": "#636efa",
            },
            labels={"index": "Date", "value": label, "variable": "Key"},
        )
        fig.update_layout(
            title_x=0.5,
            font_size=14,
        )
        fig.update_yaxes(rangemode="tozero")
        bytes = fig.to_image(format="png", width=800, height=500, scale=1)
        return bytes

    def bytes_to_file(self, b: bytes) -> discord.File:
        """Convert bytes to discord.File."""
        fp = io.BytesIO(b)
        file = discord.File(fp, filename="plot.png")
        fp.close()
        return file
