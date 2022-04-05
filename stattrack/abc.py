from __future__ import annotations

import asyncio
from abc import ABC, ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any

import discord
import pandas
from discord.ext.commands.cog import CogMeta
from redbot.core.bot import Red
from redbot.core.config import Config

from .driver import StatTrackSQLiteDriver
from .vexutils.loop import VexLoop


class CompositeMetaClass(CogMeta, ABCMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class MixinMeta(ABC):
    """A wonderful class for typehinting :tada:"""

    bot: Red
    config: Config

    driver: StatTrackSQLiteDriver
    plot_executor: ThreadPoolExecutor

    loop_meta: VexLoop
    loop: asyncio.Task
    last_loop_time: str

    last_plot_debug: dict[str, Any] | None

    cmd_count: int
    msg_count: int

    @abstractmethod
    async def plot(self, df: pandas.DataFrame, ylabel: str, status_colours: bool) -> discord.File:
        raise NotImplementedError

    @abstractmethod
    async def async_init(self) -> None:
        raise NotImplementedError
