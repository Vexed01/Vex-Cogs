import asyncio
import datetime
import functools
import io

import discord
import matplotlib
import pandas
from matplotlib import pyplot as plt
from matplotlib.axes import Axes
from matplotlib.dates import DateFormatter
from matplotlib.ticker import MaxNLocator
from redbot.core.utils.chat_formatting import humanize_timedelta

matplotlib.use("agg")


ONE_DAY_SECONDS = 86400


async def plot(
    sr: pandas.Series, delta: datetime.timedelta, title: str, ylabel: str
) -> discord.File:
    """Plot the standard dataframe to the specified parameters. Returns a file ready for Discord"""
    task = asyncio.get_event_loop().run_in_executor(
        None,
        functools.partial(
            _plot,
            sr=sr,
            delta=delta,
            title=title,
            ylabel=ylabel,
        ),
    )
    return await asyncio.wait_for(task, timeout=10.0)  # should be around 1 sec


def _plot(
    sr: pandas.Series,
    delta: datetime.timedelta,
    title: str,
    ylabel: str,
) -> discord.File:
    """Do not use on own - blocking."""
    # plotting and saving blocks event loop for ~0.5 to 1 second for me
    now = datetime.datetime.utcnow().replace(microsecond=0, second=0)
    start = now - delta
    start = max(start, sr.first_valid_index())
    expected_index = pandas.date_range(start=start, end=now, freq="min")
    ret = sr.reindex(expected_index)  # ensure all data is present or set to NaN
    assert isinstance(ret, pandas.Series)
    sr = ret
    real_delta = now - sr.first_valid_index()

    fig = plt.figure(figsize=(7, 5))
    ax = fig.add_subplot(111)
    assert isinstance(ax, Axes)
    ax.set_title(title + " for the last " + humanize_timedelta(timedelta=real_delta))
    ax.set_xlabel("Time (UTC)")
    ax.set_ylabel(ylabel)
    ax.xaxis.set_major_formatter(_get_date_formatter(delta))
    ax.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax.margins(y=0.05)
    ax.plot(sr.index, sr)
    ax.ticklabel_format(axis="y", style="plain")
    buffer = io.BytesIO()
    fig.savefig(buffer, format="png", dpi=200)
    plt.close(fig)
    buffer.seek(0)
    return discord.File(buffer, "plot.png")


def _get_date_formatter(delta: datetime.timedelta) -> DateFormatter:
    if delta.total_seconds() <= ONE_DAY_SECONDS:
        return DateFormatter("%H:%M")
    elif delta.total_seconds() <= (ONE_DAY_SECONDS * 4):
        return DateFormatter("%d %b %I%p")
    return DateFormatter("%d %b")
