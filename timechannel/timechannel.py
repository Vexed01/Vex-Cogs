import datetime
import logging
from typing import Dict

import discord
import pytz
from discord.channel import DMChannel, GroupChannel
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from vexcogutils import format_help, format_info

from .abc import CompositeMetaClass
from .converters import TimezoneConverter
from .loop import TCLoop

_log = logging.getLogger("red.vex.timechannel")


class TimeChannel(commands.Cog, TCLoop, metaclass=CompositeMetaClass):
    """
    Allocate a Discord voice channel to show the time in specific timezones. Updates every hour.

    A list of timezones can be found here, though you should be able to enter any
    major city: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

    There is a fuzzy search so you don't need to put the region in, only the city.

    This cog will shrink down from the proper region names, for example `America/New_York`
    will become `New York`.

    The `[p]timezones` command (runnable by anyone) will show the full location name.
    """

    __version__ = "1.1.0"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_guild(timechannels={})

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    def cog_unload(self) -> None:
        self.loop.cancel()
        _log.debug("Loop stopped as cog unloaded.")

    @commands.command(hidden=True, aliases=["tcinfo"])
    async def timechannelinfo(self, ctx: commands.Context):
        await ctx.send(
            await format_info(self.qualified_name, self.__version__, loops=[self.loop_meta])
        )

    @commands.guild_only()
    @commands.command()
    async def timezones(self, ctx: commands.Context):
        """See the time in all the configured timezones for this server."""
        assert ctx.guild is not None
        data: Dict[int, str] = await self.config.guild(ctx.guild).timechannels()
        print(data)
        if data is None:
            return await ctx.send("It looks like no time channels have been set up yet.")

        # partially from core at (what a tight fit with the link :aha:)
        # https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/events.py#L355
        sys_now = datetime.datetime.utcnow()
        discord_now = ctx.message.created_at
        if "UTC" not in data.values():
            description = f"UTC time: {sys_now.strftime('%b %d, %H:%M')}"
        else:
            description = ""

        diff = int(abs((discord_now - sys_now).total_seconds()))
        if diff > 60:
            description += (
                f"\n**Warning:** The system clock is out of sync with Discord's clock by {diff} "
                "seconds. These times, and the channels, may be inaccurate."
            )

        embed = discord.Embed(
            title=f"Timezones for {ctx.guild.name}",
            colour=await ctx.embed_colour(),
            timestamp=datetime.datetime.utcnow(),
            description=description,
        )
        embed.set_footer(text="Your local time")
        for c_id, target_timezone in data.items():
            channel = self.bot.get_channel(int(c_id))  # idk why its str
            assert not isinstance(channel, DMChannel) and not isinstance(channel, GroupChannel)
            if channel is None or target_timezone not in pytz.common_timezones:
                continue

            time = datetime.datetime.now(pytz.timezone(target_timezone)).strftime("%b %d, %H:%M")
            name = target_timezone.replace("_", " ")
            embed.add_field(name=name, value=time)

        await ctx.send(embed=embed)

    @commands.admin_or_permissions(manage_guild=True)
    @commands.group(aliases=["tcset"])
    async def timechannelset(self, ctx: commands.Context):
        """Manage channels which will show the time for a timezone."""

    @commands.bot_has_permissions(manage_channels=True)
    @timechannelset.command()
    async def create(self, ctx: commands.Context, timezone: TimezoneConverter):
        """
        Set up a time channel in this server.

        The list of acceptable timezones is here (the "TZ database name" column):
        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

        There is a fuzzy search, so you shouldn't need to enter the region.

        If you move the channel into a category, **click 'Keep Current Permissions' in the sync
        permissions dialogue.**

        **Examples:**
            - `[p]tcset create New York`
            - `[p]tcset create UTC`
            - `[p]tcset create London`
            - `[p]tcset create Europe/London`
        """
        assert ctx.guild is not None

        time = datetime.datetime.now(pytz.timezone(timezone)).strftime("%I%p").lstrip("0")
        short_tz = timezone.split("/")[-1]  # full one usually is too long
        name = f"{time} {short_tz}"

        # thanks boboly
        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=False),
            ctx.guild.me: discord.PermissionOverwrite(manage_channels=True, connect=True),
        }
        channel = await ctx.guild.create_voice_channel(
            name=name, overwrites=overwrites  # type:ignore
        )

        assert not isinstance(channel, DMChannel) and not isinstance(channel, GroupChannel)

        await self.config.guild(ctx.guild).timechannels.set_raw(  # type: ignore
            channel.id, value=timezone  # idk why its not an int
        )

        await ctx.send(
            f"Done, {channel.mention} will now show timezone `{timezone}`. Regular users will be "
            "unable to connect. You can move this channel into a category if you wish, but "
            "**click 'Keep Current Permissions' in the sync permissions dialogue.**"
        )

    @commands.bot_has_permissions(manage_channels=True)
    @timechannelset.command()
    async def remove(self, ctx: commands.Context, channel: discord.VoiceChannel):
        """
        Delete and stop updating a channel.

        For the <channel> argument, you can use its ID or mention (type #!channelname)

        **Example:**
            - `[p]tcset remove #!channelname` (the ! is how to mention voice channels)
            - `[p]tcset remove 834146070094282843`
        """
        assert ctx.guild is not None
        async with self.config.guild(ctx.guild).timechannels() as data:
            assert isinstance(data, dict)
            actual = data.pop(str(channel.id), None)

        if actual is None:
            await ctx.send("It looks like that's not a channel I update to.")
        else:
            await channel.delete(reason=f"Deleted with `tcset remove` by {ctx.author.name}")
            await ctx.send("Ok, I've deleted that channel and will no longer try to update it.")

    @commands.is_owner()
    @timechannelset.command(hidden=True)
    async def loopstatus(self, ctx: commands.Context):
        await ctx.send(embed=self.loop_meta.get_debug_embed())
