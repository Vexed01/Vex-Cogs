import asyncio
import json
import logging
from typing import Optional

import sentry_sdk
import vexcogutils
from redbot.core import commands
from redbot.core.bot import Red
from vexcogutils import format_help, format_info
from vexcogutils.meta import out_of_date_check

from .errors import JSONDecodeError, NoData
from .utils import decode_json, get_data, send_output

# dont want to force this as can be a pain on windows
try:
    import pyjson5  # noqa  # import otherwise unused

    use_pyjson = True
except ImportError:
    use_pyjson = False

log = logging.getLogger("red.vex.beautify")

# NOTE FOR DOCSTRINGS:
# They don't use a normal space character, if you're editing them make sure to copy and paste


class Beautify(commands.Cog):
    """
    Beautify and minify JSON.

    This cog has two commands, `[p]beautify` and `[p]minify`. Both of which behave in similar ways.

    They are very flexible and accept inputs in many ways,
    for example replies or uploading - or just simply putting it after the command.

    """

    __author__ = "Vexed#3211"
    __version__ = "1.1.2"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.bot.loop.create_task(self.async_init())

        # =========================================================================================
        # NOTE: IF YOU ARE EDITING MY COGS, PLEASE ENSURE SENTRY IS DISBALED BY FOLLOWING THE INFO
        # IN async_init(...) BELOW (SENTRY IS WHAT'S USED FOR TELEMETRY + ERROR REPORTING)
        self.sentry_hub: Optional[sentry_sdk.Hub] = None
        # =========================================================================================

    async def async_init(self):
        await out_of_date_check("beautify", self.__version__)

        # =========================================================================================
        # TO DISABLE SENTRY FOR THIS COG (EG IF YOU ARE EDITING THIS COG) EITHER DISABLE SENTRY
        # WITH THE `[p]vextelemetry` COMMAND, OR UNCOMMENT THE LINE BELOW, OR REMOVE IT COMPLETELY:
        # return

        while vexcogutils.sentryhelper.ready is False:
            await asyncio.sleep(0.1)

        await vexcogutils.sentryhelper.maybe_send_owners("beautify")

        if vexcogutils.sentryhelper.sentry_enabled is False:
            log.debug("Sentry detected as disabled.")
            return

        log.debug("Sentry detected as enabled.")
        self.sentry_hub = await vexcogutils.sentryhelper.get_sentry_hub(
            "beautify", self.__version__
        )
        # =========================================================================================

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.bot.on_command_error(ctx, error, unhandled_by_cog=True)  # type:ignore

        if self.sentry_hub is None:  # sentry disabled
            return

        with self.sentry_hub:
            sentry_sdk.add_breadcrumb(
                category="command", message="Command used was " + ctx.command.qualified_name
            )
            try:
                e = error.original  # type:ignore
            except AttributeError:
                e = error
            sentry_sdk.capture_exception(e)
            log.debug("Above exception successfully reported to Sentry")

    def cog_unload(self):
        if self.sentry_hub and self.sentry_hub.client:
            self.sentry_hub.end_session()
            self.sentry_hub.client.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def beautifyinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(self.qualified_name, self.__version__))

    async def send_invalid(self, ctx: commands.Context):
        if ctx.author.id in self.bot.owner_ids:  # type:ignore
            if use_pyjson:
                msg = ""
            else:
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

        await send_output(ctx, beautified, changed_input)

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

        **Examples:**
            - `[p]minify {"1": "One", "2": "Two"}`
            - `[p]minify` (with file uploaded)
            - `[p]minify` (while replying to a messsage)
        """
        try:
            raw_json = await get_data(ctx, data)
        except NoData:
            return

        try:
            json_dict, changed_input = decode_json(raw_json)
        except JSONDecodeError:
            return await self.send_invalid(ctx)

        beautified = json.dumps(json_dict)

        await send_output(ctx, beautified, changed_input)
