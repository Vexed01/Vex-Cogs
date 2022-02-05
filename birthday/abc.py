from __future__ import annotations

import asyncio
from abc import ABC, ABCMeta, abstractmethod
from typing import Coroutine

import discord
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
    role_manager: asyncio.Task

    ready: asyncio.Event

    coro_queue: asyncio.Queue[Coroutine]

    @abstractmethod
    async def check_if_setup(self, guild: discord.Guild) -> bool:
        raise NotImplementedError

    @abstractmethod
    async def birthday_loop(self) -> None:
        raise NotImplementedError

    @abstractmethod
    async def birthday_role_manager(self) -> None:
        raise NotImplementedError
