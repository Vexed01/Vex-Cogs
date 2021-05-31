from dataclasses import dataclass
from typing import Dict

from discord import TextChannel

from status.core import MODES_LITERAL


@dataclass
class ChannelData:
    channel: TextChannel
    mode: MODES_LITERAL
    webhook: bool
    edit_id: Dict[str, int]
    embed: bool


class InvalidChannel(Exception):
    pass


class NotFound(InvalidChannel):
    pass


class NoPermission(InvalidChannel):
    pass


class CogDisabled(InvalidChannel):
    pass
