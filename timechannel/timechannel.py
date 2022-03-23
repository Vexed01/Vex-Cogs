from __future__ import annotations

import datetime
from typing import TYPE_CHECKING

import discord
import pytz
import rapidfuzz.process
from discord.guild import Guild
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config

from timechannel.utils import gen_replacements

from .abc import CompositeMetaClass
from .data import ZONE_KEYS
from .loop import TCLoop
from .vexutils import format_help, format_info, get_vex_logger
from .vexutils.chat import datetime_to_timestamp

log = get_vex_logger(__name__)

MAX_LEN_VISUAL = ". . . . . . . . . . . . . . . . . . . . . . . . ."


class TimeChannel(commands.Cog, TCLoop, metaclass=CompositeMetaClass):
    """
    Allocate a Discord voice channel to show the time in specific timezones. Updates every hour.

    A list of timezones can be found here, though you should be able to enter any
    major city: https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

    There is a fuzzy search so you don't need to put the region in, only the city.

    The `[p]timezones` command (runnable by anyone) will show the full location name.
    """

    __version__ = "1.3.1"
    __author__ = "Vexed#9000"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_guild(timechannels={})

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    async def cog_unload(self) -> None:
        self.loop.cancel()
        log.debug("Loop stopped as cog unloaded.")

    async def maybe_migrate(self) -> None:
        if await self.config.version() == 2:
            return

        log.debug("Migating to config v2")
        keys = list(ZONE_KEYS.keys())
        values = list(ZONE_KEYS.values())
        all_guilds = await self.config.all_guilds()
        for guild_id, guild_data in all_guilds.items():
            for c_id, target_timezone in guild_data.get("timechannels", {}).items():
                if target_timezone:
                    short_tz = target_timezone.split("/")[-1].replace("_", " ")
                    num_id = keys[values.index(target_timezone)]
                    all_guilds[guild_id]["timechannels"][c_id] = f"{short_tz}: {{{num_id}}}"
            await self.config.guild_from_id(guild_id).set(all_guilds[guild_id])

        await self.config.version.set(2)

    @commands.command(hidden=True, aliases=["tcinfo"])
    async def timechannelinfo(self, ctx: commands.Context):
        await ctx.send(
            await format_info(ctx, self.qualified_name, self.__version__, loops=[self.loop_meta])
        )

    @commands.guild_only()  # type:ignore
    @commands.command()
    async def timezones(self, ctx: commands.Context):
        """See the time in all the configured timezones for this server."""
        # guild only check
        if TYPE_CHECKING:
            assert ctx.guild is not None

        data: dict[int, str] = await self.config.guild(ctx.guild).timechannels()
        if data is None:
            return await ctx.send("It looks like no time channels have been set up yet.")

        # partially from core at (what a tight fit with the link :aha:)
        # https://github.com/Cog-Creators/Red-DiscordBot/blob/V3/develop/redbot/core/events.py#L355
        sys_now = datetime.datetime.utcnow()
        aware_sys_now = datetime.datetime.now(datetime.timezone.utc)
        discord_now = ctx.message.created_at
        if "qw" not in data.values():
            description = f"UTC time: {sys_now.strftime('%b %d, %H:%M')}"
        else:
            description = ""

        description += f"\nYour local time: {datetime_to_timestamp(aware_sys_now)}"

        if discord.__version__.startswith("1"):
            diff = int(abs((discord_now - sys_now).total_seconds()))
        else:
            diff = int(abs((discord_now - aware_sys_now).total_seconds()))
        if diff > 60:
            description += (
                f"\n**Warning:** The system clock is out of sync with Discord's clock by {diff} "
                "seconds. These times, and the channels, may be inaccurate."
            )

        embed = discord.Embed(
            title=f"Timezones for {ctx.guild.name}",
            colour=await ctx.embed_colour(),
            timestamp=aware_sys_now,
            description=description,
        )
        for c_id, target_timezone in data.items():
            channel = self.bot.get_channel(int(c_id))  # str bc config
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

    @timechannelset.command(require_var_positional=True)
    async def short(self, ctx: commands.Context, *, timezone: str):
        """
        Get the short identifier for the main `create` command.

        The list of acceptable timezones is here (the "TZ database name" column):
        https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List

        There is a fuzzy search, so you shouldn't need to enter the region.

        Please look at `[p]help tcset create` for more information.

        **Examples:**
            - `[p]tcset short New York`
            - `[p]tcset short UTC`
            - `[p]tcset short London`
            - `[p]tcset short Europe/London`
        """
        fuzzy_results = rapidfuzz.process.extract(  # type:ignore
            timezone, ZONE_KEYS, limit=2, score_cutoff=90
        )
        if len(fuzzy_results) > 1:
            return await ctx.send(
                "That search returned too many matches. Use the `Region/Location` format or "
                'you can see the full list here (the "TZ database name" '
                "column):\n<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List>"
            )
        if len(fuzzy_results) == 0:
            return await ctx.send(
                "That search didn't find any matches. You should be able to enter any "
                'major city, or you can see the full list here (the "TZ database name" '
                "column):\n<https://en.wikipedia.org/wiki/List_of_tz_database_time_zones#List>"
            )

        await ctx.send(
            f"{fuzzy_results[0][0]}'s short identifier is `{fuzzy_results[0][2]}` for 12 hour "
            f"time, or `{fuzzy_results[0][2]}-24h` for 24 hour time."
        )

    @commands.bot_has_permissions(manage_channels=True)
    @timechannelset.command()
    async def create(self, ctx: commands.Context, *, string: str):
        """
        Set up a time channel in this server.

        If you move the channel into a category, **click 'Keep Current Permissions' in the sync
        permissions dialogue.**

        **How to use this command:**

        First, use the `[p]tcset short <long_tz>` to get the short identifier for the
        timezone of your choice.

        Once you've got a short identifier from `tcset short`, you can use it in this command.
        Simply put curly brackets, `{` and `}` around it, and it will be replaced with the time.

        **For example**, running `[p]tcset short new york` gives a short identifier of `fv`.
        This can then be used like so:
        `[p]tcset create \N{CLOCK FACE TWO OCLOCK}\N{VARIATION SELECTOR-16} New York: {fv}`.

        You could also use two in one, for example
        `[p]tcset create UK: {ni} FR: {nr}`

        The default is 12 hour time, but you can use `{shortid-24h}` for 24 hour time,
        eg `{ni-24h}`

        **More Examples:**
            - `[p]tcset create \N{CLOCK FACE TWO OCLOCK}\N{VARIATION SELECTOR-16} New York: {fv}`
            - `[p]tcset create \N{GLOBE WITH MERIDIANS} UTC: {qw}`
            - `[p]tcset create {ni-24h} in London`
            - `[p]tcset create US Pacific: {qv-24h}`
        """
        assert isinstance(ctx.guild, Guild)  # guild_only check on parent command

        reps = gen_replacements()
        try:
            name = string.format(**reps)
        except KeyError as e:
            p = ctx.clean_prefix
            await ctx.send(
                f"`{e}` is not a valid replacement. Use `{p}tcset short <long_tz>` to get the "
                "short identifier for the timezone of your choice.\n\nExample: "
                f"`{p}tcset create New York: {{fv}}` or `{p}tcset create New York: {{fv-24h}}`"
            )
            return

        overwrites = {
            ctx.guild.default_role: discord.PermissionOverwrite(connect=False),
            ctx.guild.me: discord.PermissionOverwrite(manage_channels=True, connect=True),
        }
        reason = "Edited for timechannel - disable with `tcset remove`"
        channel = await ctx.guild.create_voice_channel(
            name=name, overwrites=overwrites, reason=reason
        )

        await self.config.guild(ctx.guild).timechannels.set_raw(  # type: ignore
            channel.id, value=string
        )

        await ctx.send(
            f"Done, {channel.mention} will now show those timezone(s). It will update every "
            "quarter hour. Regular users will be "
            "unable to connect. You can move this channel into a category if you wish, but "
            "**click 'Keep Current Permissions' in the sync permissions dialogue.** Note that "
            "you cannot move it under a private category."
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
        assert isinstance(ctx.guild, Guild)  # guild_only check on parent command

        data: dict
        async with self.config.guild(ctx.guild).timechannels() as data:
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
