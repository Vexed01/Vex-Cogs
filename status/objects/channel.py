from typing import Dict

from discord import TextChannel

from status.core.consts import MODES_LITERAL


class ChannelData:
    def __init__(
        self,
        channel: TextChannel,
        mode: MODES_LITERAL,
        webhook: bool,
        edit_id: Dict[str, int],
        embed: bool,
    ):
        self.channel = channel
        self.mode = mode
        self.webhook = webhook
        self.edit_id = edit_id
        self.embed = embed

    def __repr__(self):
        return (
            f'ChannelSettings(channel={self.channel}, mode="{self.mode}", '
            f"webhook={self.webhook}, edit_id={self.edit_id}, embed={self.embed})"
        )


class InvalidChannel(Exception):
    pass


class NotFound(InvalidChannel):
    pass


class NoPermission(InvalidChannel):
    pass


class CogDisabled(InvalidChannel):
    pass
