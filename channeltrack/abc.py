import asyncio
from abc import ABC, ABCMeta, abstractmethod
from concurrent.futures import ThreadPoolExecutor
from typing import Any, DefaultDict, Dict, List, Optional

import discord
import pandas
from discord.ext.commands.cog import CogMeta
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config

from channeltrack.table import TableType

from .vexutils.loop import VexLoop
from .vexutils.sqldriver import PandasSQLiteDriver


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

    last_plot_debug: Optional[Dict[str, Any]]

    msg_count: DefaultDict[int, DefaultDict[int, int]]
    cmd_count: DefaultDict[int, DefaultDict[int, int]]

    opted_in_guilds: List[int]

    @abstractmethod
    async def plot(self, df: pandas.DataFrame, ylabel: str, status_colours: bool) -> discord.File:
        raise NotImplementedError

    @abstractmethod
    async def async_init(self) -> None:
        raise NotImplementedError

    @abstractmethod
    def get_table_name(
        self,
        coms_or_msg: TableType,
        *,
        ctx: Optional[commands.Context] = None,
        guild_id: Optional[int] = None,
    ) -> str:
        raise NotImplementedError
