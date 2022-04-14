from __future__ import annotations

import asyncio
from abc import ABC, ABCMeta, abstractmethod
from typing import TYPE_CHECKING

import discord
from redbot.core.bot import Red
from redbot.core.commands import CogMeta
from redbot.core.config import Config

from .vexutils.loop import VexLoop

if TYPE_CHECKING:
    from .objects import MessageData, ServerData


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
    async def get_data(self, server: str) -> ServerData:
        raise NotImplementedError()

    @abstractmethod
    async def generate_embed(
        self, data: ServerData | None, config_data: MessageData, maintenance: bool
    ) -> discord.Embed:
        raise NotImplementedError()
