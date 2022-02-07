from __future__ import annotations

from dataclasses import dataclass

from discord import TextChannel

from ..core import MODES_LITERAL


@dataclass
class ChannelData:
    channel: TextChannel
    mode: MODES_LITERAL
    webhook: bool
    embed: bool
    edit_id: dict[str, int]


class InvalidChannel(Exception):
    pass


class NotFound(InvalidChannel):
    pass


class NoPermission(InvalidChannel):
    pass


class CogDisabled(InvalidChannel):
    pass
