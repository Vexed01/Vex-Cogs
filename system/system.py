from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import discord
import psutil
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_timedelta

from system.components.view import SystemView

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
from .vexutils import format_help, format_info

if TYPE_CHECKING:
    from discord.types.embed import EmbedField

UNAVAILABLE = "\N{CROSS MARK} This command isn't available on your system."
ZERO_WIDTH = "\u200b"

# cspell:ignore psutil shwtemp tablefmt sfan suser sdiskpart sdiskusage fstype proc procs


class System(commands.Cog):
    """
    Get system metrics.

    Most commands work on all OSes or omit certian information.
    See the help for individual commands for detailed limitations.
    """

    __version__ = "1.4.0"
    __author__ = "@vexingvexed"

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
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    def finalise_embed(self, e: discord.Embed) -> discord.Embed:
        """Make embeds look nicer - limit to two columns and set the footer to boot time"""
        # needed because otherwise they are otherwise too squashed together so tabulate breaks
        # doesn't look great on mobile but is fully bearable, more than ugly text wrapping

        # oh, don't mention the ugly code please :P
        # it works...
        emb = e.to_dict()

        fields = emb.get("fields", [])
        if len(fields) > 2:  # needs multi rows
            data: list[list[EmbedField]] = []
            temp: list[EmbedField] = []
            for field in fields:
                temp.append(field)
                if len(temp) == 2:
                    data.append(temp)
                    temp = []
            if len(temp) != 0:  # clear up stragglers
                data.append(temp)

            empty_field: EmbedField = {"inline": True, "name": ZERO_WIDTH, "value": ZERO_WIDTH}
            fields = []
            for row in data:
                while len(row) < 3:
                    row.append(empty_field)
                fields.extend(row)

        # else it's 2 or less columns so doesn't need special treatment
        emb["fields"] = fields
        e = discord.Embed.from_dict(emb)

        # and footer is just a nice touch, thanks max for the idea of uptime there
        sys_uptime = humanize_timedelta(seconds=up_for())
        bot_uptime = humanize_timedelta(timedelta=datetime.datetime.utcnow() - self.bot.uptime)

        e.set_footer(text=f"System uptime: {sys_uptime}\nBot uptime: {bot_uptime}")

        return e

    @commands.has_permissions(embed_links=True)
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
            embed = await self.prep_cpu_msg(ctx.channel)
            await ctx.send(embed=embed, view=SystemView(ctx.author, self, "cpu"))

    async def prep_cpu_msg(self, channel: discord.abc.Messageable) -> discord.Embed | str:
        data = await get_cpu()
        percent = data["percent"]
        time = data["time"]
        freq = data["freq"]
        embed = discord.Embed(title="CPU Metrics", colour=await self.bot.get_embed_color(channel))
        embed.add_field(name="CPU Usage", value=box(percent))
        embed.add_field(name="CPU Times", value=box(time))
        extra = data["freq_note"]
        embed.add_field(name=f"CPU Frequency{extra}", value=box(freq))
        return self.finalise_embed(embed)

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
        await ctx.send(
            embed=await self.prep_mem_msg(ctx.channel), view=SystemView(ctx.author, self, "mem")
        )

    async def prep_mem_msg(self, channel: discord.abc.Messageable) -> discord.Embed | str:
        data = get_mem()
        physical = data["physical"]
        swap = data["swap"]
        embed = discord.Embed(title="Memory", colour=await self.bot.get_embed_color(channel))
        embed.add_field(name="Physical Memory", value=box(physical))
        embed.add_field(name="SWAP Memory", value=box(swap))
        return self.finalise_embed(embed)

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

        await ctx.send(
            embed=await self.prep_sensors_msg(ctx.channel, fahrenheit),
            view=SystemView(ctx.author, self, "sensors"),
        )

    async def prep_sensors_msg(
        self, channel: discord.abc.Messageable, fahrenheit: bool = False
    ) -> discord.Embed:
        data = get_sensors(fahrenheit)
        temp = data["temp"]
        fans = data["fans"]
        embed = discord.Embed(title="Sensors", colour=await self.bot.get_embed_colour(channel))
        embed.add_field(name="Temperatures", value=box(temp))
        embed.add_field(name="Fans", value=box(fans))
        return self.finalise_embed(embed)

    @system.command(name="users", cls=DynamicHelp, supported_sys=True)  # all systems
    async def system_users(self, ctx: commands.Context):
        """
        Get information about logged in users.

        This will show the user name, what terminal they're logged in at,
        and when they logged in.

        Platforms: Windows, Linux, Mac OS
        Note: PID is not available on Windows. Terminal is usually `Unknown`
        """
        await ctx.send(
            embed=await self.prep_users_msg(ctx.channel),
            view=SystemView(ctx.author, self, "users"),
        )

    async def prep_users_msg(self, channel: discord.abc.Messageable) -> discord.Embed:
        data = get_users()
        embed = discord.Embed(title="Users", colour=await self.bot.get_embed_colour(channel))
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
        return self.finalise_embed(embed)

    @system.command(
        name="disk", aliases=["df"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_disk(self, ctx: commands.Context, ignore_loop: bool = True):
        """
        Get infomation about disks connected to the system.

        This will show the space used, total space, filesystem and
        mount point (if you're on Linux make sure it's not potentially
        sensitive if running the command a public space).

        If `ignore_loop` is set to `True`, this will ignore any loop (fake) devices on Linux.

        Platforms: Windows, Linux, Mac OS
        Note: Mount point is basically useless on Windows as it's the
        same as the drive name, though it's still shown.
        """
        await ctx.send(
            embed=await self.prep_disk_msg(ctx.channel, ignore_loop),
            view=SystemView(ctx.author, self, "disk"),
        )

    async def prep_disk_msg(
        self, channel: discord.abc.Messageable, ignore_loop: bool = True
    ) -> discord.Embed:
        pre_data = get_disk()
        data: dict[str, str] = {}

        if ignore_loop:
            for name, disk_data in pre_data.items():
                if name.startswith("`/dev/loop"):
                    continue
                data[name] = disk_data
        else:
            data = pre_data

        embed = discord.Embed(title="Disks", colour=await self.bot.get_embed_colour(channel))
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
        return self.finalise_embed(embed)

    @system.command(
        name="processes", aliases=["proc"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_processes(self, ctx: commands.Context):
        """
        Get an overview of the status of currently running processes.

        Platforms: Windows, Linux, Mac OS
        """
        async with ctx.typing():
            await ctx.send(
                embed=await self.prep_proc_msg(ctx.channel),
                view=SystemView(ctx.author, self, "proc"),
            )

    async def prep_proc_msg(self, channel: discord.abc.Messageable) -> discord.Embed:
        proc = (await get_proc())["statuses"]
        embed = discord.Embed(title="Processes", colour=await self.bot.get_embed_colour(channel))
        embed.add_field(name="Status", value=box(proc))
        return self.finalise_embed(embed)

    @system.command(
        name="network", aliases=["net"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_net(self, ctx: commands.Context):
        """
        Get network stats. They may have overflowed and reset at some point.

        Platforms: Windows, Linux, Mac OS
        """
        await ctx.send(
            embed=await self.prep_net_msg(ctx.channel), view=SystemView(ctx.author, self, "net")
        )

    async def prep_net_msg(self, channel: discord.abc.Messageable) -> discord.Embed:
        stats = (get_net())["counters"]

        embed = discord.Embed(title="Network", colour=await self.bot.get_embed_colour(channel))
        embed.add_field(name="Network Stats", value=box(stats))
        return self.finalise_embed(embed)

    @system.command(
        name="uptime", aliases=["up"], cls=DynamicHelp, supported_sys=True  # all systems
    )
    async def system_uptime(self, ctx: commands.Context):
        """
        Get the system boot time and how long ago it was.

        Platforms: Windows, Linux, Mac OS
        """
        await ctx.send(
            embed=await self.prep_uptime_msg(ctx.channel),
            view=SystemView(ctx.author, self, "uptime"),
        )

    async def prep_uptime_msg(self, channel: discord.abc.Messageable) -> discord.Embed:
        uptime = (get_uptime())["uptime"]

        embed = discord.Embed(title="Uptime", colour=await self.bot.get_embed_colour(channel))
        embed.add_field(name="Uptime", value=box(uptime))
        return self.finalise_embed(embed)

    @system.command(name="red", cls=DynamicHelp, supported_sys=True)  # all systems
    async def system_red(self, ctx: commands.Context):
        """
        See what resources [botname] is using.

        Platforms: Windows, Linux, Mac OS
        Note: SWAP memory information is only available on Linux.
        """

        async with ctx.typing():
            await ctx.send(
                embed=await self.prep_red_msg(ctx.channel),
                view=SystemView(ctx.author, self, "red"),
            )

    async def prep_red_msg(self, channel: discord.abc.Messageable) -> discord.Embed:
        # i jolly hope we are logged in...
        if TYPE_CHECKING:
            assert self.bot.user is not None

        red = (await get_red())["red"]

        botname = self.bot.user.name

        embed = discord.Embed(
            title=f"{botname}'s resource usage", colour=await self.bot.get_embed_colour(channel)
        )
        embed.add_field(name="Resource usage", value=box(red))
        return self.finalise_embed(embed)

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
            await ctx.send(
                embed=await self.prep_all_msg(ctx.channel),
                view=SystemView(ctx.author, self, "all"),
            )

    async def prep_all_msg(self, channel: discord.abc.Messageable) -> discord.Embed:
        # i jolly hope we are logged in...
        if TYPE_CHECKING:
            assert self.bot.user is not None

        cpu = await get_cpu()
        mem = get_mem()
        proc = await get_proc()
        red = (await get_red())["red"]

        percent = cpu["percent"]
        times = cpu["time"]
        physical = mem["physical"]
        swap = mem["swap"]
        procs = proc["statuses"]
        botname = self.bot.user.name

        embed = discord.Embed(title="Overview", colour=await self.bot.get_embed_colour(channel))
        embed.add_field(name="CPU Usage", value=box(percent))
        embed.add_field(name="CPU Times", value=box(times))
        embed.add_field(name="Physical Memory", value=box(physical))
        embed.add_field(name="SWAP Memory", value=box(swap))
        embed.add_field(name="Processes", value=box(procs))
        embed.add_field(name=f"{botname}'s resource usage", value=box(red))
        return self.finalise_embed(embed)
