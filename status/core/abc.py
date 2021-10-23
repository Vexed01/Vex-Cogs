import asyncio
from abc import ABC, ABCMeta, abstractmethod
from typing import Optional

from aiohttp import ClientSession
from discord.ext.commands.cog import CogMeta
from redbot.core.bot import Red
from redbot.core.config import Config
from vexcogutils.loop import VexLoop

from status.core.statusapi import StatusAPI
from status.objects import (
    ConfigWrapper,
    LastChecked,
    ServiceCooldown,
    ServiceRestrictionsCache,
    UsedFeeds,
)


class CompositeMetaClass(CogMeta, ABCMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class MixinMeta(ABC):
    """A wonderful class for typehinting :tada:"""

    bot: Red
    config: Config
    config_wrapper: ConfigWrapper

    loop_meta: VexLoop
    loop: asyncio.Task
    actually_send: bool

    used_feeds: UsedFeeds
    last_checked: LastChecked
    service_cooldown: ServiceCooldown
    service_restrictions_cache: ServiceRestrictionsCache

    session: ClientSession
    statusapi: StatusAPI

    ready: bool

    @abstractmethod
    async def get_initial_data(self) -> None:
        raise NotImplementedError()
