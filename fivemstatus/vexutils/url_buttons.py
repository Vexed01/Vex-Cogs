from typing import Optional

import discord
from discord.http import Route
from redbot.core.bot import Red


class URLButton:
    def __init__(self, label: str, url: str) -> None:
        if not isinstance(label, str):
            raise TypeError("Label must be a string")
        if not isinstance(url, str):
            raise TypeError("URL must be a string")

        self.label = label
        self.url = url

    def to_dict(self) -> dict:
        return {
            "label": self.label,
            "style": 5,
            "type": 2,
            "url": self.url,
        }


async def send_message(
    bot: Red,
    channel_id: int,
    *,
    content: Optional[str] = None,
    embed: Optional[discord.Embed] = None,
    file: Optional[discord.File] = None,
    url_button: Optional[URLButton] = None,
):
    """Send a message with a URL button, with pure dpy 1.7."""
    payload = {}

    if content:
        payload["content"] = content

    if embed:
        payload["embed"] = embed.to_dict()

    if url_button:
        payload["components"] = [{"type": 1, "components": [url_button.to_dict()]}]  # type:ignore

    if file:
        form = [
            {
                "name": "file",
                "value": file.fp,
                "filename": file.filename,
                "content_type": "application/octet-stream",
            },
            {"name": "payload_json", "value": discord.utils.to_json(payload)},
        ]

        r = Route("POST", "/channels/{channel_id}/messages", channel_id=channel_id)
        await bot._connection.http.request(r, form=form, files=[file])

    else:
        r = Route("POST", "/channels/{channel_id}/messages", channel_id=channel_id)
        await bot._connection.http.request(r, json=payload)
