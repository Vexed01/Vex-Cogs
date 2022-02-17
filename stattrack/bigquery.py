from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

import pandas as pd
from google.auth.exceptions import GoogleAuthError
from google.cloud import bigquery
from google.oauth2 import service_account
from redbot.core import Config
from redbot.core.bot import Red


class BQError(Exception):
    pass


class CredentialsNotFound(BQError):
    pass


class CredentialsInvalid(BQError):
    pass


class PandasBigQuery:
    def __init__(self, bot: Red, config: Config) -> None:
        self.bot = bot
        self.config = config

        self.executor = ThreadPoolExecutor(4, "stattrack_bigquery")

        self.credentials: service_account.Credentials | None = None

    async def verify_credentials(self) -> None:
        """Verify credentials are valid with a simple query.

        Set the credentials by setting `bigquery.credentials` to a dict.

        If credentials are valid, this will return None.

        Raises
        ------
        CredentialsNotFound
            No credentials found
        CredentialsInvalid
            Invalid credentials
        """
        if self.credentials is None:
            raise CredentialsNotFound("No credentials found")

        def _run():
            client = bigquery.Client(
                project=self.credentials.project_id, credentials=self.credentials  # type:ignore
            )
            client.list_datasets()
            client.close()

        try:
            await self.bot.loop.run_in_executor(self.executor, _run)
        except GoogleAuthError:
            raise CredentialsInvalid("Invalid credentials")

    async def write(self, df: pd.DataFrame) -> None:
        """Write a StatTrack dataframe to BigQuery.

        Parameters
        ----------
        df : DataFrame
            DataFrame to append

        Raises
        ------
        CredentialsNotFound
            No credentials found
        CredentialsInvalid
            Invalid credentials
        """
        if self.credentials is None:
            raise CredentialsNotFound("No credentials found")

        def _run():
            df.reset_index(inplace=True)
            df.rename(columns={"index": "date"}, inplace=True)
            df.to_gbq(
                "stattrack.main_df",
                project_id=self.credentials.project_id,  # type:ignore
                credentials=self.credentials,
                if_exists="replace",
                progress_bar=False,
            )

        try:
            await self.bot.loop.run_in_executor(self.executor, _run)
        except GoogleAuthError:
            raise CredentialsInvalid("Invalid credentials")

    async def append(self, df: pd.DataFrame):
        """Append a StatTrack DataFrame to BigQuery

        Parameters
        ----------
        df : DataFrame
            DataFrame to append
        """
        if self.credentials is None:
            raise CredentialsNotFound("No credentials found")

        def _run():
            df.reset_index(inplace=True)
            df.rename(columns={"index": "date"}, inplace=True)
            df.to_gbq(
                "stattrack.main_df",
                project_id=self.credentials.project_id,  # type:ignore
                credentials=self.credentials,
                if_exists="append",
                progress_bar=False,
            )

        try:
            await self.bot.loop.run_in_executor(self.executor, _run)
        except GoogleAuthError:
            raise CredentialsInvalid("Invalid credentials")

    async def get_tables(self) -> list:
        """Get a list of tables from BigQuery

        Raises
        ------
        CredentialsNotFound
            No credentials found
        CredentialsInvalid
            Invalid credentials
        """
        if self.credentials is None:
            raise CredentialsNotFound("No credentials found")

        def _run() -> list:
            assert self.credentials is not None
            client = bigquery.Client(credentials=self.credentials)
            try:
                return list(client.list_tables("stattrack"))
            finally:
                client.close()

        try:
            tables = await self.bot.loop.run_in_executor(self.executor, _run)
        except GoogleAuthError:
            raise CredentialsInvalid("Invalid credentials")

        return tables
