import datetime
from typing import Union

import discord
import pandas
from redbot.core import commands
from redbot.core.utils.chat_formatting import humanize_timedelta, inline, pagify, text_to_file

from .abc import MixinMeta
from .consts import SECONDS_IN_DAY
from .plot import plot

old_uptime = None


class BUCommands(MixinMeta):
    @commands.command(name="uptime")
    async def uptime_command(self, ctx: commands.Context, num_days: int = 30):
        """
        Get [botname]'s uptime percent over the last 30 days, and when I was last restarted.

        The default value for `num_days` is `30`. You can put `0` days for all-time data.
        Otherwise, it needs to be `5` or more.

        Note: embeds must be enabled for this rich data to show

        **Examples:**
            - `[p]uptime`
            - `[p]uptime 0` (for all-time data)
            - `[p]uptime 7`
        """
        # MOSTLY FROM CORE'S UPTIME COMMAND
        # TODO: use datetime_to_timestamp in utils when red/dpy uses timezone aware datetimes
        since = self.bot.uptime.strftime("%Y-%m-%d %H:%M:%S")
        delta = datetime.datetime.utcnow() - self.bot.uptime
        uptime_str = humanize_timedelta(timedelta=delta) or "Less than one second."
        description = f"Been up for: **{uptime_str}** (since {since} UTC)."
        # END

        if not await ctx.embed_requested():
            # (maybe) TODO: implement non-embed version
            return await ctx.send(description)

        if num_days == 0:
            num_days = 9999  # this works, trust me
        elif num_days < 5:
            return await ctx.send("The minimum number of days is `5`.")

        data = await self.get_data(num_days)

        embed = discord.Embed(description=description, colour=await ctx.embed_colour())

        botname = ctx.me.name
        embed.add_field(
            name="Uptime (connected to Discord):", value=inline(f"{data.connected_uptime}%")
        )
        embed.add_field(name=f"Uptime ({botname} ready):", value=inline(f"{data.cog_uptime}%"))

        if data.seconds_data_collected - data.total_secs_connected > 60:
            # dont want to include stupidly small downtime
            downtime_info = (
                f"`{data.downtime}`\n`{data.net_downtime}` of this was due network issues."
            )
            embed.add_field(name="Downtime:", value=downtime_info, inline=False)

        seconds_since_first_load = (datetime.datetime.utcnow() - data.first_load).total_seconds()
        content: Union[None, str]
        if seconds_since_first_load < 60 * 15:  # 15 mins
            content = "Data tracking only started in the last few minutes. Data may be inaccurate."
        elif len(data.expected_index) == 1:
            content = None
            embed.set_footer(text="Data is only for today.")
        else:
            content = None
            embed.set_footer(
                text=(
                    f"Data is for the last {len(data.expected_index)} days, and today.\n"
                    f"You can view a graph of this data with {ctx.prefix}uptimegraph"
                )
            )

        await ctx.send(content, embed=embed)

    @commands.command()
    async def downtime(self, ctx: commands.Context, num_days: int = 30):
        """
        Check [botname] downtime over the last 30 days.

        The default value for `num_days` is `30`. You can put `0` days for all-time data.
        Otherwise, it needs to be `5` or more.

        **Examples:**
            - `[p]uptime`
            - `[p]uptime 0` (for all-time data)
            - `[p]uptime 7`
        """
        data = await self.get_data(num_days)
        midnight = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        if data.first_load > midnight:  # cog was first loaded today
            return await ctx.send(
                "It looks like there's been no recorded downtime.\n_This excludes any downtime "
                "today._"
            )
        msg = ""
        date: pandas.Timestamp
        for date in data.expected_index:
            if date == midnight:
                continue
            if SECONDS_IN_DAY - data.daily_connected_data[date] > 60:
                date_fmted = date.strftime("%Y-%m-%d")  # type:ignore  # stubs incorrect
                msg += (
                    f"\n**{date_fmted}**: `{data.date_downtime(date)}`, of which "
                    f"`{data.date_net_downtime(date)}` was due to network issues."
                )

        if not msg:
            await ctx.send(
                "It looks like there's been no recorded downtime.\n_This excludes any downtime "
                "today._"
            )
        else:
            full = (
                "_Timezone: UTC, date format: Year-Month-Day_\n_This excludes any "
                f"downtime today._\n\n{msg}"
            )
            paged = pagify(full, page_length=1000)
            await ctx.send_interactive(paged)

    @commands.command()
    async def uptimegraph(self, ctx: commands.Context, num_days: int = 30):
        if num_days == 0:
            num_days = 9999  # this works, trust me
        elif num_days < 5:
            return await ctx.send("The minimum number of days is `5`.")

        data = await self.get_data(num_days)
        sr = data.daily_connected_percentages()

        if len(sr) < 2:
            return await ctx.send("Give me a few more days to collect data!")

        async with ctx.typing():
            file = await plot(sr)
        await ctx.send(
            content=(
                "This excludes today. Days with uptime under `99.7%` will be labelled, if any."
            ),
            file=file,
        )

    @commands.is_owner()
    @commands.command()
    async def uptimeexport(self, ctx: commands.Context):
        """
        Export my uptime data to CSV

        The numbers represent uptime, so 86400 means 100% for that day (86400 seconds in 1 day).

        Everything is in UTC.

        Connected is the bot being connected to Discord.

        Cog loaded is the cog being loaded but not necessarily connected to Discord.

        Therefore, connected should always be equal to or lower than cog loaded.
        """
        df = pandas.concat([self.connected_cache, self.cog_loaded_cache], axis=1)
        data = df.to_csv(index_label="Date", header=["Connected", "Cog loaded"])
        assert data is not None
        await ctx.send("Here is your file.", file=text_to_file(data, "betteruptime.csv"))

    # mainly for users who installed, then uninstalled and found that uptime
    # was very low. main reason is first_load is tracked so this would skew everything
    @commands.is_owner()
    @commands.command(usage="")
    async def resetbu(self, ctx: commands.Context, confirm: bool = False):
        """Reset the cog's data."""
        p = ctx.clean_prefix
        if not confirm:
            return await ctx.send(
                "⚠ This will reset the all your uptime data. This action is **irreversible**. "
                "All the uptime data will be **lost forever** ⚠\n"
                f"To proceed, please run **`{p}resetbu 1`**"
            )
        if self.main_loop:
            self.main_loop.cancel()

        await self.config.version.clear()
        await self.config.cog_loaded.clear()
        await self.config.connected.clear()
        await self.config.first_load.clear()

        self.ready = False

        await ctx.send(
            f"Data has been reset. **Please run `{p}reload betteruptime` to finish the process.**"
        )
