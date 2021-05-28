import datetime

import discord
import psutil
from redbot.core import commands
from redbot.core.bot import Red
from vexcogutils import format_help, format_info

from .command import DynamicHelp
from .utils import box, get_cpu, get_disk, get_mem, get_proc, get_sensors, get_uptime, get_users

UNAVAILABLE = "\N{CROSS MARK} This command isn't available on your system."
ZERO_WIDTH = "\u200b"

# cspell:ignore psutil shwtemp tablefmt sfan suser sdiskpart sdiskusage fstype proc procs


class System(commands.Cog):
    """
    Get system metrics.

    Most commands work on all OSes or omit certian information.
    See the help for individual commands for detailed limitations.
    """

    __version__ = "1.1.2"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def systeminfo(self, ctx: commands.Context):
        await ctx.send(await format_info(self.qualified_name, self.__version__))

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
                now = datetime.datetime.utcnow()
                embed = discord.Embed(
                    title="CPU Metrics", colour=await ctx.embed_colour(), timestamp=now
                )
                embed.add_field(name="CPU Usage", value=box(percent))
                embed.add_field(name="CPU Times", value=box(time))
                extra = data["freq_note"]
                embed.add_field(name=f"CPU Frequency{extra}", value=box(freq), inline=False)
                await ctx.send(embed=embed)
            else:
                msg = "**CPU Metrics**\n"
                to_box = f"CPU Usage\n{percent}\n"
                to_box += f"CPU Times\n{time}\n"
                extra = data["freq_note"]
                to_box += f"CPU Frequency{extra}\n{freq}\n"
                msg += box(to_box)
                await ctx.send(msg)

    @system.command(
        name="mem", aliases=["memory", "ram"], cls=DynamicHelp, supported_sys=True
    )  # all systems
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
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Memory", colour=await ctx.embed_colour(), timestamp=now)
            embed.add_field(name="Physical Memory", value=box(physical))
            embed.add_field(name="SWAP Memory", value=box(swap))
            await ctx.send(embed=embed)
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
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Sensors", colour=await ctx.embed_colour(), timestamp=now)
            embed.add_field(name="Temperatures", value=box(temp))
            embed.add_field(name="Fans", value=box(fans))
            await ctx.send(embed=embed)
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
        if not data:
            return await ctx.send("It looks like no one is logged in.")
        if embed:
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Users", colour=await ctx.embed_colour(), timestamp=now)
            for name, userdata in data.items():
                embed.add_field(name=name, value=box(userdata))
            await ctx.send(embed=embed)
        else:
            msg = "**Users**\n"
            to_box = "".join(f"{name}\n{userdata}" for name, userdata in data.items())
            msg += box(to_box)
            await ctx.send(msg)

    @system.command(
        name="disk", aliases=["df"], cls=DynamicHelp, supported_sys=True
    )  # all systems
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
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Disks", colour=await ctx.embed_colour(), timestamp=now)
            for name, diskdata in data.items():
                embed.add_field(name=name, value=box(diskdata))
            await ctx.send(embed=embed)
        else:
            msg = "**Disks**\n"
            to_box = "".join(f"{name}\n{diskdata}" for name, diskdata in data.items())
            msg += box(to_box)
            await ctx.send(msg)

    @system.command(
        name="processes", aliases=["proc"], cls=DynamicHelp, supported_sys=True
    )  # all systems
    async def system_processes(self, ctx: commands.Context):
        """
        Get an overview of the status of currently running processes.

        Platforms: Windows, Linux, Mac OS
        """
        async with ctx.typing():
            proc = (await get_proc())["statuses"]

        if await ctx.embed_requested():
            now = datetime.datetime.utcnow()
            embed = discord.Embed(
                title="Processes", colour=await ctx.embed_colour(), timestamp=now
            )
            embed.add_field(name="Status", value=box(proc))
            await ctx.send(embed=embed)
        else:
            msg = "**Processes**\n"
            msg += box(f"CPU\n{proc}\n")
            await ctx.send(msg)

    @system.command(
        name="uptime", aliases=["up"], cls=DynamicHelp, supported_sys=True
    )  # all systems
    async def system_uptime(self, ctx: commands.Context):
        """
        Get the system boot time and how long ago it was.

        Platforms: Windows, Linux, Mac OS
        """
        uptime = (await get_uptime())["uptime"]

        if await ctx.embed_requested():
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Uptime", colour=await ctx.embed_colour(), timestamp=now)
            embed.add_field(name="Uptime", value=box(uptime))
            await ctx.send(embed=embed)
        else:
            msg = "**Utime**\n"
            msg += box(f"Uptime\n{uptime}\n")
            await ctx.send(msg)

    @system.command(
        name="top", aliases=["overview", "all"], cls=DynamicHelp, supported_sys=True
    )  # all systems
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

            percent = cpu["percent"]
            times = cpu["time"]
            physical = mem["physical"]
            swap = mem["swap"]
            procs = proc["statuses"]

        if await ctx.embed_requested():
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Overview", colour=await ctx.embed_colour(), timestamp=now)
            embed.add_field(name="CPU Usage", value=box(percent))
            embed.add_field(name="CPU Times", value=box(times))
            embed.add_field(name=ZERO_WIDTH, value=ZERO_WIDTH)
            embed.add_field(name="Physical Memory", value=box(physical))
            embed.add_field(name="SWAP Memory", value=box(swap))
            embed.add_field(name=ZERO_WIDTH, value=ZERO_WIDTH)
            embed.add_field(name="Processes", value=box(procs))
            await ctx.send(embed=embed)
        else:
            msg = "**Overview**\n"
            to_box = f"CPU\n{cpu}\n\n"
            to_box += f"Physical Memory\n{physical}\n"
            to_box += f"SWAP Memory\n{swap}\n"
            to_box += f"Processes\n{procs}\n"
            msg += box(to_box)
            await ctx.send(msg)
