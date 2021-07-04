import asyncio
from abc import ABC, ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from typing import Optional

import discord
import pandas
from discord.ext.commands.cog import CogMeta
from redbot.core.bot import Red
from redbot.core.config import Config
from vexcogutils.loop import VexLoop

from stattrack.driver import StatTrackDriver


class CompositeMetaClass(CogMeta, ABCMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class MixinMeta(ABC):
    """A wonderful class for typehinting :tada:"""

    bot: Red
    config: Config

    driver: StatTrackDriver
    plot_executor: ThreadPoolExecutor

    loop_meta: Optional[VexLoop]
    loop: Optional[asyncio.Task]
    last_loop_time: Optional[float]

    df_cache: Optional[pandas.DataFrame]

    cmd_count: int
    msg_count: int

    @abstractmethod
    async def plot(
        self, sr: pandas.Series, delta: timedelta, title: str, ylabel: str
    ) -> discord.File:
        raise NotImplementedError
