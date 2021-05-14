import asyncio
import datetime
import functools
import io

import discord
import pandas

from stattrack.converters import TimeData


async def plot(df: pandas.DataFrame, timespan: TimeData, title: str, ylabel: str) -> discord.File:
    """Plot the standard dataframe to the specified parameters. Returns a file ready for Discord"""
    return await asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(
            _plot,
            df=df,
            delta=timespan.delta,
            title=title,
            ylabel=ylabel,
            freq=timespan.freq,
        ),
    )


def _plot(
    df: pandas.DataFrame, delta: datetime.timedelta, title: str, ylabel: str, freq: str
) -> discord.File:
    """Do not use on own - blocking."""
    # plotting and saving takes ~0.5 to 1 second for me
    now = datetime.datetime.utcnow().replace(microsecond=0, second=0)
    start = now - delta
    if start < df.first_valid_index():
        start = df.first_valid_index()
    expected_index = pandas.date_range(start=start, end=now, freq=freq)
    df = df.reindex(expected_index)

    buffer = io.BytesIO()
    plot = df.plot(figsize=(7, 4), title=title, xlabel="Time (UTC)", ylabel=ylabel)
    plot.set_ylim(bottom=0)

    plot.get_figure().savefig(buffer, format="png", dpi=200)
    buffer.seek(0)
    return discord.File(buffer, "plot.png")
