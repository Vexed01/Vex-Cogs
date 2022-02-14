from __future__ import annotations

import asyncio
from typing import Optional

from aiohttp import web
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config

from .vexutils import format_help, format_info, get_vex_logger

log = get_vex_logger(__name__)


class UptimeResponder(commands.Cog):
    """
    A cog for responding to pings form various uptime monitoring services,
    such as UptimeRobot, Pingdom, Uptime.com, or self-hosted ones like UptimeKuma or Upptime.

    The web server will run in the background whenever the cog is loaded on the specified port.

    It will respond with status code 200 when a request is made to the root URL.

    If you want to use this with an external service, you will need to set up port forwarding.
    Make sure you are aware of the security risk of exposing your machine to the internet.
    """

    __version__ = "1.0.0"
    __author__ = "Vexed#9000"

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config: Config = Config.get_conf(
            self, identifier=418078199982063626, force_registration=True
        )
        self.config.register_global(port=8710)

    def cog_unload(self) -> None:
        self.bot.loop.create_task(self.shutdown_webserver())

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    @commands.command(
        hidden=True,
    )
    async def uptimeresponderinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    async def shutdown_webserver(self) -> None:
        await self.runner.shutdown()
        await self.runner.cleanup()
        log.info("Web server for UptimeResponder pings has been stopped due to cog unload.")

    async def red_delete_data_for_user(self, *args, **kwargs) -> None:
        # nothing to delete
        pass

    async def main_page(self, request: web.Request) -> web.Response:
        name = self.bot.user.name if self.bot.user else "Unknown"
        return web.Response(
            text=f"{name} is online and the UptimeResponder cog is loaded.", status=200
        )

    async def start_webserver(self, port: int | None = None) -> None:
        await asyncio.sleep(1)  # let previous server shut down if cog was reloaded

        port = port or await self.config.port()

        app = web.Application()
        app.add_routes([web.get("/", self.main_page)])
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, port=port)
        await site.start()

        log.info(f"Web server for UptimeResponder pings has started on port {port}.")

        self.runner = runner

    @commands.is_owner()
    @commands.command()
    async def uptimeresponderport(self, ctx: commands.Context, port: Optional[int] = None):
        """Get or set the port to run the simple web server on.

        Run the command on it's own (`[p]uptimeresponderport`) to see what it's
        set to at the moment, and to set it run `[p]uptimeresponderport 8080`, for example.
        """
        if port is None:
            await ctx.send(
                f"The current port is {await self.config.port()}.\nTo change it, run "
                f"`{ctx.clean_prefix}uptimeresponderport <port>`"
            )
            return

        async with ctx.typing():
            await self.shutdown_webserver()
            try:
                await self.start_webserver(port)
            except OSError as e:
                await ctx.send(
                    f"Failed to start web server on port {port}: ```\n{e}```\nPlease choose a"
                    " different port. No web server is running at the moment."
                )
                return
            await self.config.port.set(port)

        await ctx.send(f"The webserver has been restarted on port {port}.")
