import asyncio
import functools
import io
from heapq import nsmallest  # this is standard library
from typing import TYPE_CHECKING, Dict, Optional, Tuple

import discord
import pandas
import plotly.express as px
from pandas import Timestamp

if TYPE_CHECKING:
    from plotly.graph_objs._figure import Figure
else:
    from plotly.graph_objs import Figure

# yes i am using a private import, atm plotly does dynamic imports which are not supported by mypy


async def plot(sr: pandas.Series) -> Tuple[discord.File, Optional[float]]:
    """Plot the standard dataframe to the specified parameters. Returns a file ready for Discord"""
    task = asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(
            _plot,
            sr=sr,
        ),
    )
    return await asyncio.wait_for(task, timeout=60.0)


def _plot(
    sr: pandas.Series,
) -> Tuple[discord.File, Optional[float]]:
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

    low_values: Dict[Timestamp, float] = {}
    for i, value in enumerate(sr.values):
        if value < 99.7:  # only annotate non-perfect days
            date: Timestamp = sr.index[i]  # type: ignore
            low_values[date] = value

    values_to_annotate = nsmallest(5, low_values.values())
    for val in values_to_annotate:  # for low uptime bots, don't flood with annotations
        date = list(low_values.keys())[list(low_values.values()).index(val)]  # get date from value
        fig.add_annotation(
            x=date,
            y=val,
            text=f"{val}%\n{date.strftime('%d %b')}",
        )

    labelled_pc = max(low_values.values()) if low_values else None

    fig.update_yaxes(rangemode="tozero")
    bytes = fig.to_image(format="png", width=800, height=500, scale=1)
    buffer = io.BytesIO(bytes)
    buffer.seek(0)
    file = discord.File(buffer, filename="plot.png")
    buffer.close()
    return file, labelled_pc
