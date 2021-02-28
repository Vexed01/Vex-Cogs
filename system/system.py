import asyncio
import datetime
from typing import Union

import discord
import psutil
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, humanize_number
from tabulate import tabulate


UNAVAILABLE = "\N{CROSS MARK} This command isn't available on your system."


class System(commands.Cog):
    """
    Get system metrics.

    Most commands work on all OSes or omit certian information.
    See the help for individual commands for detailed limitations.
    """

    __version__ = "1.0.0"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**"

    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, identifier="418078199982063626")
        default = {"embed": True}
        self.config.register_global(settings=default)
        # this is a global setting... sorry bots with co-owners

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    async def _use_embed(self, ctx: commands.Context):
        if await ctx.embed_requested() is False:
            return False
        return (await self.config.settings())["embed"]

    @checks.is_owner()
    @commands.group()
    async def system(self, ctx: commands.Context):
        """Base command for this cog.

        Most commands work on all OSes or omit certian information.
        See the help for individual commands for detailed limitations.
        """

    @system.command(name="embedtoggle", aliases=["embed"])
    async def system_embedtoggle(self, ctx: commands.Context):
        """
        Toggle embeds on and off for this cog.

        Note if embeds are set to False using the `embedset` command that will oberride this.
        """
        old = (await self.config.settings())["embed"]
        new = not old
        await self.config.settings.set_raw("embed", value=new)
        await ctx.send(
            f"Embeds for this cog set to **`{new}`**.\n"
            "Note if embeds are set to False using the `embedset` command that will override this."
        )

    def _box(self, text: str):
        """Box up text as css. May return over 2k chars"""
        return box(text, "css")

    def _hum(self, num: Union[int, float]):
        """Round a number, then humanize."""
        return humanize_number(round(num))

    def _hum_mb(self, bytes: Union[int, float]):
        """Convert to MBs, round, then humanize."""
        mb = bytes / 1048576
        return self._hum(mb)

    def _secs_to_time(self, secs: Union[int, float]):
        m, s = divmod(secs, 60)
        h, m = divmod(m, 60)
        return datetime.datetime.fromtimestamp(secs).strftime("%H:%M:%S")

    def _system_uptime(self):
        now = datetime.datetime.utcnow().timestamp()
        return now - psutil.boot_time()

    async def _cpu(self):
        """Get CPU metrics"""
        psutil.cpu_percent()
        await asyncio.sleep(1)
        percent = psutil.cpu_percent(percpu=True)
        time = psutil.cpu_times()
        freq = psutil.cpu_freq(percpu=True)
        cores = psutil.cpu_count()

        if psutil.LINUX:
            data = {"percent": "", "freq": "", "freq_note": "", "time": ""}
            for i in range(cores):
                data["percent"] += f"[Core {i}] {percent[i]} %\n"
                ghz = round((freq[i].current / 1000), 2)
                data["freq"] += f"[Core {i}] {ghz} GHz\n"
        else:
            data = {"percent": "", "freq": "", "freq_note": " (nominal)", "time": ""}
            for i in range(cores):
                data["percent"] += f"[Core {i}] {percent[i]} %\n"
            ghz = round((freq[0].current / 1000), 2)
            data["freq"] = f"{ghz} GHz\n"  # blame windows

        data["time"] += f"[Idle]   {self._hum(time.idle)} seconds\n"
        data["time"] += f"[User]   {self._hum(time.user)} seconds\n"
        data["time"] += f"[System] {self._hum(time.system)} seconds\n"
        data["time"] += f"[Uptime] {self._hum(self._system_uptime())} seconds\n"

        return data

    async def _mem(self):
        """Get memory metrics"""
        physical = psutil.virtual_memory()
        swap = psutil.swap_memory()

        data = {"physical": "", "swap": ""}

        data["physical"] += f"[Percent]  {physical.percent} %\n"
        data["physical"] += f"[Used]     {self._hum_mb(physical.used)} MB\n"
        data["physical"] += f"[Avalible] {self._hum_mb(physical.available)} MB\n"
        data["physical"] += f"[Total]    {self._hum_mb(physical.total)} MB\n"

        data["swap"] += f"[Percent]  {swap.percent} %\n"
        data["swap"] += f"[Used]     {self._hum_mb(swap.used)} MB\n"
        data["swap"] += f"[Avalible] {self._hum_mb(swap.free)} MB\n"
        data["swap"] += f"[Total]    {self._hum_mb(swap.total)} MB\n"

        return data

    async def _sensors(self, farenheit: bool):
        """Get metrics from sensors"""
        temp = psutil.sensors_temperatures(farenheit)
        fans = psutil.sensors_fans()

        data = {"temp": "", "fans": "", "battery": ""}

        t_data = []
        for group in temp:
            for item in group:
                t_data.append([f"[{item.label}]" or "[Unknown]", item.current])
        data["temp"] = tabulate(t_data, tablefmt="plain")

        t_data = []
        for fan in fans:
            t_data.append([f"{fan.label}" or "[Unknown]", fan.current])
        data["fans"] = tabulate(t_data, tablefmt="plain")

        return data

    async def _users(self, embed: bool):
        """Get users connected"""
        users = psutil.users()

        if embed:
            e = "`"
        else:
            e = ""

        data = {}

        for user in users:
            data[f"{e}{user.name}{e}"] = "[Terminal]  {}\n".format(user.terminal or "Unknown")
            started = datetime.datetime.fromtimestamp(user.started).strftime("%Y-%m-%d at %H:%M:%S")
            data[f"{e}{user.name}{e}"] += f"[Started]   {started}\n"
            if not psutil.WINDOWS:
                data[f"{e}{user.name}{e}"] += f"[PID]       {user.pid}"

        return data

    @system.command(name="cpu")
    async def system_cpu(self, ctx: commands.Context):
        """
        Get metrics about the CPU.

        Platforms: Windows, Linux, Mac OS
        Note: CPU frequency is nominal and overall on Windows and Mac OS,
        on Linux it's current and per-core.
        """
        with ctx.typing():
            data = await self._cpu()
            percent = data["percent"]
            time = data["time"]
            freq = data["freq"]
            if await self._use_embed(ctx):
                now = datetime.datetime.utcnow()
                embed = discord.Embed(title="CPU Metrics", colour=await ctx.embed_colour(), timestamp=now)
                embed.add_field(name="CPU Usage", value=self._box(percent))
                embed.add_field(name=f"CPU Times", value=self._box(time))
                extra = data["freq_note"] or None
                embed.add_field(name=f"CPU Frequency{extra}", value=self._box(freq), inline=False)
                await ctx.send(embed=embed)
            else:
                msg = "**CPU Metrics**\n"
                to_box = f"CPU Usage\n{percent}\n"
                to_box += f"CPU Times\n{time}\n"
                extra = data["freq_note"] or None
                to_box += f"CPU Frequency{extra}\n{freq}\n"
                msg += self._box(to_box)
                await ctx.send(msg)

    @system.command(name="memory", aliases=["mem"])
    async def system_mem(self, ctx: commands.Context):
        """
        Get infomation about memory usage.

        Platforms: Windows, Linux, Mac OS
        """
        data = await self._mem()
        physical = data["physical"]
        swap = data["swap"]
        if await self._use_embed(ctx):
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Memory", colour=await ctx.embed_colour(), timestamp=now)
            embed.add_field(name="Physical Memory", value=self._box(physical))
            embed.add_field(name="SWAP Memory", value=self._box(swap))
            await ctx.send(embed=embed)
        else:
            msg = "**Memory**\n"
            to_box = f"Physical Memory\n{physical}\n"
            to_box += f"SWAP Memory\n{swap}\n"
            msg += self._box(to_box)
            await ctx.send(msg)

    @system.command(name="sensors", aliases=["temp", "temperature", "fan", "fans"])
    async def system_sesnsors(self, ctx: commands.Context, farenheit: bool = False):
        """
        Get sensor metrics.

        Platforms: Linux
        """
        if not psutil.LINUX:
            return await ctx.send(UNAVAILABLE)

        data = await self._mem()
        temp = data["temperature"] or "No temperature sensors found"
        fans = data["fans"] or "No fans found"
        if await self._use_embed(ctx):
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Sensors", colour=await ctx.embed_color(), timestamp=now)
            embed.add_field(name="Temperatures", value=self._box(temp))
            embed.add_field(name="Fans", value=self._box(fans))
            await ctx.send(embed=embed)
        else:
            msg = "**Temperature**\n"
            to_box = f"Temperatures\n{temp}\n"
            to_box += f"Fans\n{fans}\n"
            msg += self._box(to_box)
            await ctx.send(msg)

    @system.command(name="users")
    async def system_users(self, ctx: commands.Context):
        """
        View logged in users.

        Platforms: Windows, Linux, Mac OS
        Note: PID is not available on Windows.
        """
        embed = await self._use_embed(ctx)
        data = await self._users(embed)
        if not data:
            return await ctx.send("It looks like no one is logged in.")
        if embed:
            now = datetime.datetime.utcnow()
            embed = discord.Embed(title="Users", colour=await ctx.embed_color(), timestamp=now)
            for user in data.items():
                embed.add_field(name=user[0], value=self._box(user[1]))
            await ctx.send(embed=embed)
        else:
            msg = "**Users**\n"
            to_box = ""
            for user in data.items():
                to_box += f"{user[0]}\n{user[1]}"
            msg += self._box(to_box)
            await ctx.send(msg)
