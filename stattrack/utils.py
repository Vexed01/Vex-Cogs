import io
from typing import List

import discord
from pandas import DataFrame


async def plot(df: DataFrame, title: str, xlabel: str, ylabel: str):

def _plot(df, subset):    
    buffer = io.BytesIO()
    plot = df.plot(figsize=(7, 4), title=title, xlabel=xlabel, ylabel=ylabel)
    plot.set_xlabel("Time (UTC)")
    plot.set_ylabel("Ping (ms)")
    # await ctx.send(end - start)
    plot.get_figure().savefig(buffer, format="png", dpi=200)    
    buffer.seek(0)
    file = discord.File(buffer, "plot.png")    
    return file
