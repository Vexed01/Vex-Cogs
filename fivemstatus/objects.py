from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict


class MessageData(TypedDict):
    server: str
    msg_id: int
    maintenance: bool
    last_known_name: str
    channel_id: int


@dataclass
class ServerData:
    current_users: int | Literal["?"]
    max_users: int
    name: str
    ip: str


class ServerUnreachable(Exception):
    pass
