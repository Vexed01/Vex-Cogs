import asyncio
from abc import ABC, ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta

import discord
import pandas
from discord.ext.commands.cog import CogMeta
from redbot.core.bot import Red
from redbot.core.config import Config
from vexcogutils.loop import VexLoop
from vexcogutils.sqldriver import PandasSQLiteDriver


class CompositeMetaClass(CogMeta, ABCMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class MixinMeta(ABC):
    """A wonderful class for typehinting :tada:"""

    bot: Red
    config: Config

    driver: PandasSQLiteDriver
    plot_executor: ThreadPoolExecutor

    loop_meta: VexLoop
    loop: asyncio.Task
    last_loop_time: str

    df_cache: pandas.DataFrame

    cmd_count: int
    msg_count: int

    @abstractmethod
    async def plot(
        self, sr: pandas.Series, delta: timedelta, title: str, ylabel: str
    ) -> discord.File:
        raise NotImplementedError

    @abstractmethod
    async def async_init(self) -> None:
        raise NotImplementedError
