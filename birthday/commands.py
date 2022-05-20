from __future__ import annotations

import asyncio
import datetime
from collections import defaultdict
from typing import TYPE_CHECKING

import discord
from dateutil.parser import ParserError
from dateutil.parser import parse as time_parser
from redbot.core import Config, commands
from redbot.core.commands import CheckFailure
from redbot.core.utils import AsyncIter
from redbot.core.utils.chat_formatting import box, pagify, warning
from redbot.core.utils.menus import start_adding_reactions
from redbot.core.utils.predicates import MessagePredicate, ReactionPredicate
from rich.table import Table  # type:ignore

from .abc import MixinMeta
from .consts import MAX_BDAY_MSG_LEN, MIN_BDAY_YEAR
from .converters import BirthdayConverter, TimeConverter
from .utils import channel_perm_check, format_bday_message, role_perm_check
from .vexutils import get_vex_logger, no_colour_rich_markup

log = get_vex_logger(__name__)


class BirthdayCommands(MixinMeta):
    async def setup_check(self, ctx: commands.Context) -> None:
        if ctx.guild is None:
            raise CheckFailure("This command can only be used in a server.")
            # this should have been caught by guild only check, but this keeps type checker happy
            # and idk what order decos run in so

        if not await self.check_if_setup(ctx.guild):
            await ctx.send(
                "This command is not available until the cog has been setup. "
                f"Get an admin to use `{ctx.clean_prefix}bdset interactive` to get started."
            )
            raise CheckFailure("cog needs setup")

    @commands.guild_only()  # type:ignore
    @commands.before_invoke(setup_check)  # type:ignore
    @commands.group(aliases=["bday"])
    async def birthday(self, ctx: commands.Context):
        """Set and manage your birthday."""

    @birthday.command(aliases=["add"])
    async def set(self, ctx: commands.Context, *, birthday: BirthdayConverter):
        """
        Set your birthday.

        You can optionally add in the year, if you are happy to share this.

        If you use a date in the format xx/xx/xx or xx-xx-xx MM-DD-YYYY is assumed.

        **Examples:**
            - `[p]bday set 24th September`
            - `[p]bday set 24th Sept 2002`
            - `[p]bday set 9/24/2002`
            - `[p]bday set 9-24-2002`
            - `[p]bday set 9-24`
        """
        # guild only check in group
        if TYPE_CHECKING:
            assert isinstance(ctx.author, discord.Member)

        # year as 1 means year not specified

        if birthday.year != 1 and birthday.year < MIN_BDAY_YEAR:
            await ctx.send(f"I'm sorry, but I can't set your birthday to before {MIN_BDAY_YEAR}.")
            return

        if birthday > datetime.datetime.utcnow():
            await ctx.send("You can't be born in the future!")
            return

        async with self.config.member(ctx.author).birthday() as bday:
            bday["year"] = birthday.year if birthday.year != 1 else None
            bday["month"] = birthday.month
            bday["day"] = birthday.day

        if birthday.year == 1:
            str_bday = birthday.strftime("%B %d")
        else:
            str_bday = birthday.strftime("%B %d, %Y")

        await ctx.send(f"Your birthday has been set as {str_bday}.")

    @birthday.command(aliases=["delete", "del"])
    async def remove(self, ctx: commands.Context):
        """Remove your birthday."""
        # guild only check in group
        if TYPE_CHECKING:
            assert isinstance(ctx.author, discord.Member)
            assert ctx.guild is not None

        m = await ctx.send("Are you sure?")
        start_adding_reactions(m, ReactionPredicate.YES_OR_NO_EMOJIS)
        check = ReactionPredicate.yes_or_no(m, ctx.author)  # type:ignore

        try:
            await self.bot.wait_for("reaction_add", check=check, timeout=60)
        except asyncio.TimeoutError:
            for reaction in ReactionPredicate.YES_OR_NO_EMOJIS:
                await m.remove_reaction(reaction, ctx.guild.me)
            return

        if check.result is False:
            await ctx.send("Cancelled.")
            return

        await self.config.member(ctx.author).birthday.clear()
        await ctx.send("Your birthday has been removed.")

    @birthday.command()
    async def upcoming(self, ctx: commands.Context, days: int = 7):
        """View upcoming birthdays, defaults to 7 days.

        **Examples:**
            - `[p]birthday upcoming` - default of 7 days
            - `[p]birthday upcoming 14` - 14 days
        """
        # guild only check in group
        if TYPE_CHECKING:
            assert isinstance(ctx.author, discord.Member)
            assert ctx.guild is not None

        if days < 1 or days > 365:
            await ctx.send("You must enter a number of days greater than 0 and smaller than 365.")
            return

        today_dt = datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

        all_birthdays: dict[int, dict[str, dict]] = await self.config.all_members(ctx.guild)

        parsed_bdays: dict[int, list[str]] = defaultdict(list)
        number_day_mapping: dict[int, str] = {}

        async for member_id, member_data in AsyncIter(all_birthdays.items(), steps=50):
            member = ctx.guild.get_member(member_id)
            if not isinstance(member, discord.Member):
                continue

            birthday_dt = datetime.datetime(
                year=member_data["birthday"]["year"] or 1,
                month=member_data["birthday"]["month"],
                day=member_data["birthday"]["day"],
            )

            if today_dt.month == birthday_dt.month and today_dt.day == birthday_dt.day:
                parsed_bdays[0].append(
                    member.mention
                    + (
                        ""
                        if birthday_dt.year == 1
                        else f" turns {today_dt.year - birthday_dt.year}"
                    )
                )
                number_day_mapping[0] = "Today"
                continue

            this_year_bday = birthday_dt.replace(year=today_dt.year)
            next_year_bday = birthday_dt.replace(year=today_dt.year + 1)
            next_birthday_dt = this_year_bday if this_year_bday > today_dt else next_year_bday

            diff = next_birthday_dt - today_dt
            if diff.days > days:
                continue

            next_bday_year = (
                today_dt.year if today_dt.year == next_birthday_dt.year else today_dt.year + 1
            )

            parsed_bdays[diff.days].append(
                member.mention
                + (
                    ""
                    if birthday_dt.year == 1
                    else (f" will turn {next_bday_year - birthday_dt.year}")
                )
            )
            number_day_mapping[diff.days] = next_birthday_dt.strftime("%B %d")

        if len(parsed_bdays) == 0:
            await ctx.send(f"No upcoming birthdays in the next {days} days.")
            return

        sorted_parsed_bdays = sorted(parsed_bdays.items(), key=lambda x: x[0])

        embed = discord.Embed(title="Upcoming Birthdays", colour=await ctx.embed_colour())

        if len(parsed_bdays) > 25:
            embed.description = "Too many days to display. I've had to stop at 25."

        for day, members in sorted_parsed_bdays:
            embed.add_field(name=number_day_mapping.get(day), value="\n".join(members))

        await ctx.send(embed=embed)


class BirthdayAdminCommands(MixinMeta):
    @commands.guild_only()
    @commands.is_owner()
    @commands.group(hidden=True)
    async def birthdaydebug(self, ctx: commands.Context):
        """Birthday debug commands."""

    @birthdaydebug.command(name="upcoming")
    async def debug_upcoming(self, ctx: commands.Context):
        await ctx.send_interactive(pagify(str(await self.config.all_members(ctx.guild))), "py")

    @commands.group()
    @commands.guild_only()  # type:ignore
    @commands.admin_or_permissions(manage_guild=True)
    async def bdset(self, ctx: commands.Context):
        """
        Birthday management commands for admins.

        Looking to set your own birthday? Use `[p]birthday set` or `[p]bday set`.
        """

    @commands.bot_has_permissions(manage_roles=True)
    @bdset.command()
    async def interactive(self, ctx: commands.Context):
        """Start interactive setup"""
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.me, discord.Member)
            assert isinstance(ctx.author, discord.Member)

        m: discord.Message = await ctx.send(
            "Just a heads up, you'll be asked for a message for when the user provided their birth"
            " year, a message for when they didn't, the channel to sent notifications, the role,"
            " and the time of day to send them.\n\nWhen you're ready, press the tick."
        )
        start_adding_reactions(m, ReactionPredicate.YES_OR_NO_EMOJIS)
        pred = ReactionPredicate.yes_or_no(m, ctx.author)  # type:ignore
        try:
            await self.bot.wait_for("reaction_add", check=pred, timeout=300)
        except asyncio.TimeoutError:
            await m.edit(
                content=(
                    f"Took too long to react, cancelling setup. Run `{ctx.clean_prefix}bdset"
                    " interactive` to start again."
                )
            )

        if pred.result is not True:
            await ctx.send("Okay, I'll cancel setup.")
            return

        # ============================== MSG WITH YEAR ==============================

        m = await ctx.send(
            "What message should I send if the user provided their birth year?\n\nYou can use the"
            " following variables: `mention`, `name`, `new_age`. Put curly brackets `{}` around"
            " them, for example: {mention} is now {new_age} years old!\n\nYou have 5 minutes."
        )

        try:
            pred = MessagePredicate.same_context(ctx)
            message = await self.bot.wait_for("message", check=pred, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send(
                f"Took too long to react, cancelling setup. Run `{ctx.clean_prefix}bdset"
                " interactive` to start again."
            )
            return

        message_w_year = message.content

        if len(message_w_year) > MAX_BDAY_MSG_LEN:
            await ctx.send(
                "That message is too long, please try again. Stay under"
                f" {MAX_BDAY_MSG_LEN} characters."
            )
            return

        # ============================== MSG WITHOUT YEAR ==============================

        m = await ctx.send(
            "What message should I send if the user didn't provide their birth year?\n\nYou can"
            " use the following variables: `mention`, `name`. Put curly brackets `{}` around them,"
            " for example: {mention}'s birthday is today! Happy birthday {name}\n\nYou have 5"
            " minutes."
        )

        try:
            pred = MessagePredicate.same_context(ctx)
            message = await self.bot.wait_for("message", check=pred, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send(
                f"Took too long to react, cancelling setup. Run `{ctx.clean_prefix}bdset"
                " interactive` to start again."
            )
            return

        message_wo_year = message.content

        if len(message_wo_year) > MAX_BDAY_MSG_LEN:
            await ctx.send(
                f"That message is too long, please try again. Stay under {MAX_BDAY_MSG_LEN}"
                " characters."
            )
            return

        # ============================== CHANNEL ==============================

        m = await ctx.send(
            "Where would you like to send notifications? I will ignore any message with an invalid"
            " channel.\n\nYou have 5 minutes."
        )

        try:
            pred = MessagePredicate.valid_text_channel(ctx)
            await self.bot.wait_for("message", check=pred, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send(
                f"Took too long to react, cancelling setup. Run `{ctx.clean_prefix}bdset"
                " interactive` to start again."
            )
            return

        channel: discord.TextChannel = pred.result  # type:ignore
        if error := channel_perm_check(ctx.me, channel):
            await ctx.send(
                warning(
                    f"{error} Please make sure"
                    " you rectify this as soon as possible, but I'll let you continue the setup."
                )
            )

        channel_id = pred.result.id  # type:ignore

        # ============================== ROLE ==============================

        m = await ctx.send(
            "What role should I assign to users who have their birthday today? I will ignore any"
            " message which isn't a role.\n\nYou can mention the role, give its exact name, or its"
            " ID.\n\nYou have 5 minutes."
        )

        try:
            pred = MessagePredicate.valid_role(ctx)
            await self.bot.wait_for("message", check=pred, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send(
                f"Took too long to react, cancelling setup. Run `{ctx.clean_prefix}bdset"
                " interactive` to start again."
            )
            return

        # no need to check hierarchy for author, since command is locked to admins
        if error := role_perm_check(ctx.me, pred.result):  # type:ignore
            await ctx.send(
                warning(
                    f"{error} Please make"
                    " sure you rectify this as soon as possible, but I'll let you continue the"
                    " setup."
                )
            )

        role_id = pred.result.id  # type:ignore

        # ============================== TIME ==============================

        def time_check(m: discord.Message):
            if m.author == ctx.author and m.channel == ctx.channel is False:
                return False

            try:
                time_parser(m.content)
            except ParserError:
                return False

            return True

        m = await ctx.send(
            "What time of day should I send the birthday message? Please use the UTC time, for"
            " example `12AM` for midnight or `7:00`. I will ignore any invalid input. I will"
            " ignore minutes.\n\nYou have 5 minutes."
        )

        try:
            ret = await self.bot.wait_for("message", check=time_check, timeout=300)
        except asyncio.TimeoutError:
            await ctx.send(
                f"Took too long to react, cancelling setup. Run `{ctx.clean_prefix}bdset"
                " interactive` to start again."
            )
            return

        full_time = time_parser(ret.content)
        full_time = full_time.replace(tzinfo=datetime.timezone.utc, year=1, month=1, day=1)

        midnight = datetime.datetime.now(tz=datetime.timezone.utc).replace(
            year=1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        time_utc_s = int((full_time - midnight).total_seconds())

        try:
            await ctx.trigger_typing()  # dpy 1
        except AttributeError:
            await ctx.typing()  # dpy 2

        p = ctx.clean_prefix

        setup_state = 5
        errors = ""
        try:
            format_bday_message(message_w_year, ctx.author, 1)
        except KeyError as e:
            setup_state -= 1
            errors += warning(
                "You birthday message **with year** can only include `{mention}`, `{name}`"
                " and `{new_age}`. You can't have anything else in `{}`. You did"
                f" `{{{e.args[0]}}}` which is invalid.\nYou can correct this with `{p}bdset"
                " msgwithyear`\n\n"
            )

        try:
            format_bday_message(message_wo_year, ctx.author)
        except KeyError as e:
            e = e
            setup_state -= 1
            errors += warning(
                "You birthday message **without year** can only include `{mention}` and"
                f" `{{name}}`. You can't have anything else in `{{}}`. You did `{{{e.args[0]}}}`"
                f" which is invalid.\nYou can correct this with `{p}bdset msgwithoutyear`\n\n"
            )

        async with self.config.guild(ctx.guild).all() as conf:
            conf["time_utc_s"] = time_utc_s
            conf["message_w_year"] = message_w_year
            conf["message_wo_year"] = message_wo_year
            conf["channel_id"] = channel_id
            conf["role_id"] = role_id
            conf["setup_state"] = setup_state

        if errors:
            await ctx.send(
                errors
                + f"Once you fix this, members will be able to use `{p}birthday add` to add their"
                " birthday and messages will be sent."
            )
            return

        await ctx.send(
            f"All set! You can change these settings at any time with `{p}bdset` and view them"
            f" with `{p}bdset settings`. Members can now use `{p}birthday add` to add their"
            " birthday."
        )

    @bdset.command()
    async def settings(self, ctx: commands.Context):
        """View your current settings"""
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.me, discord.Member)

        table = Table("Name", "Value", title="Settings for this server")

        async with self.config.guild(ctx.guild).all() as conf:
            channel = ctx.guild.get_channel(conf["channel_id"])
            table.add_row("Channel", channel.name if channel else "Channel deleted")

            role = ctx.guild.get_role(conf["role_id"])
            table.add_row("Role", role.name if role else "Role deleted")

            if conf["time_utc_s"] is None:
                time = "invalid"
            else:
                time = datetime.datetime.utcfromtimestamp(conf["time_utc_s"]).strftime("%H:%M UTC")
                table.add_row("Time", time)

            message_w_year = conf["message_w_year"] or "No message set"
            message_wo_year = conf["message_wo_year"] or "No message set"

        warnings = "\n"
        if (error := role is None) or (error := role_perm_check(ctx.me, role)):
            if isinstance(error, bool):
                error = "Role deleted."
            warnings += warning(error + " This may result in repeated notifications.\n")
        if (error := channel is None) or (error := channel_perm_check(ctx.me, channel)):
            if isinstance(error, bool):
                error = "Channel deleted."
            warnings += warning(error + " You won't get birthday notifications.\n")

        final_table = no_colour_rich_markup(table)
        message = (
            final_table
            + "\nMessage with year:\n"
            + box(message_w_year)
            + "\nMessage without year:\n"
            + box(message_wo_year)
            + warnings
        )
        await ctx.send(message)

    @bdset.command()
    async def time(self, ctx: commands.Context, *, time: TimeConverter):
        """
        Set the time of day for the birthday message.

        Minutes are ignored.

        **Examples:**
            - `[p]bdset time 7:00` - set the time to 7:45AM UTC
            - `[p]bdset time 12AM` - set the time to midnight UTC
            - `[p]bdset time 3PM` - set the time to 3:00PM UTC
        """
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None

        midnight = datetime.datetime.utcnow().replace(
            year=1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        time_utc_s = int((time - midnight).total_seconds())

        async with self.config.guild(ctx.guild).all() as conf:
            old = conf["time_utc_s"]
            conf["time_utc_s"] = time_utc_s

            if old is None:
                conf["setup_state"] += 1

        m = (
            "Time set! I'll send the birthday message and update the birthday role at"
            f" {time.strftime('%H:%M')} UTC."
        )

        if old is not None:
            old_dt = datetime.datetime.utcfromtimestamp(old)
            if time > old_dt and time > datetime.datetime.utcnow():
                m += (
                    "\n\nThe time you set is after the time I currently send the birthday message,"
                    " so the birthday message will be sent for a second time."
                )

        await ctx.send(m)

    @bdset.command()
    async def msgwithoutyear(self, ctx: commands.Context, *, message: str):
        """
        Set the message to be send when the user did not provide a year.

        **Placeholders:**
            - `{name}` - the user's name
            - `{mention}` - an @ mention of the user

            All the placeholders are optional.

        **Examples:**
            - `[p]bdset msgwithoutyear Happy birthday {mention}!`
            - `[p]bdset msgwithoutyear {mention}'s birthday is today! Happy birthday {name}.`
        """
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.author, discord.Member)

        if len(message) > MAX_BDAY_MSG_LEN:
            await ctx.send(
                f"That message is too long! It needs to be under {MAX_BDAY_MSG_LEN} characters."
            )

        try:
            format_bday_message(message, ctx.author, 1)
        except KeyError as e:
            await ctx.send(
                f"You have a placeholder `{{{e.args[0]}}}` that is invalid. You can only include"
                " `{name}` and `{mention}` for the message without a year."
            )
            return

        async with self.config.guild(ctx.guild).all() as conf:
            if conf["message_wo_year"] is None:
                conf["setup_state"] += 1

            conf["message_wo_year"] = message

        await ctx.send("Message set. Here's how it will look:")
        await ctx.send(
            format_bday_message(message, ctx.author),
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    @bdset.command()
    async def msgwithyear(self, ctx: commands.Context, *, message: str):
        """
        Set the message to be send when the user did provide a year.

        **Placeholders:**
            - `{name}` - the user's name
            - `{mention}` - an @ mention of the user
            - `{new_age}` - the user's new age

            All the placeholders are optional.

        **Examples:**
            - `[p]bdset msgwithyear {mention} has turned {new_age}, happy birthday!`
            - `[p]bdset msgwithyear {name} is {new_age} today! Happy birthday {mention}!`
        """
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.author, discord.Member)

        if len(message) > MAX_BDAY_MSG_LEN:
            await ctx.send(
                f"That message is too long! It needs to be under {MAX_BDAY_MSG_LEN} characters."
            )

        try:
            format_bday_message(message, ctx.author, 1)
        except KeyError as e:
            await ctx.send(
                f"You have a placeholder `{{{e.args[0]}}}` that is invalid. You can only include"
                " `{name}`, `{mention}` and `{new_age}` for the message with a year."
            )
            return

        async with self.config.guild(ctx.guild).all() as conf:
            if conf["message_w_year"] is None:
                conf["setup_state"] += 1

            conf["message_w_year"] = message

        await ctx.send("Message set. Here's how it will look, if you're turning 20:")
        await ctx.send(
            format_bday_message(message, ctx.author, 20),
            allowed_mentions=discord.AllowedMentions(users=True),
        )

    @bdset.command()
    async def channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """
        Set the channel where the birthday message will be sent.

        **Example:**
            - `[p]bdset channel #birthdays` - set the channel to #birthdays
        """
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.me, discord.Member)

        if channel.permissions_for(ctx.me).send_messages is False:
            await ctx.send(
                "I can't do that because I don't have permissions to send messages in"
                f" {channel.mention}."
            )
            return

        async with self.config.guild(ctx.guild).all() as conf:
            if conf["channel_id"] is None:
                conf["setup_state"] += 1

            conf["channel_id"] = channel.id

        await ctx.send(f"Channel set to {channel.mention}.")

    @commands.bot_has_permissions(manage_roles=True)
    @bdset.command()
    async def role(self, ctx: commands.Context, *, role: discord.Role):
        """
        Set the role that will be given to the user on their birthday.

        You can give the exact name or a mention.

        **Example:**
            - `[p]bdset role @Birthday` - set the role to @Birthday
            - `[p]bdset role Birthday` - set the role to @Birthday without a mention
            - `[p]bdset role 418058139913063657` - set the role with an ID
        """
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.me, discord.Member)

        # no need to check hierarchy for author, since command is locked to admins
        if ctx.me.top_role < role:
            await ctx.send(f"I can't use {role.name} because it is higher than my highest role.")
            return

        async with self.config.guild(ctx.guild).all() as conf:
            if conf["role_id"] is None:
                conf["setup_state"] += 1

            conf["role_id"] = role.id

        await ctx.send(f"Role set to {role.name}.")

    @bdset.command()
    async def force(
        self, ctx: commands.Context, user: discord.Member, *, birthday: BirthdayConverter
    ):
        """
        Force-set a specific user's birthday.

        You can @ mention any user or type out their exact name. If you're typing out a name with
        spaces, make sure to put quotes around it (`"`).

        **Examples:**
            - `[p]bdset set @User 1-1-2000` - set the birthday of `@User` to 1/1/2000
            - `[p]bdset set User 1/1` - set the birthday of `@User` to 1/1/2000
            - `[p]bdset set "User with spaces" 1-1` - set the birthday of `@User with spaces`
            to 1/1
            - `[p]bdset set 354125157387344896 1/1/2000` - set the birthday of `@User` to 1/1/2000
        """
        if birthday.year != 1 and birthday.year < MIN_BDAY_YEAR:
            await ctx.send(f"I'm sorry, but I can't set a birthday to before {MIN_BDAY_YEAR}.")
            return

        if birthday > datetime.datetime.utcnow():
            await ctx.send("You can't be born in the future!")
            return

        async with self.config.member(user).birthday() as bday:
            bday["year"] = birthday.year if birthday.year != 1 else None
            bday["month"] = birthday.month
            bday["day"] = birthday.day

        if birthday.year == 1:
            str_bday = birthday.strftime("%B %d")
        else:
            str_bday = birthday.strftime("%B %d, %Y")

        await ctx.send(f"{user.name}'s birthday has been set as {str_bday}.")

    @commands.is_owner()
    @bdset.command()
    async def zemigrate(self, ctx: commands.Context):
        """
        Import data from ZeCogs'/flare's fork of Birthdays cog
        """
        # group has guild check
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if await self.config.guild(ctx.guild).setup_state() != 0:
            m = await ctx.send(
                "You have already started setting the cog up. Are you sure? This will overwrite"
                " your old data for all guilds."
            )

            start_adding_reactions(m, ReactionPredicate.YES_OR_NO_EMOJIS)
            pred = ReactionPredicate.yes_or_no(m, ctx.author)  # type:ignore
            try:
                await self.bot.wait_for("reaction_add", check=pred, timeout=60)
            except asyncio.TimeoutError:
                await ctx.send("Timeout. Cancelling.")
                return

            if pred.result is False:
                await ctx.send("Cancelling.")
                return

        bday_conf = Config.get_conf(
            None,
            int(
                "402907344791714442305425963449545260864366380186701260757993729164269683092560089"
                "8581468610241444437790345710548026575313281401238342705437492295956906331"
            ),
            cog_name="Birthdays",
        )

        for guild_id, guild_data in (await bday_conf.all_guilds()).items():
            guild = self.bot.get_guild(int(guild_id))
            if guild is None:
                continue
            new_data = {
                "channel_id": guild_data.get("channel", None),
                "role_id": guild_data.get("role", None),
                "message_w_year": "{mention} is now **{new_age} years old**. :tada:",
                "message_wo_year": "It's {mention}'s birthday today! :tada:",
                "time_utc_s": 0,  # UTC midnight
                "setup_state": 5,
            }
            await self.config.guild(guild).set_raw(value=new_data)

        bday_conf.init_custom("GUILD_DATE", 2)
        all_member_data = await bday_conf.custom("GUILD_DATE").all()  # type:ignore
        if "backup" in all_member_data:
            del all_member_data["backup"]

        for guild_id, guild_data in all_member_data.items():
            guild = self.bot.get_guild(int(guild_id))
            if guild is None:
                continue
            for day, users in guild_data.items():
                for user_id, year in users.items():
                    dt = datetime.datetime.fromordinal(int(day))

                    if year is None or year < MIN_BDAY_YEAR:
                        year = 1

                    try:
                        dt = dt.replace(year=year)
                    except (OverflowError, ValueError):  # flare's users are crazy
                        dt = dt.replace(year=1)

                    new_data = {
                        "year": dt.year if dt.year != 1 else None,
                        "month": dt.month,
                        "day": dt.day,
                    }
                    await self.config.member_from_ids(guild_id, user_id).birthday.set(new_data)

        await ctx.send(
            "All set. You can now configure the messages and time to send with other commands"
            " under `[p]bdset`, if you would like to change it from ZeLarp's. This is per-guild."
        )

    @bdset.command()
    async def stop(self, ctx: commands.Context):
        """
        Stop the cog from sending birthday messages and giving roles in the server.
        """
        await self.config.guild(ctx.guild).clear()
        await ctx.send(
            "Birthday messages and roles have been stopped. Configuration has been reset, but the"
            " birthdays of users have been kept in case you need them again."
        )
