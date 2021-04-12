import json
from ast import literal_eval
from typing import Optional

from redbot.core import commands
from redbot.core.bot import Red
from vexcogutils import format_help
from vexcogutils.utils import format_info

from .errors import NoData
from .utils import get_data, send_output

# NOTE FOR DOCSTRINGS:
# They don't use a normal space character, if you're editing them make sure to copy and paste


class Beautify(commands.Cog):
    """
    Beautify and minify JSON.
    """

    __author__ = "Vexed#3211"
    __version__ = "1.0.1"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def beautifyinfo(self, ctx: commands.Context):
        await ctx.send(format_info(self.qualified_name, self.__version__))

    @commands.command(name="beautify")
    async def com_beautify(self, ctx: commands.Context, *, data: Optional[str]):
        """
        Beautify some JSON.

        This command accepts it in a few forms.

        1. Upload the JSON as a file (it can be .txt or .json)
        ​ ​ ​ ​ - Note that if you upload multiple files I will only scan the first one
        2. Paste the JSON in the command
        ​ ​ ​ ​ - You send it raw, in inline code or a codeblock
        ​3. Reply to a message with JSON
        ​ ​ ​ ​ - I will search for attachments and any codeblocks in the message
        """
        try:
            raw_json = await get_data(ctx, data)
        except NoData:
            return

        # using literal_eval to support both valid JSON (") and python dicts (')
        # this is PERFECTLY SAFE and will not execute arbitrary code (look at the docstring)
        try:
            json_literal = literal_eval(raw_json)
            if not isinstance(json_literal, dict):
                raise ValueError

        except (ValueError, SyntaxError):  # these are main ones literal_eval raises, may be more
            return await ctx.send("That doesn't look like valid JSON.")

        beautified = json.dumps(json_literal, indent=4)

        await send_output(ctx, beautified)

    @commands.command(name="minify")
    async def com_minify(self, ctx: commands.Context, *, data: Optional[str]):
        """
        Minify some JSON.

        This command accepts it in a few forms.

        1. Upload the JSON as a file (it can be .txt or .json)
        ​ ​ ​ ​ - Note that if you upload multiple files I will only scan the first one
        2. Paste the JSON in the command
        ​ ​ ​ ​ - You send it raw, in inline code or a codeblock
        ​3. Reply to a message with JSON
        ​ ​ ​ ​ - I will search for attachments and any codeblocks in the message
        """
        try:
            raw_json = await get_data(ctx, data)
        except NoData:
            return

        # using literal_eval to support both valid JSON (") and python dicts (')
        # this is PERFECTLY SAFE and will not execute arbitrary code (look at the docstring)
        try:
            json_literal = literal_eval(raw_json)
            if not isinstance(json_literal, dict):
                raise ValueError

        except (ValueError, SyntaxError):  # these are main ones literal_eval raises, may be more
            return await ctx.send("That doesn't look like valid JSON.")

        beautified = json.dumps(json_literal)

        await send_output(ctx, beautified)
