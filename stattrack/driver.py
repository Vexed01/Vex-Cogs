from __future__ import annotations

import asyncio
import datetime
import os
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from typing import Iterable

import aiosqlite
import pandas as pd
from redbot.core.data_manager import cog_data_path


class StatTrackSQLiteDriver:
    """An asynchronous SQLite driver, working with DataFrames. Tailored to StatTrack"""

    def __init__(self) -> None:
        self.sql_path = str(cog_data_path(raw_name="stattrack") / "timeseries.db")
        self.sql_write_executor = ThreadPoolExecutor(1, "stattrack_sql_write")

    def storage_usage(self) -> int:
        """Return the size of the database file in bytes."""
        return os.path.getsize(self.sql_path)

    async def get_last_index(self) -> pd.Timestamp:
        """Get the latest index from the database.

        Returns
        -------
        pd.Timestamp
        """
        query = 'SELECT "index" FROM main_df ORDER BY "index" DESC LIMIT 1'
        async with aiosqlite.connect(self.sql_path) as conn:
            async with conn.execute(query) as cursor:
                index = await cursor.fetchone()
        if index is None:
            return pd.Timestamp(0)
        return pd.to_datetime(index[0])

    async def read_all(self) -> pd.DataFrame:
        """Create a Pandas DataFrame from the whole table.

        Returns
        -------
        pd.DataFrame
        """
        query = "SELECT * FROM main_df"
        async with aiosqlite.connect(self.sql_path) as conn:
            async with conn.execute("PRAGMA table_info(main_df)") as cursor:
                columns = [row[1] for row in await cursor.fetchall()]
            async with conn.execute(query) as cursor:
                data = await cursor.fetchall()
        df = pd.DataFrame(data, columns=columns)
        df.set_index("index", inplace=True)
        df.index = pd.to_datetime(df.index, infer_datetime_format=True)
        return df

    async def read_partial(
        self, metrics: Iterable[str], delta: datetime.timedelta | None = None
    ) -> pd.DataFrame:
        """Build a SELECT query and execute it, creating a Pandas DataFrame.

        Parameters
        ----------
        metrics : Iterable[str]
            The metric(s) to query

        delta : datetime.timedelta, optional
            Timeframe for data: from now to `delta` ago
            If not given, data returned will be all-time.

        Returns
        -------
        pd.DataFrame
        """
        query = f"""
        SELECT "index",{",".join(metrics)}
        FROM main_df
        """
        if delta:
            start_timestamp = (datetime.datetime.now() - delta).strftime("%Y-%m-%d %H:%M:%S")
            query += f'\nWHERE "index" >= "{start_timestamp}"'
        async with aiosqlite.connect(self.sql_path) as conn:
            async with conn.execute(query) as cursor:
                data = await cursor.fetchall()
        df = pd.DataFrame(data, columns=["index"] + list(metrics))
        df.set_index("index", inplace=True)
        df.index = pd.to_datetime(df.index, infer_datetime_format=True)
        return df

    async def write(self, df: pd.DataFrame) -> None:
        """Write a DataFrame to the database. This is a write operation, so it will **replace**
        other data.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to write
        """
        # yes im crazy mixing aiosqlite and sqlite3 :aha:
        # writes do block all other operations on the database
        def _write():
            connection = sqlite3.connect(self.sql_path)
            try:
                df.to_sql("main_df", con=connection, if_exists="replace")
                connection.commit()
            finally:
                connection.close()

        await asyncio.get_event_loop().run_in_executor(self.sql_write_executor, _write)

    async def append(self, df: pd.DataFrame) -> None:
        """Append a DataFrame to the database.

        Parameters
        ----------
        df : pd.DataFrame
            DataFrame to append
        """
        # see comments above in write()
        def _append():
            connection = sqlite3.connect(self.sql_path)
            try:
                df.to_sql("main_df", con=connection, if_exists="append")
                connection.commit()
            finally:
                connection.close()

        await asyncio.get_event_loop().run_in_executor(self.sql_write_executor, _append)
