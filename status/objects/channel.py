from __future__ import annotations

from dataclasses import dataclass

import discord

from ..core import MODES_LITERAL


@dataclass
class ChannelData:
    channel: discord.TextChannel | discord.Thread
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
