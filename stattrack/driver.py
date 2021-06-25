import concurrent.futures
import functools
import sqlite3
from asyncio.events import AbstractEventLoop

import pandas
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path

# TODO: maybe find something better than SQLite that's more intended for storage than being
# indexable. tried feather and hdf, both of which integrate with pandas, but they require too
# many deps for the premise of this cog (simple stat tracking)
# someone wanting more advanced stuff should look at preda's offerings

# (comparisons from red config, mainly to make me feel like i didn't waste an evening)
# this compares a write for config to appending to the SQL. i've not compared writes because they
# will only happend once, for migration from config. SQL includes copying DF + executor overhead
# basically this is the raw speed changes for the loop itself
# ~1.3 sec to ~0.03 sec, dataset of ~1 week on windows
# ~5-6 sec to ~[] sec, dataset of ~1 month on linux
# reads are insignificant as only happen on cog load


class StatTrackDriver:
    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.sql_executor = concurrent.futures.ThreadPoolExecutor(1, "stattrack_sql")
        self.sql_path = str(cog_data_path(raw_name="StatTrack") / "timeseries.db")

    def _write(self, df: pandas.DataFrame) -> None:
        """Blocking on larger datasets/slower disks - run me in executor. Please."""
        connection = sqlite3.connect(self.sql_path)
        df.to_sql("main_df", con=connection, if_exists="replace")
        connection.commit()
        connection.close()

    def _append(self, df: pandas.DataFrame) -> None:
        """Blocking - run me in executor. Please."""
        connection = sqlite3.connect(self.sql_path)
        df.to_sql("main_df", con=connection, if_exists="append")
        connection.commit()
        connection.close()

    def _read(self) -> pandas.DataFrame:
        connection = sqlite3.connect(self.sql_path)
        df = pandas.read_sql(
            "SELECT * FROM main_df", connection, index_col="index", parse_dates=["index"]
        )
        connection.close()
        return df

    async def write(self, df: pandas.DataFrame) -> None:
        """Write a dataframe to the database. Replaces and old data."""
        assert isinstance(self.bot.loop, AbstractEventLoop)
        func = functools.partial(self._write, df.copy(True))
        await self.bot.loop.run_in_executor(self.sql_executor, func)

    async def append(self, df: pandas.DataFrame) -> None:
        """Append a dataframe to the database."""
        assert isinstance(self.bot.loop, AbstractEventLoop)
        func = functools.partial(self._append, df.copy(True))
        await self.bot.loop.run_in_executor(self.sql_executor, func)

    async def read(self) -> pandas.DataFrame:
        """Read the database, returning as a pandas dataframe."""
        assert isinstance(self.bot.loop, AbstractEventLoop)
        func = functools.partial(self._read)
        return await self.bot.loop.run_in_executor(self.sql_executor, func)
