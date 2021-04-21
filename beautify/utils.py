import json
import logging
from typing import NamedTuple, Optional

import discord
from redbot.core import commands
from redbot.core.utils.chat_formatting import box, text_to_file

from .errors import AttachmentInvalid, AttachmentPermsError, JSONDecodeError, NoData

# dont want to force this as can be a pain on windows
try:
    import pyjson5

    use_pyjson = True
except ImportError:
    use_pyjson = False

log = logging.getLogger("red.vexed.beautify")


def cleanup_json(json: str) -> str:
    """Remove codeblocks, if present."""
    if json.startswith("```") and json.endswith("```"):
        # remove ```json and ``` from start and end
        json = json.strip("```json")
        json = json.strip("```py")  # not documented but want to accept it as well
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
                return cleanup_json(substrings[1].lstrip("json").lstrip("py"))

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


class DecodeReturn(NamedTuple):
    data: dict
    changed_input: bool


def decode_json(str_json: str) -> DecodeReturn:
    # quick and dirty...
    if "False" in str_json or "True" in str_json or "None" in str_json:
        changed_input = True

        str_json = str_json.replace("False", "false").replace("True", "true")
        str_json = str_json.replace("None", "null")
    else:
        changed_input = False

    # preferred parsing, supports single quotes and other more "versatile" formats
    if use_pyjson:
        try:
            json_pyjson = pyjson5.loads(str_json)

            if isinstance(json_pyjson, dict):
                return DecodeReturn(json_pyjson, changed_input)
        except Exception:  # cant just catch pyjson5 as might not be imported... sad
            log.debug(
                "Exception caught. If the bellow information doesn't mention 'pyjson5' please "
                "report this to Vexed.",
                exc_info=True,
            )

    # secondary, less support but can pick up some other stuff
    try:
        return DecodeReturn(json.loads(str_json), changed_input)
    except json.JSONDecodeError:
        raise JSONDecodeError()


async def send_output(ctx: commands.Context, text: str, changed_input: bool) -> None:
    """Send output as a codeblock or file, depending on file limits. Handles no attachment perm."""
    if changed_input:
        extra = (
            "_Note: I have had to change the input due to parsing limitations. Any of the "
            "following anywhere in the data may have been made lowercase: `true` or `false` and "
            "any occurrence of `None` has been replaced with `null`. This is regardless of where "
            "they are in the data._\n\n"
        )
    else:
        extra = ""

    if (len(text) + len(extra)) < 1980 and text.count("\n") < 20:  # limit long messages
        await ctx.send(extra + box(text, lang="json"))
    else:
        if ctx.guild and not ctx.channel.permissions_for(ctx.me).attach_files:  # type:ignore
            return await ctx.send(
                f"{extra}The output is big and I don't have permission to attach files. "
                "You could try again in my DMs."
            )

        file = text_to_file(text, "output.json")
        await ctx.send("The output is big, so I've attached it as a file.", file=file)
