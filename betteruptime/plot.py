import asyncio
import functools
import io

import discord
import pandas
import plotly.express as px
from pandas import Timestamp
from plotly.graph_objs._figure import Figure

# yes i am using a private import, atm plotly does dynamic imports which are not supported by mypy


async def plot(sr: pandas.Series) -> discord.File:
    """Plot the standard dataframe to the specified parameters. Returns a file ready for Discord"""
    task = asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(
            _plot,
            sr=sr,
        ),
    )
    return await asyncio.wait_for(task, timeout=10.0)


def _plot(
    sr: pandas.Series,
) -> discord.File:
    """Do not use on own - blocking."""

    fig: Figure = px.line(
        sr,
        template="plotly_dark",
        labels={"index": "Date", "value": "Percentage uptime"},
    )
    fig.update_layout(
        title_x=0.5,
        font_size=14,
        showlegend=False,
    )
    for i, value in enumerate(sr.values):
        if value < 99.7:  # only annotate non-perfect days
            date: Timestamp = sr.index[i]  # type:ignore
            fig.add_annotation(
                x=date,
                y=value,
                text=f"{value}%\n{date.strftime('%d %b')}",
            )
    fig.update_yaxes(rangemode="tozero")
    bytes = fig.to_image(format="png", width=800, height=500, scale=1)
    buffer = io.BytesIO(bytes)
    buffer.seek(0)
    file = discord.File(buffer, filename="plot.png")
    buffer.close()
    return file
