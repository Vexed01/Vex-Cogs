import asyncio
from abc import ABC, ABCMeta

import pandas
from redbot.core.bot import Red
from redbot.core.commands import CogMeta
from redbot.core.config import Config
from vexcogutils.loop import VexLoop


class CompositeMetaClass(CogMeta, ABCMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class MixinMeta(ABC):
    """A wonderful class for typehinting :tada:"""

    bot: Red
    config: Config

    conf_loop_meta: VexLoop
    conf_loop: asyncio.Task
    main_loop_meta: VexLoop
    main_loop: asyncio.Task

    last_known_ping: float
    last_ping_change: float

    fist_load: float

    cog_loaded_cache: pandas.Series
    connected_cache: pandas.Series

    ready: bool
