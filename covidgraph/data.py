from __future__ import annotations

import aiohttp
import pandas as pd
from asyncache import cached
from cachetools import TTLCache

from .abc import MixinMeta
from .errors import CovidError

API_BASE = "https://disease.sh"


class CovidData(MixinMeta):
    """Asynchronously get COVID data."""

    async def get_cases(self, country: str, days: int | None) -> tuple[str, pd.Series]:
        if days is None:
            d = "all"
        else:
            d = str(days)

        if country in ("global", "world", "worldwide"):
            country = "all"

        return await self.get(
            f"{API_BASE}/v3/covid-19/historical/{country}?lastdays={d}",
            extra_key="cases",
            convert_to_daily=True,
        )

    async def get_deaths(self, country: str, days: int | None) -> tuple[str, pd.Series]:
        if days is None:
            d = "all"
        else:
            d = str(days)

        if country in ("global", "world", "worldwide"):
            country = "all"

        return await self.get(
            f"{API_BASE}/v3/covid-19/historical/{country}?lastdays={d}",
            extra_key="deaths",
            convert_to_daily=True,
        )

    async def get_vaccines(self, country: str, days: int | None) -> tuple[str, pd.Series]:
        if days is None:
            d = "all"
        else:
            d = str(days)

        if country in ("global", "world", "worldwide", "all"):
            return await self.get(
                f"{API_BASE}/v3/covid-19/vaccine/coverage?lastdays={d}",
            )

        return await self.get(
            f"{API_BASE}/v3/covid-19/vaccine/coverage/countries/{country}?lastdays={d}",
        )

    @cached(TTLCache(maxsize=64, ttl=3600))  # 1 hour
    async def get(
        self, url: str, extra_key: str | None = None, convert_to_daily: bool = False
    ) -> tuple[str, pd.Series]:
        """Get data from an endpoint as a Series"""
        async with aiohttp.ClientSession() as session:
            resp = await session.get(url)
            if resp.status != 200:
                raise CovidError  # usually invalid country

            data: dict = await resp.json()

        ts_dict = data.get("timeline", data)  # fallback to data if no timeline key

        ts = pd.Series(ts_dict[extra_key] if extra_key else ts_dict)

        ts.index = pd.to_datetime(ts.index, utc=True)

        if convert_to_daily:  # cumulative to daily and ty so much copolit
            ts = ts.diff().dropna()

        return data.get("country", "worldwide"), ts
