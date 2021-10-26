import asyncio
from abc import ABC, ABCMeta, abstractmethod

from redbot.core.bot import Red
from redbot.core.commands import CogMeta
from redbot.core.config import Config

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

    loop_meta: VexLoop
    loop: asyncio.Task

    @abstractmethod
    async def maybe_migrate(self) -> None:
        raise NotImplementedError()
