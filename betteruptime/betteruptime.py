import asyncio
import datetime
import logging
from time import time
from typing import Dict, Union

import discord
import pandas
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_timedelta, inline
from vexcogutils import format_help, format_info

from .consts import CROSS, SECONDS_IN_DAY
from .loop import BetterUptimeLoop

# only used in dev com so dont want is as a requirement in info.json
try:
    from tabulate import tabulate
except ImportError:
    pass


old_ping = None

_log = logging.getLogger("red.vexed.betteruptime")


class BetterUptime(commands.Cog, BetterUptimeLoop):
    """
    Replaces the core `uptime` command to show the uptime
    percentage over the last 30 days.

    The cog will need to run for a full 30 days for the full
    data to become available.
    """

    __version__ = "1.2.2"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        default: dict = {}  # :dict is pointless but maked mypy happy
        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(cog_loaded=default)
        self.config.register_global(connected=default)
        self.config.register_global(first_load=None)

        self.last_known_ping = 0.0
        self.last_ping_change = 0.0

        self.first_load = 0.0

        self.cog_loaded_cache: Dict[str, float] = {}
        self.connected_cache: Dict[str, float] = {}

        self.recent_load = True

        try:
            self.bot.add_dev_env_value("bu", lambda x: self)
        except Exception:
            pass

    def cog_unload(self) -> None:
        _log.info("BetterUptime is now unloading. Cleaning up...")
        self.uptime_loop.cancel()
        self.config_loop.cancel()

        # it should be pretty safe to assume the bot's online when unloading
        # and if not it's only a few seconds of "mistake"
        try:
            until_next = (
                self.uptime_loop.next_iteration - datetime.datetime.now(datetime.timezone.utc)
            ).total_seconds()  # assume up to now was uptime because the command was invoked
            utcdatetoday = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")

            self.cog_loaded_cache[utcdatetoday] += until_next
            self.connected_cache[utcdatetoday] += time() - self.last_ping_change
        except Exception:
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
        loops = {
            "Main loop": self.uptime_loop.is_running(),
            "Config loop": self.config_loop.is_running(),
        }
        main = format_info(self.qualified_name, self.__version__, extras=loops)

        extra = (
            f"\nNote: these **will** show `{CROSS}` for a few more seconds until the cog is fully "
            "ready."
            if self.recent_load
            else ""
        )

        await ctx.send(f"{main}{extra}")

    @commands.command(name="uptime")
    async def uptime_command(self, ctx: commands.Context):
        """Get [botname]'s uptime percent over the last 30 days, and when I was last restarted."""
        # START OF CODE FROM RED'S CORE uptime COMMAND
        since = ctx.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or "Less than one second."
        description = f"Been up for: **{uptime_str}** (since {since} UTC)."
        # END

        if not await ctx.embed_requested():
            # TODO: implement non-embed version
            return await ctx.send(description)

        while not self.connected_cache:
            await asyncio.sleep(0.2)  # max wait it 2 if command triggerd straight after cog load

        embed = discord.Embed(description=description, colour=await ctx.embed_colour())
        now = datetime.datetime.utcnow()

        try:
            until_next = (
                self.uptime_loop.next_iteration - datetime.datetime.now(datetime.timezone.utc)
            ).total_seconds()  # assume up to now was uptime because the command was invoked
        except Exception:
            until_next = 0

        seconds_cog_loaded = 15 - until_next
        seconds_connected = time() - self.last_ping_change

        conf_cog_loaded = self.cog_loaded_cache
        conf_connected = self.connected_cache
        conf_first_loaded = datetime.datetime.utcfromtimestamp(self.first_load)

        dates_to_look_for = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today(),
            normalize=True,
        ).tolist()

        if len(dates_to_look_for) > 30:
            dates_to_look_for = dates_to_look_for[:29]

        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_since_midnight = float((now - midnight).seconds)
        if len(dates_to_look_for) >= 30:
            seconds_data_collected = float((SECONDS_IN_DAY * 29) + seconds_since_midnight)
        else:
            seconds_data_collected = float((len(dates_to_look_for) - 1) * SECONDS_IN_DAY)

            if conf_first_loaded > midnight:  # cog was first loaded today
                seconds_data_collected += (now - conf_first_loaded).total_seconds()
            else:
                seconds_data_collected += seconds_since_midnight

        for date in dates_to_look_for:
            date = date.strftime("%Y-%m-%d")
            seconds_cog_loaded += conf_cog_loaded.get(date, 0)
            seconds_connected += conf_connected.get(date, 0)

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
            seconds_data_collected - seconds_connected <= 45
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
        elif len(dates_to_look_for) - 1 == 0:
            content = None
            embed.set_footer(text="Data is only for today.")
        else:
            content = None
            embed.set_footer(text=f"Data is for the last {len(dates_to_look_for)} days.")

        await ctx.send(content, embed=embed)

    @commands.command()
    async def downtime(self, ctx: commands.Context):
        """Check [botname] downtime over the last 30 days."""

        conf_cog_loaded = self.cog_loaded_cache
        conf_connected = self.connected_cache
        conf_first_loaded = datetime.datetime.utcfromtimestamp(self.first_load)

        dates_to_look_for = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today() - datetime.timedelta(days=1),
            normalize=True,
        ).tolist()

        if len(dates_to_look_for) > 30:
            dates_to_look_for = dates_to_look_for[:29]

        msg = ""

        for date in dates_to_look_for:
            date = date.strftime("%Y-%m-%d")

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
            await ctx.send(
                f"{msg}\n\n_Timezone: UTC, date format: Year-Month-Day_\n_This excludes any "
                "downtime today._"
            )

    @commands.command(name="updev", hidden=True)
    async def _dev_com(self, ctx: commands.Context):

        dates_to_look_for = pandas.date_range(
            end=datetime.datetime.today(), periods=30, tz=datetime.timezone.utc
        ).tolist()

        now = datetime.datetime.utcnow()

        try:
            until_next = (
                self.uptime_loop.next_iteration - datetime.datetime.now(datetime.timezone.utc)
            ).total_seconds()  # assume up to now was uptime because the command was invoked
        except Exception:
            until_next = 0

        seconds_cog_loaded = until_next
        seconds_connected = time() - self.last_ping_change

        conf_cog_loaded = self.cog_loaded_cache
        conf_connected = self.connected_cache
        conf_first_loaded = datetime.datetime.utcfromtimestamp(self.first_load)

        dates_to_look_for = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today(),
            normalize=True,
        ).tolist()

        if len(dates_to_look_for) > 30:
            dates_to_look_for = dates_to_look_for[:29]

        midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
        seconds_since_midnight = (now - midnight).seconds
        if len(dates_to_look_for) >= 30:
            seconds_data_collected = float((SECONDS_IN_DAY * 29) + seconds_since_midnight)
        else:
            seconds_data_collected = float((len(dates_to_look_for) - 1) * SECONDS_IN_DAY)

            if conf_first_loaded > midnight:  # cog was first loaded today
                seconds_data_collected += (now - conf_first_loaded).total_seconds()
            else:
                seconds_data_collected += seconds_since_midnight

        for date in dates_to_look_for:
            date = date.strftime("%Y-%m-%d")
            seconds_cog_loaded += conf_cog_loaded.get(date, 0)
            seconds_connected += conf_connected.get(date, 0)

        await ctx.send(
            f"The cog was first loaded `{(now - conf_first_loaded).total_seconds()}` seconds ago\n"
            f"Seconds connected: `{seconds_connected}`\n"
            f"Seconds cog loaded: `{seconds_cog_loaded}`\n"
            f"Seconds of collection: `{seconds_data_collected}`\n"
        )

    @commands.command(name="uploop", hidden=True)
    async def _dev_loop(self, ctx: commands.Context):
        try:
            tabulate
        except NameError:
            return await ctx.send(
                "Tabulate must be installed to use this command (`[p]pipinstall tabulate`)"
            )

        uptime_loop = self.uptime_loop

        uptime_data1 = [
            ["next_iteration", uptime_loop.next_iteration],
            ["_last_iteration", uptime_loop._last_iteration],
            ["is_running", uptime_loop.is_running()],
            ["failed", uptime_loop.failed()],
            ["_last_iteration_failed", uptime_loop._last_iteration_failed],
            ["current_loop", uptime_loop.current_loop],
        ]

        uptime_data2 = [
            ["Seconds until next", uptime_loop.next_iteration.timestamp() - time()],
            ["Seconds since last", time() - uptime_loop._last_iteration.timestamp()],
        ]

        config_loop = self.config_loop

        config_data1 = [
            ["next_iteration", config_loop.next_iteration],
            ["_last_iteration", config_loop._last_iteration],
            ["is_running", config_loop.is_running()],
            ["failed", config_loop.failed()],
            ["_last_iteration_failed", config_loop._last_iteration_failed],
            ["current_loop", config_loop.current_loop],
        ]

        config_data2 = [
            ["Seconds until next", config_loop.next_iteration.timestamp() - time()],
            ["Seconds since last", time() - config_loop._last_iteration.timestamp()],
        ]

        uptime_loop = f"{box(tabulate(uptime_data1))}\n{box(tabulate(uptime_data2))}"
        config_loop = f"{box(tabulate(config_data1))}\n{box(tabulate(config_data2))}"

        e = discord.Embed(title="Loop info")
        e.add_field(name="Uptime loop", value=uptime_loop, inline=False)
        e.add_field(name="Config loop", value=config_loop, inline=False)
        await ctx.send(embed=e)


def setup(bot: Red) -> None:
    apc = BetterUptime(bot)
    global old_ping
    old_ping = bot.get_command("uptime")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(apc)
