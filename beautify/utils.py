from typing import Optional

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, text_to_file

from .errors import AttachmentInvalid, AttachmentPermsError, NoData


def cleanup_json(json: str) -> str:
    """Remove codeblocks, if present."""
    if json.startswith("```") and json.endswith("```"):
        # remove ```json and ``` from start and end
        json = json.strip("```json")
        return json.strip("```")

    elif json.startswith("`") and json.endswith("`"):
        # inline codeblocks
        return json.strip("`")

    return json


async def get_data(ctx: commands.Context, data: Optional[str]) -> str:
    if data is not None:
        return cleanup_json(data)

    # ignores are because message.reference could be none - that is checked
    if ctx.message.attachments:
        attachment = ctx.message.attachments[0]

    elif ctx.message.reference:
        if ctx.message.reference.cached_message.attachments:  # type:ignore
            attachment = ctx.message.reference.cached_message.attachments[0]  # type:ignore

        else:
            content = ctx.message.reference.cached_message.content  # type:ignore
            substrings = content.split("```")
            if len(substrings) == 3:
                return cleanup_json(substrings[1].lstrip("json"))

            await ctx.send_help()
            raise NoData
    else:
        await ctx.send_help()
        raise NoData

    filename = attachment.filename
    if not (filename.endswith(".json") or filename.endswith(".txt")):
        await ctx.send("The file attached must be `.txt` or `.json`,")
        raise AttachmentInvalid

    try:
        att_bytes = await attachment.read()
        if not isinstance(att_bytes, bytes):
            await ctx.send("Something's wrong with that attachment.")
            raise AttachmentInvalid
        return att_bytes.decode()  # hey i dont catch decode errors :aha:
    except discord.HTTPException:
        await ctx.send("I can't access that attachment.")
        raise AttachmentPermsError


async def send_output(ctx: commands.Context, text: str) -> None:
    """Send output as a codeblock or file, depending on file limits. Handles no attachment perm."""
    if len(text) < 1980 and text.count("\n") < 20:  # discord msg limits or long message
        await ctx.send(box(text, lang="json"))
    else:
        if ctx.guild and not ctx.channel.permissions_for(ctx.me).attach_files:  # type:ignore
            return await ctx.send(
                "The output is big and I don't have permission to attach files. "
                "You could try again in my DMs."
            )

        file = text_to_file(text, "output.json")
        await ctx.send("The output is big, so I've attached it as a file.", file=file)
