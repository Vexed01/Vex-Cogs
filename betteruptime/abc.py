import asyncio
from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING

import pandas
from redbot.core.bot import Red
from redbot.core.commands import CogMeta
from redbot.core.config import Config

from .vexutils.loop import VexLoop

if TYPE_CHECKING:
    from betteruptime.utils import UptimeData


class CompositeMetaClass(CogMeta, ABCMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class MixinMeta(ABC):
    """A wonderful class for typehinting :tada:"""

    bot: Red
    config: Config

    main_loop_meta: VexLoop
    main_loop: asyncio.Task

    last_known_ping: float
    last_ping_change: float

    first_load: float

    cog_loaded_cache: pandas.Series
    connected_cache: pandas.Series

    ready: asyncio.Event

    @abstractmethod
    async def get_data(self, num_days: int) -> "UptimeData":
        raise NotImplementedError

    @abstractmethod
    async def async_init(self) -> None:
        raise NotImplementedError
