import asyncio
import os
import sys

import pandas
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.data_manager import cog_data_path
from redbot.core.utils.chat_formatting import pagify

from .abc import CompositeMetaClass
from .commands import BUCommands
from .loop import BULoop
from .slash import BUSlash
from .utils import Utils
from .vexutils import format_help, format_info, get_vex_logger
from .vexutils.chat import humanize_bytes
from .vexutils.meta import out_of_date_check

old_uptime = None
log = get_vex_logger(__name__)


# THIS COG WILL BE REWRITTEN/REFACTORED AT SOME POINT (#23)


class BetterUptime(commands.Cog, BUCommands, BUSlash, BULoop, Utils, metaclass=CompositeMetaClass):
    """
    Replaces the core `uptime` command to show the uptime
    percentage over the last 30 days.

    The cog will need to run for a full 30 days for the full
    data to become available.
    """

    __version__ = "2.1.4"
    __author__ = "@vexingvexed"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        default: dict = {}
        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(
            version=1, cog_loaded=default, connected=default, first_load=None
        )
        self.last_known_ping = 0.0
        self.last_ping_change = 0.0

        self.first_load = 0.0

        self.cog_loaded_cache = pandas.Series(dtype="float64")
        self.connected_cache = pandas.Series(dtype="float64")
        self.unload_write = True

        self.ready = asyncio.Event()
        self.conf_ready = asyncio.Event()

        try:
            self.bot.add_dev_env_value("bu", lambda _: self)
        except Exception:
            pass

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    async def cog_load(self) -> None:
        await self.setup_loop()

    async def cog_unload(self) -> None:
        log.info("BetterUptime is now unloading. Cleaning up...")

        if self.main_loop:
            self.main_loop.cancel()

        global old_uptime
        if old_uptime:
            try:
                self.bot.remove_command("uptime")
            except Exception:
                pass
            self.bot.add_command(old_uptime)

        try:
            self.bot.remove_dev_env_value("bu")
        except Exception:
            pass

    @commands.command(hidden=True)
    async def betteruptimeinfo(self, ctx: commands.Context):
        loops = [self.main_loop_meta] if self.main_loop_meta else []
        disk_usage = os.path.getsize(cog_data_path(self) / "settings.json")
        memory_usage = sys.getsizeof(self.connected_cache) + sys.getsizeof(self.cog_loaded_cache)

        await ctx.send(
            await format_info(ctx, self.qualified_name, self.__version__, loops=loops)
            + f"\nMemory usage (cache size): {humanize_bytes(memory_usage)}"
            + f"\nDisk usage (database): {humanize_bytes(disk_usage)}"
        )

    @commands.is_owner()
    @commands.command(name="updev", hidden=True)
    async def _dev_com(self, ctx: commands.Context):
        await ctx.send_interactive(pagify(str(await self.get_data(9000))), box_lang="")

    @commands.is_owner()
    @commands.command(name="uploop", hidden=True)
    async def _dev_loop(self, ctx: commands.Context):
        await ctx.send(embed=self.main_loop_meta.get_debug_embed())


async def setup(bot: Red) -> None:
    global old_uptime
    old_uptime = bot.get_command("uptime")
    if old_uptime:
        bot.remove_command(old_uptime.name)

    cog = BetterUptime(bot)
    await out_of_date_check("betteruptime", cog.__version__)
    await bot.add_cog(cog)
