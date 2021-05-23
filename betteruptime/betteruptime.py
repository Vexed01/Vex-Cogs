import asyncio
import datetime
import logging
from time import time
from typing import Dict, List, Union

import discord
import pandas
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_timedelta, inline, pagify
from vexcogutils import format_help, format_info

from .abc import CompositeMetaClass
from .consts import SECONDS_IN_DAY
from .loop import BULoop

old_ping = None

_log = logging.getLogger("red.vex.betteruptime")


class BetterUptime(commands.Cog, BULoop, metaclass=CompositeMetaClass):
    """
    Replaces the core `uptime` command to show the uptime
    percentage over the last 30 days.

    The cog will need to run for a full 30 days for the full
    data to become available.
    """

    __version__ = "1.5.0"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        default: dict = {}  # :dict is pointless but makes mypy happy
        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(cog_loaded=default)
        self.config.register_global(connected=default)
        self.config.register_global(first_load=None)

        self.last_known_ping = 0.0
        self.last_ping_change = 0.0

        self.first_load = 0.0

        self.cog_loaded_cache = pandas.Series({})
        self.connected_cache = pandas.Series({})

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
        self.main_loop.cancel()
        self.conf_loop.cancel()

        # it should be pretty safe to assume the bot's online when unloading
        # and if not it's only a few seconds of "mistake"
        if self.main_loop_meta.next_iter:  # could be None
            try:
                until_next = (
                    self.main_loop_meta.next_iter - datetime.datetime.now(datetime.timezone.utc)
                ).total_seconds()  # assume up to now was uptime because the command was invoked
                utcdatetoday = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

                self.cog_loaded_cache[utcdatetoday] += until_next
                self.connected_cache[utcdatetoday] += time() - self.last_ping_change
            except Exception:  # TODO: pos remove
                pass

        asyncio.create_task(self.write_to_config())

        global old_ping
        if old_ping:
            try:
                self.bot.remove_command("ping")
            except Exception:
                pass
            self.bot.add_command(old_ping)

        try:
            self.bot.remove_dev_env_value("bu")
        except Exception:
            pass

    # =============================================================================================

    @commands.command(hidden=True)
    async def betteruptimeinfo(self, ctx: commands.Context):
        loops = [self.main_loop_meta, self.conf_loop_meta]
        await ctx.send(await format_info(self.qualified_name, self.__version__, loops=loops))

    @commands.command(name="uptime")
    async def uptime_command(self, ctx: commands.Context, num_days: int = 30):
        """
        Get [botname]'s uptime percent over the last 30 days, and when I was last restarted.

        The default value for `num_days` is `30`. You can put `0` days for all-time data.
        Otherwise, it needs to be `5` or more.
        """
        # START OF CODE FROM RED'S CORE uptime COMMAND
        since = ctx.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or "Less than one second."
        description = f"Been up for: **{uptime_str}** (since {since} UTC)."
        # END

        if num_days == 0:
            num_days = 9999  # this works, trust me
        elif num_days < 5:
            return await ctx.send("The minimum number of days is `5`.")

        if not await ctx.embed_requested():
            # TODO: implement non-embed version
            return await ctx.send(description)

        while self.connected_cache.empty:
            await asyncio.sleep(0.2)  # max wait is 2 if command triggerd straight after cog load

        embed = discord.Embed(description=description, colour=await ctx.embed_colour())
        now = datetime.datetime.utcnow()
        if self.main_loop_meta.next_iter is None:
            until_next = 0.0
        else:
            try:
                until_next = (
                    self.main_loop_meta.next_iter - datetime.datetime.now(datetime.timezone.utc)
                ).total_seconds()  # assume up to now was uptime because the command was invoked
            except Exception:  # TODO: pos remove
                until_next = 0.0

        seconds_cog_loaded = 15 - until_next
        seconds_connected = time() - self.last_ping_change

        ts_cl = self.cog_loaded_cache.copy(deep=True)
        ts_con = self.connected_cache.copy(deep=True)
        conf_first_loaded = datetime.datetime.utcfromtimestamp(self.first_load)

        expected_index = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today(),
            normalize=True,
        )

        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_since_midnight = float((now - midnight).seconds)
        if len(expected_index) >= num_days:
            expected_index = expected_index[: (num_days - 1)]
            seconds_data_collected = float(
                (SECONDS_IN_DAY * (num_days - 1)) + seconds_since_midnight
            )
        else:
            seconds_data_collected = float((len(expected_index) - 1) * SECONDS_IN_DAY)

            if conf_first_loaded > midnight:  # cog was first loaded today
                seconds_data_collected += (now - conf_first_loaded).total_seconds()
            else:
                seconds_data_collected += seconds_since_midnight

        ts_cl = ts_cl.reindex(expected_index)
        ts_con = ts_con.reindex(expected_index)
        seconds_cog_loaded += ts_cl.sum()
        seconds_connected += ts_con.sum()

        main_downtime = (
            humanize_timedelta(seconds=seconds_data_collected - seconds_connected) or "none"
        )
        dt_due_to_net = (
            humanize_timedelta(seconds=seconds_cog_loaded - seconds_connected) or "none"
        )

        # if downtime is under the loop frequency we can just assume it's full uptime... this
        # mainly fixes irregularities near first load
        if seconds_data_collected - seconds_cog_loaded <= 16:  # 15 second loop
            seconds_cog_loaded = seconds_data_collected
        if (
            seconds_data_collected - seconds_connected <= 60
        ):  # for my my experience heartbeats are ~41 secs
            seconds_connected = seconds_data_collected

        uptime_cog_loaded = format(
            round((seconds_cog_loaded / seconds_data_collected) * 100, 2), ".2f"
        )
        uptime_connected = format(
            round((seconds_connected / seconds_data_collected) * 100, 2), ".2f"
        )

        botname = ctx.me.name
        embed.add_field(
            name="Uptime (connected to Discord):", value=inline(f"{uptime_connected}%")
        )
        embed.add_field(name=f"Uptime ({botname} ready):", value=inline(f"{uptime_cog_loaded}%"))

        if (
            seconds_data_collected - seconds_connected > 60
        ):  # dont want to include stupidly small downtime
            downtime_info = f"`{main_downtime}`\n`{dt_due_to_net}` of this was due network issues."
            embed.add_field(name="Downtime:", value=downtime_info, inline=False)

        seconds_since_first_load = (datetime.datetime.utcnow() - conf_first_loaded).total_seconds()
        content: Union[None, str]
        if seconds_since_first_load < 60 * 15:  # 15 mins
            content = "Data tracking only started in the last few minutes. Data may be inaccurate."
        elif len(expected_index) == 1:
            content = None
            embed.set_footer(text="Data is only for today.")
        else:
            content = None
            embed.set_footer(text=f"Data is for the last {len(expected_index)} days, and today.")

        await ctx.send(content, embed=embed)

    @commands.command()
    async def downtime(self, ctx: commands.Context, num_days: int = 30):
        """
        Check [botname] downtime over the last 30 days.

        The default value for `num_days` is `30`. You can put `0` days for all-time data.
        Otherwise, it needs to be `5` or more.
        """
        conf_cog_loaded = self.cog_loaded_cache
        conf_connected = self.connected_cache
        conf_first_loaded = datetime.datetime.utcfromtimestamp(self.first_load)

        expected_index = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today() - datetime.timedelta(days=1),
            normalize=True,
        )

        if len(expected_index) > num_days:
            expected_index = expected_index[: (num_days - 1)]

        msg = ""

        for date in expected_index:
            cog_loaded = conf_cog_loaded.get(date, 0.0)
            cog_unloaded = SECONDS_IN_DAY - cog_loaded
            connected = conf_connected.get(date, 0.0)
            not_connected = SECONDS_IN_DAY - connected

            if not_connected > 120:  # from my experience heartbeats are ~41 secs
                dt_net = cog_loaded - connected
                if dt_net < 45:  # heartbeats are ~41
                    dt_net = 0.0
                main_downtime = humanize_timedelta(seconds=cog_unloaded) or "none"
                dt_due_to_net = humanize_timedelta(seconds=dt_net) or "none"

                msg += (
                    f"\n**{date}**: `{main_downtime}`, of which `{dt_due_to_net}` was due to "
                    "network issues."
                )

        if not msg:
            await ctx.send(
                "It looks like there's been no recorded downtime.\n_This excludes any downtime "
                "today._"
            )
        else:
            full = (
                "_Timezone: UTC, date format: Year-Month-Day_\n_This excludes any "
                f"downtime today._\n\n{msg}"
            )
            paged = pagify(full, page_length=1000)
            await ctx.send_interactive(paged)

    @commands.command(name="updev", hidden=True)
    async def _dev_com(self, ctx: commands.Context):

        now = datetime.datetime.utcnow()

        if not self.main_loop_meta.next_iter:
            until_next = 0.0
        else:
            try:
                until_next = (
                    self.main_loop_meta.next_iter - datetime.datetime.now(datetime.timezone.utc)
                ).total_seconds()  # assume up to now was uptime because the command was invoked
            except Exception:  # TODO: pos remove
                until_next = 0.0

        seconds_cog_loaded = until_next
        seconds_connected = time() - self.last_ping_change

        ts_cl = self.cog_loaded_cache.copy(deep=True)
        ts_con = self.connected_cache.copy(deep=True)
        conf_first_loaded = datetime.datetime.utcfromtimestamp(self.first_load)

        expected_index = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today(),
            normalize=True,
        )

        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_since_midnight = (now - midnight).seconds
        seconds_data_collected = float((len(expected_index) - 1) * SECONDS_IN_DAY)

        if conf_first_loaded > midnight:  # cog was first loaded today
            seconds_data_collected += (now - conf_first_loaded).total_seconds()
        else:
            seconds_data_collected += seconds_since_midnight

        ts_cl = ts_cl.reindex(expected_index)
        ts_con = ts_con.reindex(expected_index)
        seconds_cog_loaded += ts_cl.sum()
        seconds_connected += ts_con.sum()

        await ctx.send(
            f"The cog was first loaded `{(now - conf_first_loaded).total_seconds()}` seconds ago\n"
            f"Seconds connected: `{seconds_connected}`\n"
            f"Seconds cog loaded: `{seconds_cog_loaded}`\n"
            f"Seconds of collection: `{seconds_data_collected}`\n"
        )

    @commands.command(name="uploop", hidden=True)
    async def _dev_loop(self, ctx: commands.Context):
        main = self.main_loop_meta.get_debug_embed()
        conf = self.conf_loop_meta.get_debug_embed()

        await ctx.send(embed=main)
        await ctx.send(embed=conf)


def setup(bot: Red) -> None:
    global old_ping
    old_ping = bot.get_command("uptime")
    if old_ping:
        bot.remove_command(old_ping.name)

    bu = BetterUptime(bot)
    bot.add_cog(bu)
