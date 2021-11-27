from abc import ABC, ABCMeta
from concurrent.futures.thread import ThreadPoolExecutor

from redbot.core.bot import Red
from redbot.core.commands import CogMeta


class CompositeMetaClass(CogMeta, ABCMeta):
    """
    This allows the metaclass used for proper type detection to
    coexist with discord.py's metaclass
    """


class MixinMeta(ABC):
    """A wonderful class for typehinting :tada:"""

    bot: Red
    executor: ThreadPoolExecutor
