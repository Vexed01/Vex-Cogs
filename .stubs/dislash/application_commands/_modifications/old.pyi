"""
This type stub file was generated by pyright.
"""

from discord import Message

__all__ = (
    "create_message_with_components",
    "send_with_components",
    "edit_with_components",
    "MessageWithComponents",
)

def create_message_with_components(self, *, channel, data): ...
def send_message(
    self,
    channel_id,
    content,
    *,
    tts=...,
    embed=...,
    nonce=...,
    allowed_mentions=...,
    message_reference=...,
    components=...,
): ...
def send_files(
    self,
    channel_id,
    *,
    files,
    content=...,
    tts=...,
    embed=...,
    nonce=...,
    allowed_mentions=...,
    message_reference=...,
    components=...,
): ...
async def send_with_components(
    messageable,
    content=...,
    *,
    tts=...,
    embed=...,
    components=...,
    file=...,
    files=...,
    delete_after=...,
    nonce=...,
    allowed_mentions=...,
    reference=...,
    mention_author=...,
): ...
async def edit_with_components(message, **fields): ...

class MessageWithComponents(Message):
    def __init__(self, *, state, channel, data) -> None: ...
    def __repr__(self): ...
