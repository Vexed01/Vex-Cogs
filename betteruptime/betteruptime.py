import logging

import pandas
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import pagify
from vexcogutils import format_help, format_info

from betteruptime.commands import BUCommands

from .abc import CompositeMetaClass
from .loop import BULoop
from .utils import Utils

old_uptime = None

_log = logging.getLogger("red.vex.betteruptime")


# THIS COG WILL BE REWRITTEN/REFACTORED AT SOME POINT (#23)


class BetterUptime(commands.Cog, BUCommands, BULoop, Utils, metaclass=CompositeMetaClass):
    """
    Replaces the core `uptime` command to show the uptime
    percentage over the last 30 days.

    The cog will need to run for a full 30 days for the full
    data to become available.
    """

    __version__ = "2.0.4"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        default: dict = {}
        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(cog_loaded=default)
        self.config.register_global(connected=default)
        self.config.register_global(first_load=None)

        self.last_known_ping = 0.0
        self.last_ping_change = 0.0

        self.first_load = 0.0

        self.cog_loaded_cache = pandas.Series(dtype="object")  # dtype="object is to suppresses
        self.connected_cache = pandas.Series(dtype="object")  # deprecation warn
        self.unload_write = True

        self.main_loop = None
        self.main_loop_meta = None

        self.ready = False

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

    def cog_unload(self) -> None:
        _log.info("BetterUptime is now unloading. Cleaning up...")

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

    # =============================================================================================

    @commands.command(hidden=True)
    async def betteruptimeinfo(self, ctx: commands.Context):
        loops = [self.main_loop_meta] if self.main_loop_meta else []
        await ctx.send(await format_info(self.qualified_name, self.__version__, loops=loops))

    @commands.command(name="updev", hidden=True)
    async def _dev_com(self, ctx: commands.Context):
        await ctx.send_interactive(pagify(str(await self.get_data(9000))), box_lang="")

    @commands.command(name="uploop", hidden=True)
    async def _dev_loop(self, ctx: commands.Context):
        assert self.main_loop_meta is not None
        await ctx.send(embed=self.main_loop_meta.get_debug_embed())


def setup(bot: Red) -> None:
    global old_uptime
    old_uptime = bot.get_command("uptime")
    if old_uptime:
        bot.remove_command(old_uptime.name)

    bu = BetterUptime(bot)
    bot.add_cog(bu)
