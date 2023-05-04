import discord
from redbot.core import app_commands, commands

from .abc import MixinMeta


class BUSlash(MixinMeta):
    uptime = app_commands.Group(name="uptime", description="Get my uptime data")

    @uptime.command(name="data", description="Get my uptime data in an embed")
    @app_commands.describe(days="Days of data to show, use 0 for all-time data. Default: 30")
    async def uptime_slash(self, interaction: discord.Interaction, days: int = 30):
        context: commands.Context = await self.bot.get_context(interaction)
        await self.uptime_command(context)

    @uptime.command(name="graph", description="Get my uptime graph in an embed")
    @app_commands.describe(days="Days of data to show, use 0 for all-time data. Default: 30")
    async def uptimegraph_slash(self, interaction: discord.Interaction, days: int = 30):
        context: commands.Context = await self.bot.get_context(interaction)
        await self.uptimegraph(context)

    @uptime.command(name="downtime", description="Get my downtime data in an embed")
    @app_commands.describe(days="Days of data to show, use 0 for all-time data. Default: 30")
    async def downtime_slash(self, interaction: discord.Interaction, days: int = 30):
        context: commands.Context = await self.bot.get_context(interaction)
        await self.downtime(context)
