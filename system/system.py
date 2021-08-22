import asyncio
import datetime
import logging
from typing import List, Optional

import discord
import psutil
import sentry_sdk
import vexcogutils
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_timedelta
from vexcogutils import format_help, format_info
from vexcogutils.meta import out_of_date_check

from .backend import (
    box,
    get_cpu,
    get_disk,
    get_mem,
    get_net,
    get_proc,
    get_red,
    get_sensors,
    get_uptime,
    get_users,
    up_for,
)
from .command import DynamicHelp

log = logging.getLogger("red.vex.system")
UNAVAILABLE = "\N{CROSS MARK} This command isn't available on your system."
ZERO_WIDTH = "\u200b"

# cspell:ignore psutil shwtemp tablefmt sfan suser sdiskpart sdiskusage fstype proc procs


class System(commands.Cog):
    """
    Get system metrics.

    Most commands work on all OSes or omit certian information.
    See the help for individual commands for detailed limitations.
    """

    __version__ = "1.3.8"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        asyncio.create_task(self.async_init())

        # =========================================================================================
        # NOTE: IF YOU ARE EDITING MY COGS, PLEASE ENSURE SENTRY IS DISBALED BY FOLLOWING THE INFO
        # IN async_init(...) BELOW (SENTRY IS WHAT'S USED FOR TELEMETRY + ERROR REPORTING)
        self.sentry_hub: Optional[sentry_sdk.Hub] = None
        # =========================================================================================

    async def async_init(self):
        await out_of_date_check("system", self.__version__)

        # =========================================================================================
        # TO DISABLE SENTRY FOR THIS COG (EG IF YOU ARE EDITING THIS COG) EITHER DISABLE SENTRY
        # WITH THE `[p]vextelemetry` COMMAND, OR UNCOMMENT THE LINE BELOW, OR REMOVE IT COMPLETELY:
        # return

        while vexcogutils.sentryhelper.ready is False:
            await asyncio.sleep(0.1)

        if vexcogutils.sentryhelper.sentry_enabled is False:
            log.debug("Sentry detected as disabled.")
            return

        log.debug("Sentry detected as enabled.")
        self.sentry_hub = await vexcogutils.sentryhelper.get_sentry_hub("system", self.__version__)
        # =========================================================================================

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.bot.on_command_error(ctx, error, unhandled_by_cog=True)

        if self.sentry_hub is None:  # sentry disabled
            return

        with self.sentry_hub:
            sentry_sdk.add_breadcrumb(
                category="command", message="Command used was " + ctx.command.qualified_name
            )
            sentry_sdk.capture_exception(error.original)  # type:ignore
            log.debug("Above exception successfully reported to Sentry")

    def cog_unload(self):
        if self.sentry_hub:
            self.sentry_hub.end_session()
            self.sentry_hub.client.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def systeminfo(self, ctx: commands.Context):
        await ctx.send(await format_info(self.qualified_name, self.__version__))

    def finalise_embed(self, e: discord.Embed) -> discord.Embed:
        """Make embeds look nicer - limit to two columns and set the footer to boot time"""
        # needed because otherwise they are otherwise too squashed together so tabulate breaks
        # doesn't look great on mobile but is fully bearable, more than ugly text wrapping

        # oh, don't mention the ugly code please :P
        # it works...
        emb = e.to_dict()

        fields = emb["fields"]
        if len(fields) > 2:  # needs multi rows
            data: List[list] = []
            temp = []
            for field in fields:
                temp.append(field)
                if len(temp) == 2:
                    data.append(temp)
                    temp = []
            if len(temp) != 0:  # clear up stragglers
                data.append(temp)

            empty_field = {"inline": True, "name": ZERO_WIDTH, "value": ZERO_WIDTH}
            fields = []
            for row in data:
                while len(row) < 3:
                    row.append(empty_field)
                fields.extend(row)  # type:ignore

        # else it's 2 or less columns so doesn't need special treatment
        emb["fields"] = fields
        e = discord.Embed.from_dict(emb)

        # and footer is just a nice touch, thanks max for the idea of uptime there
        sys_uptime = humanize_timedelta(seconds=up_for())
        bot_uptime = humanize_timedelta(timedelta=datetime.datetime.utcnow() - self.bot.uptime)

        e.set_footer(text=f"System uptime: {sys_uptime}\nBot uptime: {bot_uptime}")

        return e

    @commands.is_owner()
    @commands.group()
    async def system(self, ctx: commands.Context):
        """
        Get information about your system metrics.

        Most commands work on all OSes or omit certian information.
        See the help for individual commands for detailed limitations.
        """

    @system.command(name="cpu", cls=DynamicHelp, supported_sys=True)  # all systems
    async def system_cpu(self, ctx: commands.Context):
        """
        Get metrics about the CPU.

        This will show the CPU usage as a percent for each core, and frequency depending on
        platform.
        It will also show the time spent idle, user and system as well as uptime.

        Platforms: Windows, Linux, Mac OS
        Note: CPU frequency is nominal and overall on Windows and Mac OS,
        on Linux it's current and per-core.
        """
        async with ctx.typing():
            data = await get_cpu()
            percent = data["percent"]
            time = data["time"]
            freq = data["freq"]
            if await ctx.embed_requested():
                embed = discord.Embed(title="CPU Metrics", colour=await ctx.embed_colour())
                embed.add_field(name="CPU Usage", value=box(percent))
                embed.add_field(name="CPU Times", value=box(time))
                extra = data["freq_note"]
                embed.add_field(name=f"CPU Frequency{extra}", value=box(freq))
                await ctx.send(embed=self.finalise_embed(embed))
            else:
                msg = "**CPU Metrics**\n"
                to_box = f"CPU Usage\n{percent}\n"
                to_box += f"CPU Times\n{time}\n"
                extra = data["freq_note"]
                to_box += f"CPU Frequency{extra}\n{freq}\n"
                msg += box(to_box)
                await ctx.send(msg)

    @system.command(
        name="mem", aliases=["memory", "ram"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_mem(self, ctx: commands.Context):
        """
        Get infomation about memory usage.

        This will show memory available as a percent, memory used and available as well
        as the total amount. Data is provided for both physical and SWAP RAM.

        Platforms: Windows, Linux, Mac OS
        """
        data = await get_mem()
        physical = data["physical"]
        swap = data["swap"]
        if await ctx.embed_requested():
            embed = discord.Embed(title="Memory", colour=await ctx.embed_colour())
            embed.add_field(name="Physical Memory", value=box(physical))
            embed.add_field(name="SWAP Memory", value=box(swap))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Memory**\n"
            to_box = f"Physical Memory\n{physical}\n"
            to_box += f"SWAP Memory\n{swap}\n"
            msg += box(to_box)
            await ctx.send(msg)

    @system.command(
        name="sensors",
        aliases=["temp", "temperature", "fan", "fans"],
        cls=DynamicHelp,
        supported_sys=psutil.LINUX,
    )
    async def system_sensors(self, ctx: commands.Context, fahrenheit: bool = False):
        """
        Get sensor metrics.

        This will return any data about temperature and fan sensors it can find.
        If there is no name for an individual sensor, it will use the name of the
        group instead.

        Platforms: Linux
        """
        if not psutil.LINUX:
            return await ctx.send(UNAVAILABLE)

        data = await get_sensors(fahrenheit)
        temp = data["temp"]
        fans = data["fans"]
        if await ctx.embed_requested():
            embed = discord.Embed(title="Sensors", colour=await ctx.embed_colour())
            embed.add_field(name="Temperatures", value=box(temp))
            embed.add_field(name="Fans", value=box(fans))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Temperature**\n"
            to_box = f"Temperatures\n{temp}\n"
            to_box += f"Fans\n{fans}\n"
            msg += box(to_box)
            await ctx.send(msg)

    @system.command(name="users", cls=DynamicHelp, supported_sys=True)  # all systems
    async def system_users(self, ctx: commands.Context):
        """
        Get information about logged in users.

        This will show the user name, what terminal they're logged in at,
        and when they logged in.

        Platforms: Windows, Linux, Mac OS
        Note: PID is not available on Windows. Terminal is usually `Unknown`
        """
        embed = await ctx.embed_requested()
        data = await get_users(embed)

        if embed:
            embed = discord.Embed(title="Users", colour=await ctx.embed_colour())
            if not data:
                embed.add_field(
                    name="No one's logged in",
                    value=(
                        "If you're expecting data here, you're probably using WSL or other "
                        "virtualisation technology"
                    ),
                )

            for name, userdata in data.items():
                embed.add_field(name=name, value=box(userdata))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Users**\n"
            if not data:
                data = {
                    "No one's logged in": (
                        "If you're expecting data here, you're probably using WSL or other "
                        "virtualisation technology"
                    )
                }
            to_box = "".join(f"{name}\n{userdata}" for name, userdata in data.items())
            msg += box(to_box)
            await ctx.send(msg)

    @system.command(
        name="disk", aliases=["df"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_disk(self, ctx: commands.Context):
        """
        Get infomation about disks connected to the system.

        This will show the space used, total space, filesystem and
        mount point (if you're on Linux make sure it's not potentially
        sensitive if running the command a public space).

        Platforms: Windows, Linux, Mac OS
        Note: Mount point is basically useless on Windows as it's the
        same as the drive name, though it's still shown.
        """
        embed = await ctx.embed_requested()
        data = await get_disk(embed)

        if embed:
            embed = discord.Embed(title="Disks", colour=await ctx.embed_colour())
            if not data:
                embed.add_field(
                    name="No disks found",
                    value=(
                        "That's not something you see very often! You're probably using WSL or "
                        "other virtualisation technology"
                    ),
                )
            for name, diskdata in data.items():
                embed.add_field(name=name, value=box(diskdata))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Disks**\n"
            if not data:
                data = {
                    "No one's logged in": (
                        "That's not something you see very often! You're probably using WSL or "
                        "other virtualisation technology"
                    )
                }
            to_box = "".join(f"{name}\n{diskdata}" for name, diskdata in data.items())
            msg += box(to_box)
            await ctx.send(msg)

    @system.command(
        name="processes", aliases=["proc"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_processes(self, ctx: commands.Context):
        """
        Get an overview of the status of currently running processes.

        Platforms: Windows, Linux, Mac OS
        """
        async with ctx.typing():
            proc = (await get_proc())["statuses"]

        if await ctx.embed_requested():
            embed = discord.Embed(title="Processes", colour=await ctx.embed_colour())
            embed.add_field(name="Status", value=box(proc))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Processes**\n"
            msg += box(f"CPU\n{proc}\n")
            await ctx.send(msg)

    @system.command(
        name="network", aliases=["net"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_net(self, ctx: commands.Context):
        """
        Get network stats. They may have overflowed and reset at some point.

        Platforms: Windows, Linux, Mac OS
        """
        stats = (await get_net())["counters"]

        if await ctx.embed_requested():
            embed = discord.Embed(title="Network", colour=await ctx.embed_colour())
            embed.add_field(name="Network Stats", value=box(stats))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Network**\n"
            msg += box(f"Network Stats\n{stats}\n")
            await ctx.send(msg)

    @system.command(
        name="uptime", aliases=["up"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_uptime(self, ctx: commands.Context):
        """
        Get the system boot time and how long ago it was.

        Platforms: Windows, Linux, Mac OS
        """
        uptime = (await get_uptime())["uptime"]

        if await ctx.embed_requested():
            embed = discord.Embed(title="Uptime", colour=await ctx.embed_colour())
            embed.add_field(name="Uptime", value=box(uptime))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Utime**\n"
            msg += box(f"Uptime\n{uptime}\n")
            await ctx.send(msg)

    @system.command(name="red", cls=DynamicHelp, supported_sys=True)  # all systems
    async def system_red(self, ctx: commands.Context):
        """
        See what resources [botname] is using.

        Platforms: Windows, Linux, Mac OS
        Note: SWAP memory information is only available on Linux.
        """
        async with ctx.typing():
            red = (await get_red())["red"]

        botname = self.bot.user.name

        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"{botname}'s resource usage", colour=await ctx.embed_colour()
            )
            embed.add_field(name="Resource usage", value=box(red))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = f"**{botname}'s resource usage**\n"
            msg += box(f"Resource usage\n{red}\n")
            await ctx.send(msg)

    @system.command(
        name="all", aliases=["overview", "top"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_all(self, ctx: commands.Context):
        """
        Get an overview of the current system metrics, similar to `top`.

        This will show CPU utilisation, RAM usage and uptime as well as
        active processes.

        Platforms: Windows, Linux, Mac OS
        Note: This command appears to be very slow in Windows.
        """
        async with ctx.typing():
            cpu = await get_cpu()
            mem = await get_mem()
            proc = await get_proc()
            red = (await get_red())["red"]

        percent = cpu["percent"]
        times = cpu["time"]
        physical = mem["physical"]
        swap = mem["swap"]
        procs = proc["statuses"]
        botname = self.bot.user.name

        if await ctx.embed_requested():
            embed = discord.Embed(title="Overview", colour=await ctx.embed_colour())
            embed.add_field(name="CPU Usage", value=box(percent))
            embed.add_field(name="CPU Times", value=box(times))
            embed.add_field(name="Physical Memory", value=box(physical))
            embed.add_field(name="SWAP Memory", value=box(swap))
            embed.add_field(name="Processes", value=box(procs))
            embed.add_field(name=f"{botname}'s resource usage", value=box(red))
            await ctx.send(embed=self.finalise_embed(embed))
        else:
            msg = "**Overview**\n"
            to_box = f"CPU Usage\n{percent}\n"
            to_box += f"CPU Times\n{times}\n"
            to_box += f"Physical Memory\n{physical}\n"
            to_box += f"SWAP Memory\n{swap}\n"
            to_box += f"Processes\n{procs}\n"
            to_box += f"{botname}'s resource usage\n{red}\n"
            msg += box(to_box)
            await ctx.send(msg)
