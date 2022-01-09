import concurrent.futures
import functools
import os
import sqlite3
from asyncio.events import AbstractEventLoop
from typing import Optional

from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path

# (comparisons from red config, mainly to make me feel like i didn't waste an evening)
# (these are with the stattrack cog, this driver is also used in betteruptime)
# this compares a write for config to appending to the SQL. i've not compared writes because they
# will only happend once, for migration from config. SQL includes copying DF + executor overhead
# basically this is the raw speed changes for the loop itself
# ~1.3 sec to ~0.03 sec, dataset of ~1 week on windows
# ~5-6 sec to ~0.04 sec, dataset of ~1 month on linux
# reads are insignificant as only happen on cog load

try:
    import pandas
except ImportError:
    raise RuntimeError("Pandas must be installed for this driver to work.")


class PandasSQLiteDriver:
    """An asynchronous SQLite driver for Pandas dataframes."""

    def __init__(self, bot: Red, cog_name: str, filename: str, table: str = "main_df") -> None:
        """Get a driver object for interacting with a table in the given cog's datapath.

        Parameters
        ----------
        bot : Red
            Bot object
        cog_name : str
            Full cog name, LikeThis
        filename : str
            The full file name to use for the database, for example `timeseries.db`
        table : str, optional
            The SQLite table to use, by default "main_df"
        """
        self.bot = bot
        self.table = table

        self.sql_executor = concurrent.futures.ThreadPoolExecutor(1, f"{cog_name.lower()}_sql")
        self.sql_path = str(cog_data_path(raw_name=cog_name) / filename)

    def _write(self, df: pandas.DataFrame, table: Optional[str] = None) -> None:
        connection = sqlite3.connect(self.sql_path)
        try:
            df.to_sql(table or self.table, con=connection, if_exists="replace")  # type:ignore
            connection.commit()
        finally:
            connection.close()

    def _append(self, df: pandas.DataFrame, table: Optional[str] = None) -> None:
        connection = sqlite3.connect(self.sql_path)
        try:
            df.to_sql(table or self.table, con=connection, if_exists="append")  # type:ignore
            connection.commit()
        finally:
            connection.close()

    def _read(self, table: Optional[str] = None) -> pandas.DataFrame:
        connection = sqlite3.connect(self.sql_path)
        try:
            df = pandas.read_sql(
                f"SELECT * FROM {table or self.table}",
                connection,
                index_col="index",
                parse_dates=["index"],
            )
            return df
        finally:
            connection.close()

    async def write(self, df: pandas.DataFrame, table: Optional[str] = None) -> None:
        """Write a dataframe to the database. Replaces and old data."""
        assert isinstance(self.bot.loop, AbstractEventLoop)
        func = functools.partial(self._write, df.copy(True), table)
        await self.bot.loop.run_in_executor(self.sql_executor, func)

    async def append(self, df: pandas.DataFrame, table: Optional[str] = None) -> None:
        """Append a dataframe to the database."""
        assert isinstance(self.bot.loop, AbstractEventLoop)
        func = functools.partial(self._append, df.copy(True), table)
        await self.bot.loop.run_in_executor(self.sql_executor, func)

    async def read(self, table: Optional[str] = None) -> pandas.DataFrame:
        """Read the database, returning as a pandas dataframe."""
        assert isinstance(self.bot.loop, AbstractEventLoop)
        func = functools.partial(self._read, table)
        return await self.bot.loop.run_in_executor(self.sql_executor, func)

    def storage_usage(self) -> int:
        """Return the size of the database file in bytes."""
        return os.path.getsize(self.sql_path)
