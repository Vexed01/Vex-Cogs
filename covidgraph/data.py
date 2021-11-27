from typing import Optional, Tuple

import aiohttp
import pandas as pd
from asyncache import cached
from cachetools import TTLCache

from .abc import MixinMeta
from .errors import CovidError

API_BASE = "https://disease.sh"


class CovidData(MixinMeta):
    """Asynchronously get COVID data."""

    async def get_cases(self, country: str, days: Optional[int]) -> Tuple[str, pd.Series]:
        if days is None:
            d = "all"
        else:
            d = str(days)

        return await self.get(
            f"{API_BASE}/v3/covid-19/historical/{country}?lastdays={d}",
            extra_key="cases",
            convert_to_daily=True,
        )

    async def get_deaths(self, country: str, days: Optional[int]) -> Tuple[str, pd.Series]:
        if days is None:
            d = "all"
        else:
            d = str(days)

        return await self.get(
            f"{API_BASE}/v3/covid-19/historical/{country}?lastdays={d}",
            extra_key="deaths",
            convert_to_daily=True,
        )

    async def get_vaccines(self, country: str, days: Optional[int]) -> Tuple[str, pd.Series]:
        if days is None:
            d = "all"
        else:
            d = str(days)

        return await self.get(
            f"{API_BASE}/v3/covid-19/vaccine/coverage/countries/{country}?lastdays={d}",
        )

    @cached(TTLCache(maxsize=64, ttl=3600))  # 1 hour
    async def get(
        self, url: str, extra_key: Optional[str] = None, convert_to_daily: bool = False
    ) -> Tuple[str, pd.Series]:
        """Get data from an endpoint as a Series"""
        print(url)
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url)
            if resp.status != 200:
                raise CovidError  # usually invalid country

            data: dict = await resp.json()

        if extra_key:
            sr = pd.Series(data["timeline"][extra_key])
        else:
            sr = pd.Series(data["timeline"])

        sr.index = pd.to_datetime(sr.index, utc=True)  # type:ignore

        if convert_to_daily:  # cumulative to daily and ty so much copolit
            sr = sr.diff().dropna()

        return data.get("country", ""), sr
