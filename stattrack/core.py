import asyncio
import datetime
import io
import random

import discord
import pandas
from redbot.core import commands
from redbot.core.bot import Red
from vexcogutils import format_help, format_info

def snapped_utcnow():
    return datetime.datetime.utcnow().replace(microsecond=0).replace(second=0)


# TODO:
# track guild count, user count
# save/retrieve from config
# maybe use a dark style


class StatTrack(commands.Cog):
    """BETA COG: StatTrack (Stat Tracking)"""

    __version__ = "0.0.0"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.df_cache = pandas.DataFrame()

        self.loop = asyncio.create_task(self.le_loop())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        self.loop.cancel()

    @commands.command(hidden=True)
    async def stattrackinfo(self, ctx: commands.Context):
        await ctx.send(format_info(self.qualified_name, self.__version__))

    async def le_loop(self):
        while True:
            df = pandas.DataFrame(index=[snapped_utcnow()])
            df["ping"] = [round(self.bot.latency * 1000)]
            self.df_cache = self.df_cache.append(df)

            await asyncio.sleep(60)

    @commands.command()
    async def stattrack(self, ctx: commands.Context):
        now = snapped_utcnow()
        expected_index = pandas.date_range(start=now - datetime.timedelta(minutes=60), end=now, freq="min")
        df = self.df_cache.reindex(expected_index)  # will not overwrite

        buffer = io.BytesIO()
        plot = df.plot(figsize=(7, 4), title="Ping data for the last 60 minutes.")
        plot.set_xlabel("Time (UTC)")
        plot.set_ylabel("Ping (ms)")
        plot.get_figure().savefig(buffer, format="png", dpi=200)
        buffer.seek(0)
        file = discord.File(buffer, "plot.png")
        await ctx.send("hi", file=file)
