import asyncio
import functools
import io

import discord
import matplotlib
import pandas
from matplotlib import pyplot as plt

matplotlib.use("agg")


ONE_DAY_SECONDS = 86400


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
    with plt.style.context("dark_background"):
        fig = plt.figure(figsize=(8, 5))
        ax = fig.add_subplot(111)
        ax = sr.plot(
            ylabel="Percentage",
            title="Daily uptime data",
            ax=ax,
        )
        ax.set_ylim([0, 105])
        buffer = io.BytesIO()
        fig.savefig(buffer, format="png", dpi=200)
        plt.close(fig)
        buffer.seek(0)
        file = discord.File(buffer, "plot.png")
        buffer.close()
        return file
