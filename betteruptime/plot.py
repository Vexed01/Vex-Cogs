import asyncio
import functools
import io

import discord
import matplotlib
import pandas
from matplotlib import pyplot as plt
from numpy import ceil, floor
from pandas import Timestamp

matplotlib.use("agg")


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


def get_y_lim_min(sr: pandas.Series) -> int:
    min = sr.min()
    if min > 70:
        return 60
    if min > 20:
        return floor((min / 10) - 1.3) * 10
    return 0


def get_y_lim_max(sr: pandas.Series):
    max = sr.max()
    if max > 90:
        return 104
    if max > 50:
        return ceil((max / 10) * 10) + 4
    return ceil((max / 10) * 10) + 2.5


def _plot(
    sr: pandas.Series,
) -> discord.File:
    """Do not use on own - blocking."""
    with plt.style.context("dark_background"):
        fig = plt.figure(figsize=(8, 5))
        ax = fig.add_subplot(111)
        ax = sr.plot(
            ylabel="Percentage",
            title="Daily uptime data",
            ax=ax,
        )

        ymin = get_y_lim_min(sr)
        ymax = get_y_lim_max(sr)
        ax.set_ylim([ymin, ymax])

        for i, value in enumerate(sr.values):
            if value < 99.7:  # only annotate days that weren't perfect
                date: Timestamp = sr.index[i]
                ax.annotate(
                    f"{value}%\n{date.strftime('%d %b')}",  # type:ignore  # stubs incorrect
                    (sr.index[i], value),
                    xytext=(sr.index[i], value - ((ymax - ymin) / 8)),
                    arrowprops={"arrowstyle": "-"},
                )

        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=200)
        plt.close(fig)
        buffer.seek(0)
        file = discord.File(buffer, "plot.png")
        buffer.close()
        return file
