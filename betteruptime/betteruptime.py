import asyncio
import datetime
import logging
from time import time
from typing import Dict

import discord
import pandas
from discord.ext import tasks
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_timedelta, inline

# only used in dev com so dont want is as a requirement in info.json
try:
    from tabulate import tabulate
except ImportError:
    tabulate = None

INF = float("inf")

SECONDS_IN_DAY = 60 * 60 * 24

old_ping = None

log = logging.getLogger("red.vexed.betteruptime")


class BetterUptime(commands.Cog):
    """
    Replaces the core `uptime` command to show the uptime
    percentage over the last 30 days.

    The cog will need to run for a full 30 days for the full
    data to become available.
    """

    __version__ = "1.0.2"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        docs = "This cog has docs! Check them out at\nhttps://vex-cogs.readthedocs.io/en/latest/cogs/betteruptime.html"
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**\n{docs}"
        # adding docs link here so doesn't show up in auto generated docs

    def __init__(self, bot: Red):
        self.bot = bot

        default = {}
        self.config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_global(cog_loaded=default)
        self.config.register_global(connected=default)
        self.config.register_global(first_load=None)

        self.last_known_ping = 0.0
        self.last_ping_change = 0.0

        self.cog_loaded_cache: Dict[str, int] = {}
        self.connected_cache: Dict[str, int] = {}

        asyncio.create_task(self._async_init())

        try:
            self.bot.add_dev_env_value("bu", lambda x: self)
        except Exception:
            pass

    async def _async_init(self):
        await self.bot.wait_until_red_ready()

        self.last_known_ping: float = self.bot.latency
        self.last_ping_change = time()

        log.debug("Waiting a bit to allow for previous unload to clean up (assuming reload)...")
        await asyncio.sleep(2)  # if reloading wait for unloading to be able to clean up properly
        log.debug("Setting up...")
        self.cog_loaded_cache = await self.config.cog_loaded()
        self.connected_cache = await self.config.connected()

        # want to make sure its actually written
        if await self.config.first_load() is None:
            await self.config.first_load.set(time())

        log.info("BetterUptime has been initialized. Waiting for some uptime to occur before starting loops...")

        await asyncio.sleep(15)
        self.uptime_loop.start()

        await asyncio.sleep(1)
        self.config_loop.start()

        log.info("BetterUptime is now fully running.")

    def cog_unload(self):
        log.info("BetterUptime is now unloading. Cleaning up...")
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
            self.connected_cache += time() - self.last_ping_change
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

    async def write_to_config(self, final=False):
        if self.cog_loaded_cache:  # dont want to write if the cache is empty
            await self.config.cog_loaded.set(self.cog_loaded_cache)
        if self.connected_cache:
            await self.config.connected.set(self.connected_cache)

        if final:
            log.info("BetterUptime is fully unloaded.")
        else:
            log.debug("Wrote local cache to config.")

    @tasks.loop(seconds=15)  # 15 seconds is basically guaranteed to catch all, heartbeats are ~41 secs atm
    async def uptime_loop(self):
        log.debug("Loop started")
        utcdatetoday = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        utcdateyesterday = datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=1)
        utcdateyesterday = utcdateyesterday.strftime("%Y-%m-%d")

        # === COG LOADED ===

        # im sure the indentation could be reduced here
        try:
            self.cog_loaded_cache[utcdatetoday] += 15
        except KeyError:
            # we need to top up both today and yesterday with their respective amounts

            now = datetime.datetime.now(datetime.timezone.utc)
            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            just_after_midnight = (now - midnight).seconds

            if just_after_midnight > 15:
                self.cog_loaded_cache[utcdatetoday] = 15
            else:
                just_before_midnight = 15 - just_after_midnight
                self.cog_loaded_cache[utcdatetoday] = just_after_midnight

                try:
                    self.cog_loaded_cache[utcdateyesterday] += just_before_midnight
                except KeyError:
                    pass

        # === CONNECTED ===
        # bit of background info here: the latency is updated every heartbeat and if the heartbeat fails the latency
        # is infinity (INF)

        current_latency = self.bot.latency

        # the latency has changed and it's not infinity (couldn't connect)
        if current_latency != self.last_known_ping:
            if current_latency != INF:
                since_last = time() - self.last_ping_change

                try:
                    self.connected_cache[utcdatetoday] += since_last
                except KeyError:
                    # we need to top up both today and yesterday with their respective amounts

                    now = datetime.datetime.now(datetime.timezone.utc)
                    midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
                    just_after_midnight = (now - midnight).seconds

                    if just_after_midnight > since_last:
                        self.connected_cache[utcdatetoday] = since_last
                    else:
                        just_before_midnight = since_last - just_after_midnight
                        self.connected_cache[utcdatetoday] = just_after_midnight

                        try:
                            self.connected_cache[utcdateyesterday] += just_before_midnight
                        except KeyError:
                            pass
            self.last_known_ping = self.connected_cache
            self.last_ping_change = time()

    @tasks.loop(seconds=60)
    async def config_loop(self):
        await self.write_to_config()

    # ============================================================================================

    @commands.command(name="uptime")
    async def uptime_command(self, ctx: commands.Context):
        """Get [botname]'s uptime percent over the last 30 days, and when I was last restarted."""
        # START OF CODE FROM RED'S CORE uptime COMMAND
        since = ctx.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or "Less than one second."
        description = f"Been up for: **{uptime_str}** (since {since} UTC)."
        # END

        if not await ctx.embed_requested() or self.connected_cache is None:
            # TODO: implement non-embed version
            return await ctx.send(description)

        embed = discord.Embed(description=description, colour=await ctx.embed_colour())
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
        conf_first_loaded = datetime.datetime.utcfromtimestamp(await self.config.first_load())

        full_days_loaded = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today() - datetime.timedelta(days=1),
        ).tolist()

        if len(full_days_loaded) >= 30:
            seconds_data_collected = SECONDS_IN_DAY * 30
        else:
            seconds_data_collected = len(full_days_loaded) * SECONDS_IN_DAY

            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_since_midnight = (now - midnight).seconds
            if conf_first_loaded > midnight:  # cog was first loaded today
                seconds_data_collected += (now - conf_first_loaded).total_seconds()
            else:
                seconds_data_collected += seconds_since_midnight

        for date in dates_to_look_for:
            date = date.strftime("%Y-%m-%d")
            seconds_cog_loaded += conf_cog_loaded.get(date, 0)
            seconds_connected += conf_connected.get(date, 0)

        downtime_cog_loaded = (
            humanize_timedelta(seconds=seconds_data_collected - (seconds_cog_loaded - seconds_connected)) or "none"
        )
        downtime_connected = humanize_timedelta(seconds=seconds_data_collected - seconds_connected) or "none"

        # if downtime is under the loop frequency we can just assume it's full uptime... this mainly fixes
        # irregularities near first load
        if seconds_data_collected - seconds_cog_loaded <= 16:  # 15 second loop
            seconds_cog_loaded = seconds_data_collected
        if seconds_data_collected - seconds_connected <= 45:  # for my my experience heartbeats are ~41 secs
            seconds_connected = seconds_data_collected

        uptime_cog_loaded = format(round((seconds_cog_loaded / seconds_data_collected) * 100, 2), ".2f")
        uptime_connected = format(round((seconds_connected / seconds_data_collected) * 100, 2), ".2f")

        botname = ctx.me.name
        embed.add_field(name="Uptime (connected to Discord):", value=inline(f"{uptime_connected}%"))
        embed.add_field(name=f"Uptime ({botname} ready):", value=inline(f"{uptime_cog_loaded}%"))

        if seconds_data_collected - seconds_connected > 120:  # dont want to include stupidly small downtime
            downtime_info = f"`{downtime_connected}`\n`{downtime_cog_loaded}` of this was due network issues"
            embed.add_field(name="Downtime:", value=downtime_info, inline=False)

        seconds_since_first_load = (datetime.datetime.utcnow() - conf_first_loaded).total_seconds()
        if seconds_since_first_load < 60 * 15:  # 15 mins
            content = "Data tracking only started in the last few minutes. Data may be inaccurate."
        elif len(full_days_loaded) == 0:
            content = None
            embed.set_footer(text=f"Data is only for today.")
        else:
            content = None
            embed.set_footer(text=f"Data is for the last {len(full_days_loaded) + 1} days.")

        await ctx.send(content, embed=embed)

    @commands.command()
    async def downtime(self, ctx: commands.Context):
        """Check [botname] downtime over the last 30 days."""
        conf_cog_loaded = self.cog_loaded_cache
        conf_connected = self.connected_cache
        conf_first_loaded = datetime.datetime.utcfromtimestamp(await self.config.first_load())

        full_days_loaded = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today() - datetime.timedelta(days=1),
        ).tolist()

        msg = ""

        for date in full_days_loaded:
            date = date.strftime("%Y-%m-%d")
            cog_unloaded = SECONDS_IN_DAY - conf_cog_loaded.get(date, 0)
            not_connected = SECONDS_IN_DAY - conf_connected.get(date, 0)

            if not_connected > 120:
                c_l_hum = humanize_timedelta(seconds=cog_unloaded) or "none"
                c_hum = humanize_timedelta(seconds=not_connected) or "none"

                msg += f"\n**{date}**: `{c_hum}`, of which `{c_l_hum}` was due to me not being ready."

        if not msg:
            await ctx.send("It looks like there's been no recorded downtime.")
        else:
            await ctx.send(
                f"{msg}\n\n_Timezone: UTC, date format: Year-Month-Day_\n_This excludes any downtime today._"
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

        seconds_cog_loaded = 15 - until_next
        seconds_connected = time() - self.last_ping_change

        conf_cog_loaded = self.cog_loaded_cache
        conf_connected = self.connected_cache
        conf_first_loaded = datetime.datetime.utcfromtimestamp(await self.config.first_load())

        full_days_loaded = pandas.date_range(
            start=conf_first_loaded + datetime.timedelta(days=1),
            end=datetime.datetime.today() - datetime.timedelta(days=1),
        ).tolist()

        if len(full_days_loaded) >= 30:
            seconds_data_collected = SECONDS_IN_DAY * 30
        else:
            seconds_data_collected = len(full_days_loaded) * SECONDS_IN_DAY

            midnight = now.replace(hour=0, minute=0, second=0, microsecond=0)
            seconds_since_midnight = (now - midnight).seconds
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
            f"Seconds cog loaded: `{seconds_cog_loaded}`"
        )

    @commands.command(name="uploop", hidden=True)
    async def _dev_loop(self, ctx: commands.Context):
        if tabulate is None:
            return await ctx.send("Tabulate must be installed to use this command (`[p]pipinstall tabulate`)")

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


def setup(bot: Red):
    apc = BetterUptime(bot)
    global old_ping
    old_ping = bot.get_command("uptime")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(apc)
