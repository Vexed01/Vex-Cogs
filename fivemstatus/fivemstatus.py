from __future__ import annotations

import datetime
import json

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config

from .abc import CompositeMetaClass
from .loop import FiveMLoop
from .objects import MessageData, ServerData, ServerUnreachable
from .vexutils import format_help, format_info, get_vex_logger

log = get_vex_logger(__name__)

MAX_LEN_VISUAL = ". . . . . . . . . . . . . . . . . . . . . . . . ."


class FiveMStatus(commands.Cog, FiveMLoop, metaclass=CompositeMetaClass):
    """
    View the live status of a FiveM server, in a updating Discord message.

    The message is an embed that updates minutely.
    """

    __version__ = "1.0.1"
    __author__ = "Vexed#9000"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_guild(message={})

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        self.loop.cancel()
        log.debug("Loop stopped as cog unloaded.")

    @commands.command(hidden=True)
    async def fivemstatusinfo(self, ctx: commands.Context):
        await ctx.send(
            await format_info(ctx, self.qualified_name, self.__version__, loops=[self.loop_meta])
        )

    async def get_data(self, server: str) -> ServerData:
        if server.startswith("https://"):
            server = server[8:]
        if not server.startswith("http"):
            server = f"http://{server}"

        async with aiohttp.ClientSession() as session:
            url = server
            if not url.endswith("/"):
                url += "/"

            info = None

            try:
                info = json.loads(
                    await (await session.get(f"{url}info.json", timeout=10)).text(encoding="utf-8")
                )
                players = await (await session.get(f"{url}players.json", timeout=10)).text(
                    encoding="utf-8"
                )
                player_count = players.count('"endpoint":')  # i know this is stupid but from my
            # testing many servers have invalid players.json files on random occurrences.
            except aiohttp.ClientError:
                raise ServerUnreachable(f"Server at {url} is unreachable.")

        # strip colour data
        name = ""
        skip = False
        for c in info.get("vars", {}).get("sv_projectName", ""):
            if c == "^":
                skip = True
            elif skip:
                skip = False
            else:
                name += c

        if name == "":
            name = "FiveM Server"

        return ServerData(
            current_users=player_count,
            max_users=info["vars"]["sv_maxClients"],
            name=name,
            ip=url.lstrip("http://").lstrip("https://").rstrip("/"),
        )

    async def generate_embed(
        self, data: ServerData | None, config_data: MessageData, maintenance: bool
    ) -> discord.Embed:
        if maintenance:
            return discord.Embed(
                title=config_data["last_known_name"],
                colour=0xFFA200,
                description="FiveM server is in maintenance mode.",
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )
        if data is None:  # offline
            return discord.Embed(
                title=config_data["last_known_name"],
                colour=0xFF0000,
                description="FiveM server is offline.",
                timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
            )

        embed = discord.Embed(
            title=config_data["last_known_name"],
            colour=0x1FC60C,
            description=f"FiveM server is online. Join at `{data.ip}`",
            timestamp=datetime.datetime.now(tz=datetime.timezone.utc),
        )
        embed.add_field(name="Status", value=f"{data.current_users}/{data.max_users} players")
        return embed

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def fivemstatus(self, ctx: commands.Context):
        """
        Set up a live FiveM status embed.

        To stop updating the message, just delete it.
        """

    @fivemstatus.command()
    async def setup(self, ctx: commands.Context, channel: discord.TextChannel, server: str):
        """Set up a FiveM status message.

        **Examples:**
            - `[p]fivemstatus setup #status 1.0.1.0:30120`
        """
        try:
            data = await self.get_data(server)
        except ServerUnreachable as e:
            await ctx.send(e)
            return

        embed = await self.generate_embed(data, None, False)

        try:
            message = await channel.send(embed=embed)
        except discord.Forbidden:
            await ctx.send("I don't have permission to send messages in that channel.")
            return

        msg_id = message.id

        await self.config.guild(ctx.guild).message.set(
            {
                "server": server,
                "msg_id": msg_id,
                "maintenance": False,
                "last_known_name": data.name,
                "channel_id": channel.id,
            }
        )

        await ctx.send("All set, head over to the channel and check it out.")

    @fivemstatus.command()
    async def maintenance(self, ctx: commands.Context):
        """Toggle maintenance mode."""
        async with self.config.guild(ctx.guild).message() as conf:
            if not conf:
                await ctx.send("You haven't set up yet.")
                return

            conf["maintenance"] = not conf["maintenance"]

            new_setting = conf["maintenance"]

        await ctx.send(
            ("Maintenance mode enabled." if new_setting else "Maintenance mode disabled.")
            + " The status embed may take up to a minute to update."
        )
