from __future__ import annotations

import json
from typing import Optional

import discord
from redbot.core import app_commands, commands
from redbot.core.bot import Red

from .errors import JSONDecodeError, NoData
from .utils import decode_json, get_data, send_output
from .vexutils import format_help, format_info, get_vex_logger

log = get_vex_logger(__name__)

# dont want to force this as can be a pain on windows
try:
    import pyjson5  # noqa  # import otherwise unused

    use_pyjson = True
    log.debug("pyjson5 available")
except ImportError:
    use_pyjson = False
    log.debug("pyjson5 not available")


class Beautify(commands.Cog):
    """
    Beautify and minify JSON.

    This cog has two commands, `[p]beautify` and `[p]minify`. Both of which behave in similar ways.

    They are very flexible and accept inputs in many ways,
    for example replies or uploading - or just simply putting it after the command.

    """

    __author__ = "Vexed#0714"
    __version__ = "1.1.3"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def beautifyinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    async def send_invalid(
        self, ctx: commands.Context | None = None, interaction: discord.Interaction | None = None
    ):
        author = ctx.author if ctx else interaction.user
        if author.id in self.bot.owner_ids:  # type:ignore
            if use_pyjson:
                msg = ""
            else:
                msg = (
                    "\n\n_It looks like you're a bot owner. If you just passed a Python dict, you "
                    f"can run this to let me support them `{ctx.clean_prefix if ctx else '/'}"
                    "pipinstall pyjson5` "
                    "You'll need to reload the cog. This might not work on Windows._"
                )
        else:
            msg = ""

        if ctx:
            await ctx.send(f"That doesn't look like valid JSON.{msg}")
        elif interaction:
            await interaction.response.send_message(f"That doesn't look like valid JSON.{msg}")
        else:
            raise ValueError("No context or interaction passed.")

    @commands.command(name="beautify")
    async def com_beautify(self, ctx: commands.Context, *, data: Optional[str]):
        """
        Beautify some JSON.

        This command accepts it in a few forms.

        1. Upload the JSON as a file (it can be .txt or .json)
          - Note that if you upload multiple files I will only scan the first one
        2. Paste the JSON in the command
          - You can send it raw, in inline code or a codeblock
        3. Reply to a message with JSON
          - I will search for attachments and any codeblocks in the message

        **Examples:**
        - `[p]beautify {"1": "One", "2": "Two"}`
        - `[p]beautify` (with file uploaded)
        - `[p]beautify` (while replying to a messsage)
        """
        try:
            raw_json = await get_data(ctx, data)
        except NoData:
            return

        try:
            json_dict, changed_input = decode_json(raw_json)
        except JSONDecodeError:
            return await self.send_invalid(ctx)

        beautified = json.dumps(json_dict, indent=4)

        await send_output(beautified, changed_input, ctx=ctx)

    @commands.command(name="minify")
    async def com_minify(self, ctx: commands.Context, *, data: Optional[str]):
        """
        Minify some JSON.

        This command accepts it in a few forms.

        1. Upload the JSON as a file (it can be .txt or .json)
          - Note that if you upload multiple files I will only scan the first one
        2. Paste the JSON in the command
          - You can send it raw, in inline code or a codeblock
        3. Reply to a message with JSON
          - I will search for attachments and any codeblocks in the message

        **Examples:**
        - `[p]minify {"1": "One", "2": "Two"}`
        - `[p]minify` (with file uploaded)
        - `[p]minify` (while replying to a messsage)
        """
        try:
            raw_json = await get_data(ctx, data)
        except NoData as e:
            log.debug("No data found for msg %s", ctx.message.id, exc_info=e)
            return

        try:
            json_dict, changed_input = decode_json(raw_json)
        except JSONDecodeError:
            await self.send_invalid(ctx)
            return

        beautified = json.dumps(json_dict)

        await send_output(beautified, changed_input, ctx=ctx)

    @app_commands.describe(paste="Paste JSON data", attachment="Upload a JSON file")
    @app_commands.command(name="beautify")
    async def beautify_slash(
        self,
        interaction: discord.Interaction,
        *,
        paste: Optional[str],
        attachment: Optional[discord.Attachment],
    ):
        """Beautify some JSON. Choose either to paste data or upload an attachment."""
        if attachment:
            raw_json = (await attachment.read()).decode("utf-8")
        else:
            raw_json = paste

        if not raw_json:
            await interaction.response.send_message(
                "No data found. Make sure to either paste data or upload a file."
            )
            return

        try:
            json_dict, changed_input = decode_json(raw_json)
        except JSONDecodeError:
            await self.send_invalid(interaction=interaction)
            return

        beautified = json.dumps(json_dict, indent=4)

        await send_output(beautified, changed_input, interaction=interaction)

    @app_commands.describe(paste="Paste JSON data", attachment="Upload a JSON file")
    @app_commands.command(name="minify")
    async def minify_slash(
        self,
        interaction: discord.Interaction,
        *,
        paste: Optional[str],
        attachment: Optional[discord.Attachment],
    ):
        """Minify some JSON. Choose either to paste data or upload an attachment."""
        if attachment:
            raw_json = (await attachment.read()).decode("utf-8")
        else:
            raw_json = paste

        if not raw_json:
            await interaction.response.send_message(
                "No data found. Make sure to either paste data or upload a file."
            )
            return

        try:
            json_dict, changed_input = decode_json(raw_json)
        except JSONDecodeError:
            await self.send_invalid(interaction=interaction)
            return

        beautified = json.dumps(json_dict)

        await send_output(beautified, changed_input, interaction=interaction)
