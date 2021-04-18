import json
from typing import Optional

from redbot.core import commands
from redbot.core.bot import Red
from vexcogutils import format_help, format_info

from .errors import NoData
from .utils import get_data, send_output

# dont want to force this as can be a pain on windows
try:
    import pyjson5
except ImportError:
    pass

# NOTE FOR DOCSTRINGS:
# They don't use a normal space character, if you're editing them make sure to copy and paste


class Beautify(commands.Cog):
    """
    Beautify and minify JSON.
    """

    __author__ = "Vexed#3211"
    __version__ = "1.0.2"

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

    async def send_invalid(self, ctx: commands.Context):
        if ctx.author.id in self.bot.owner_ids:  # type:ignore
            try:
                pyjson5
                msg = ""
            except NameError:
                msg = (
                    "\n\n_It looks like you're a bot owner. If you just passed a Python dict, you "
                    f"can run this to let me support them `{ctx.clean_prefix}pipinstall pyjson5` "
                    "You'll need to reload the cog. This might not work on Windows._"
                )
        else:
            msg = ""

        await ctx.send(f"That doesn't look like valid JSON.{msg}")

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

        # preferred parsing, supports python dicts
        try:
            json_pyjson = pyjson5.loads(raw_json)
            if not isinstance(json_pyjson, dict):
                return await self.send_invalid(ctx)
            json_dict = json_pyjson
        except NameError:  # not imported
            # secondary, doesn't support dicts
            try:
                json_dict = json.loads(raw_json)
            except json.JSONDecodeError:
                return await self.send_invalid(ctx)
        except Exception:  # cant just catch pyjson5 as might not be imported
            return await self.send_invalid(ctx)

        beautified = json.dumps(json_dict, indent=4)

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

        # preferred parsing, supports python dicts
        try:
            json_pyjson = pyjson5.loads(raw_json)
            if not isinstance(json_pyjson, dict):
                return await self.send_invalid(ctx)
            json_dict = json_pyjson
        except NameError:  # not imported
            # secondary, doesn't support dicts
            try:
                json_dict = json.loads(raw_json)
            except json.JSONDecodeError:
                return await self.send_invalid(ctx)
        except Exception:  # cant just catch pyjson5 as might not be imported
            return await self.send_invalid(ctx)

        beautified = json.dumps(json_dict)

        await send_output(ctx, beautified)
