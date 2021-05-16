import asyncio
from abc import ABC, ABCMeta
from typing import Optional

import pandas
from discord.ext.commands.cog import CogMeta
from redbot.core.bot import Red
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

    loop_meta: Optional[VexLoop]
    loop: Optional[asyncio.Task]
    last_loop_time: Optional[float]

    df_cache: Optional[pandas.DataFrame]

    cmd_count: int
    msg_count: int
