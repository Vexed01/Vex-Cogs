import functools
import io
from asyncio.events import AbstractEventLoop

import discord
import pandas as pd
import plotly.express as px
from plotly.graph_objs._figure import Figure

from .abc import MixinMeta

# yes i am using private import, atm plotly does dynamic imports which are not supported by mypy


class GraphPlot(MixinMeta):
    async def plot_graph(self, data: pd.Series, label: str) -> discord.File:
        """Get a graph of the trends."""
        func = functools.partial(self._plot_graph, ts=data, label=label)

        assert isinstance(self.bot.loop, AbstractEventLoop)
        return await self.bot.loop.run_in_executor(self.executor, func)

    def _plot_graph(self, ts: pd.Series, label: str) -> discord.File:
        """Blocking"""
        fig: Figure = px.line(
            ts,
            template="plotly_dark",
            labels={"index": "Date", "value": label},
        )

        fig.update_layout(
            title_x=0.5,
            font_size=14,
            showlegend=False,
        )
        fig.update_yaxes(rangemode="tozero")
        bytes = fig.to_image(format="png", width=800, height=500, scale=1)
        buffer = io.BytesIO(bytes)
        buffer.seek(0)
        file = discord.File(buffer, filename="plot.png")
        buffer.close()
        return file
