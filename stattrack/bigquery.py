from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor

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
            client = bigquery.Client(credentials=self.credentials)
            client.list_datasets()
            client.close()

        try:
            await self.bot.loop.run_in_executor(self.executor, _run)
        except GoogleAuthError:
            raise CredentialsInvalid("Invalid credentials")
