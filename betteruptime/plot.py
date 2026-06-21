import asyncio
import io
from heapq import nsmallest  # this is standard library
from typing import Dict, Optional, Tuple

import discord
import pandas as pd


async def plot(sr: pd.Series) -> Tuple[discord.File, Optional[float]]:
    """Plot the series using Matplotlib and return a Discord file and optional labelled threshold.

    This offloads the blocking work to a thread pool to avoid blocking the event loop.
    """
    loop = asyncio.get_event_loop()
    return await asyncio.wait_for(loop.run_in_executor(None, _plot, sr), timeout=60.0)


def _plot(sr: pd.Series) -> Tuple[discord.File, Optional[float]]:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # Prepare figure
    plt.style.use("dark_background")
    fig, ax = plt.subplots(figsize=(8, 5), dpi=100)

    x = sr.index
    y = sr.values.astype(float)

    ax.plot(x, y, color="#1f77b4", linewidth=2)
    ax.fill_between(x, y, 0, color="#1f77b4", alpha=0.08)

    ax.set_ylabel("Percentage uptime")
    ax.set_xlabel("Date")
    fig.autofmt_xdate()
    ax.set_ylim(bottom=0)
    ax.set_title("Daily uptime")
    ax.tick_params(labelsize=10)

    # annotate low values (<99.7)
    low_values: Dict[pd.Timestamp, float] = {}
    for i, value in enumerate(y):
        if value < 99.7:
            date = x[i]
            low_values[date] = float(value)

    values_to_annotate = nsmallest(5, low_values.values())
    for val in values_to_annotate:
        # find the corresponding date for this value (first match)
        date = next(k for k, v in low_values.items() if v == val)
        ax.annotate(
            f"{val}%\n{date.strftime('%d %b')}",
            xy=(date, val),
            xytext=(0, 8),
            textcoords="offset points",
            ha="center",
            fontsize=9,
        )

    labelled_pc = max(low_values.values()) if low_values else None

    # Render to PNG in memory
    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png")
    plt.close(fig)
    buf.seek(0)
    file = discord.File(buf, filename="plot.png")
    return file, labelled_pc
