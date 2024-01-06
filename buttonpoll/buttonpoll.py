from __future__ import annotations

import argparse
import datetime
import os
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, List, Literal, Optional

import discord
from discord.channel import TextChannel
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from redbot.core.commands import BadArgument, parse_timedelta
from redbot.core.utils.chat_formatting import humanize_list, pagify

from .components.setup import SetupYesNoView, StartSetupView
from .poll import Poll, PollOption, PollView
from .vexutils import format_help, format_info, get_vex_logger
from .vexutils.chat import datetime_to_timestamp
from .vexutils.loop import VexLoop

log = get_vex_logger(__name__)


# Originally from sinbad's scheduler cog
# https://github.com/mikeshardmind/SinbadCogs/blob/d59fd7bc69833dc24f9e74ec59e635ffe593d43f/scheduler/converters.py#L23
class NoExitParser(argparse.ArgumentParser):
    def error(self, message):
        raise BadArgument(message)


class ButtonPoll(commands.Cog):
    """
    Create polls with buttons, and get a pie chart afterwards!
    """

    __author__ = "@vexingvexed"
    __version__ = "1.2.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_guild(
            poll_settings={},
            poll_user_choices={},
            historic_poll_settings={},
            historic_poll_user_choices={},
        )

        self.loop = bot.loop.create_task(self.buttonpoll_loop())
        self.loop_meta = VexLoop("ButtonPoll", 60.0)

        self.polls: List[Poll] = []

        bot.add_dev_env_value("bpoll", lambda _: self)

        self.plot_executor = ThreadPoolExecutor(
            max_workers=16, thread_name_prefix="buttonpoll_plot"
        )

    async def red_delete_data_for_user(
        self,
        *,
        requester: Literal["discord_deleted_user", "owner", "user", "user_strict"],
        user_id: int,
    ):
        for g_id, g_polls in (await self.config.all_guilds()).items():
            for poll_id, poll in g_polls["poll_user_choices"].items():
                for user, vote in poll.items():
                    if user == str(user_id):
                        async with self.config.guild_from_id(
                            g_id
                        ).poll_user_choices() as user_choices:
                            del user_choices[poll_id][user]

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def cog_unload(self) -> None:
        self.loop.cancel()
        self.bot.remove_dev_env_value("bpoll")

        # if the cog will be reloaded, best to clean up views as they are re-initialised on load
        for poll in self.polls:
            poll.view.stop()

        self.plot_executor.shutdown(wait=False)

        log.verbose("buttonpoll successfully unloaded")

    @commands.command(hidden=True)
    async def buttonpollinfo(self, ctx: commands.Context):
        main = await format_info(ctx, self.qualified_name, self.__version__)
        return await ctx.send(main)

    async def cog_load(self) -> None:
        # re-initialise views
        all_polls = await self.config.all_guilds()
        for guild_polls in all_polls.values():
            for poll in guild_polls["poll_settings"].values():
                obj_poll = Poll.from_dict(poll, self)
                self.polls.append(obj_poll)
                self.bot.add_view(obj_poll.view, message_id=obj_poll.message_id)
                log.debug(f"Re-initialised view for poll {obj_poll.unique_poll_id}")

    @commands.guild_only()  # type:ignore
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command(aliases=["poll", "bpoll"])
    async def buttonpoll(self, ctx: commands.Context, chan: Optional[TextChannel] = None):
        """
        Start a button-based poll

        This is an interactive setup. By default the current channel will be used,
        but if you want to start a poll remotely you can send the channel name
        along with the buttonpoll command.

        **Examples:**
        - `[p]buttonpoll` - start a poll in the current channel
        - `[p]buttonpoll #polls` start a poll somewhere else
        """
        channel = chan or ctx.channel
        if TYPE_CHECKING:
            assert isinstance(channel, (TextChannel, discord.Thread))
            assert isinstance(ctx.author, discord.Member)  # we are in a guild...

        if not channel.permissions_for(ctx.author).send_messages:  # type:ignore
            return await ctx.send(
                f"You don't have permission to send messages in {channel.mention}, so I can't "
                "start a poll there."
            )
        if not channel.permissions_for(ctx.me).send_messages:  # type:ignore
            return await ctx.send(
                f"I don't have permission to send messages in {channel.mention}, so I can't "
                "start a poll there."
            )
        if not channel.permissions_for(ctx.me).attach_files:  # type:ignore
            await ctx.send(
                "\N{WARNING SIGN}\N{VARIATION SELECTOR-16} I don't have permission to attach "
                "files in that channel. I won't be able to send a pie chart."
            )

        view = StartSetupView(author=ctx.author, channel=channel, cog=self)
        await ctx.send("Click below to start a poll!", view=view)

    @commands.guild_only()  # type:ignore
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def advstartpoll(self, ctx: commands.Context, *, arguments: str = ""):
        """
        Advanced users: create a pull using command arguments

        The help text for this command is too long to fit in the help command. Just run
        `[p]advstartpoll` to see it.
        """
        if not arguments:
            return await ctx.send(
                """
\N{WARNING SIGN}\N{VARIATION SELECTOR-16} **This command is for advanced users only.
You should use `[p]buttonpoll` or the slash command `poll` for a more user-friendly experience.**

\N{WARNING SIGN}\N{VARIATION SELECTOR-16} This command does not check for permissions. Please
check I have permission to send messages in the channel you want to start the poll in. I'll also
need permission to attach files if you want a pie chart.

**Required arguments:**
- `--channel ID`: The channel ID to start the poll in
- `--question string`: The question to ask
- `--option string`: The options to provide. You can provide between 2 and 5 options. \
Repeat this argument for each option.

**You must also provide one of the following:**
- `--duration integer`: The duration of the poll in seconds. Must be at least 60. \
Polls may finish up to 60 seconds late, so don't rely on precision timing.
- `--end string`: The time to end the poll. \
Must be in the format `YYYY-MM-DD HH:MM:SS` (24 hour time) or a Unix timestamp. This is in UTC.

If both are provided, `--duration` will be used.

**Optional arguments:**
- `--description string`: A description for the poll. Use \\n for new lines.
- `--allow-vote-change`: Allow users to change their vote.
- `--view-while-live`: Allow users to view the poll results so far while it is live.
- `--send-new-msg`: Send a new message when the poll is finished.
- `--silent`: Suppress all error messages that occur during the command.

For the final four optional arguments, they are false if not included, and true if included.

**Examples:**
- `[p]advstartpoll --channel 123456789 --question What is your favourite colour? --option Red \
--option Blue --option Green --option None of them --duration 3600 --description \
Choose wisely!`
- `[p]advstartpoll --channel 123456789 --question What is your favourite colour? --option Red \
--option Blue --option Green --option None of them --end 2021-01-01 12:00:00 \
--allow-vote-change --send-new-msg`"""
            )

        parser = NoExitParser(
            description="Create a poll using just command arguments.",
            add_help=False,
        )
        parser.add_argument("--channel", type=int, required=True)
        parser.add_argument("--question", type=str, required=True, nargs="+")
        parser.add_argument("--option", type=str, action="append", required=True, nargs="+")
        parser.add_argument("--duration", type=int)
        parser.add_argument("--end", type=str, nargs="+")
        parser.add_argument("--description", type=str, nargs="+", default="")
        parser.add_argument("--allow-vote-change", action="store_true")
        parser.add_argument("--view-while-live", action="store_true")
        parser.add_argument("--send-new-msg", action="store_true")
        parser.add_argument("--silent", action="store_true")
        try:
            args = parser.parse_args(arguments.split())
        except Exception as e:
            return await ctx.send(f"Error parsing arguments: {e}")

        if args.duration is None and args.end is None:
            if not args.silent:
                await ctx.send("You must provide either a duration or an end time.")
            return

        channel = self.bot.get_channel(args.channel)
        if not channel:
            if not args.silent:
                await ctx.send("That channel does not exist.")
            return

        unique_poll_id = (  # rand hex, interaction ID, first 25 chars of sanitised question
            os.urandom(5).hex()
            + "_"
            + str(ctx.message.id)
            + "_"
            + "".join(" ".join(c) for c in args.option if " ".join(c).isalnum())[:25]
        )

        if args.duration:
            poll_finish = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
                seconds=args.duration
            )
        else:
            try:
                poll_finish = datetime.datetime.strptime(
                    " ".join(args.end), "%Y-%m-%d %H:%M:%S"
                ).replace(tzinfo=datetime.timezone.utc)
            except ValueError:
                try:
                    poll_finish = datetime.datetime.fromtimestamp(
                        int(args.end), tz=datetime.timezone.utc
                    )
                except ValueError:
                    if not args.silent:
                        await ctx.send(
                            "Invalid end time. Must be in the format `YYYY-MM-DD HH:MM:SS` "
                            "(24 hour time) or a Unix timestamp."
                        )
                    return

        poll = Poll(
            unique_poll_id=unique_poll_id,
            guild_id=channel.guild.id,
            channel_id=channel.id,
            question=" ".join(args.question),
            description=" ".join(args.description) or "",
            options=[PollOption(" ".join(o), discord.ButtonStyle.primary) for o in args.option],
            allow_vote_change=args.allow_vote_change,
            view_while_live=args.view_while_live,
            send_msg_when_over=args.send_new_msg,
            poll_finish=poll_finish,
            cog=self,
            view=None,
        )
        poll.view = PollView(self.config, poll)

        e = discord.Embed(
            colour=await self.bot.get_embed_colour(channel),
            title=poll.question,
            description=poll.description or None,
        )
        e.add_field(
            name=(
                f"Ends at {datetime_to_timestamp(poll.poll_finish)}, "
                f"{datetime_to_timestamp(poll.poll_finish, 'R')}"
            ),
            value=(
                "You have one vote, "
                + (
                    "and you can change it by clicking a new button."
                    if poll.allow_vote_change
                    else "and you can't change it."
                )
                + (
                    "\nYou can view the results while the poll is live, once you vote."
                    if poll.view_while_live
                    else "\nYou can view the results when the poll finishes."
                )
            ),
        )

        m = await channel.send(embed=e, view=poll.view)  # type:ignore

        poll.set_msg_id(m.id)
        async with self.config.guild(channel.guild).poll_settings() as poll_settings:
            poll_settings[poll.unique_poll_id] = poll.to_dict()
        self.polls.append(poll)

    @app_commands.guild_only()
    @app_commands.default_permissions(manage_messages=True)
    @app_commands.describe(
        channel="Channel to start the poll in.",
        question="Question to ask.",
        description="An optional description.",
        duration="Duration of the poll. Examples: 1 day, 1 minute, 4 hours",
        choice1="First choice.",
        choice2="Second choice.",
        choice3="Optional third choice.",
        choice4="Optional fourth choice.",
        choice5="Optional fifth choice.",
    )
    @app_commands.command(name="poll", description="Start a button-based poll.")
    async def poll_slash(
        self,
        interaction: discord.Interaction,
        channel: Optional[discord.TextChannel],
        question: app_commands.Range[str, 1, 256],
        description: Optional[app_commands.Range[str, 1, 4000]],
        duration: app_commands.Range[str, 1, 20],
        choice1: app_commands.Range[str, 1, 80],
        choice2: app_commands.Range[str, 1, 80],
        choice3: Optional[app_commands.Range[str, 1, 80]],
        choice4: Optional[app_commands.Range[str, 1, 80]],
        choice5: Optional[app_commands.Range[str, 1, 80]],
    ):
        try:
            parsed_duration = parse_timedelta(duration or "")
        except Exception:
            await interaction.response.send_message(
                "Invalid time format. Please use a valid time format, for example `1 day`, "
                "`1 minute`, `4 hours`.",
                ephemeral=True,
            )
            return
        if parsed_duration is None:
            await interaction.response.send_message(
                "Invalid time format. Please use a valid time format, for example `1 day`, "
                "`1 minute`, `4 hours`.",
                ephemeral=True,
            )
            return

        str_options: list[str | None] = [choice1, choice2, choice3, choice4, choice5]
        while None in str_options:
            str_options.remove(None)

        if len(str_options) < 2:
            await interaction.response.send_message(
                "You must provide at least two unique choices.",
                ephemeral=True,
            )
            return

        if len(str_options) != len(set(str_options)):
            await interaction.response.send_message(
                "You can't have duplicate choices.",
                ephemeral=True,
            )
            return

        options: list[PollOption] = []
        for option in str_options:
            options.append(PollOption(option, discord.ButtonStyle.primary))

        await interaction.response.send_message(
            "Great! Just a few quick questions now.",
            view=SetupYesNoView(
                author=interaction.user,
                channel=channel or interaction.channel,
                cog=self,
                question=question,
                description=description or "",
                time=parsed_duration,
                options=options,
            ),
            ephemeral=True,
        )

    @commands.guild_only()  # type:ignore
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command(aliases=["voters"])
    async def getvoters(self, ctx: commands.Context, message_id: int):
        """
        Fetch the current voters for a running poll

        **Arguments**
        - `message_id`: (integer) The ID of the poll message
        """
        conf = await self.config.guild(ctx.guild).all()
        for poll in self.polls:
            if poll.message_id == message_id:
                obj_poll = poll
                votes = conf["poll_user_choices"].get(obj_poll.unique_poll_id, {})
                break
        else:  # not currently active so look through historic polls
            for poll in conf["historic_poll_settings"].values():
                if int(poll["message_id"]) == message_id:
                    obj_poll = Poll.from_dict(poll, self)
                    votes = conf["historic_poll_user_choices"].get(obj_poll.unique_poll_id, {})
                    break
            else:
                return await ctx.send("Could not find poll associated with this message!")

        if not votes:
            return await ctx.send("This poll has no votes yet!")

        options = {}
        for user_id, vote in votes.items():
            if vote not in options:
                options[vote] = []
            user = ctx.guild.get_member(int(user_id))
            if user:
                mention = user.mention
            else:
                mention = f"<@{user_id}>"
            options[vote].append(mention)

        sorted_votes = sorted(options.items(), key=lambda x: len(x[1]), reverse=True)

        text = ""
        for vote, voters in sorted_votes:
            text += (
                f"**{vote}** has {len(voters)} {'votes' if len(voters) != 1 else 'vote'} from "
                f"{humanize_list(voters)}\n"
            )

        for p in pagify(text):
            embed = discord.Embed(
                title=obj_poll.question,
                description=p,
                color=ctx.author.color,
            )
            await ctx.send(embed=embed)

    @commands.guild_only()  # type:ignore
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command(aliases=["endp"])
    async def endpoll(self, ctx: commands.Context, message_id: int):
        """
        End a currently running poll

        **Arguments**
        - `message_id`: (integer) The ID of the poll message
        """
        for poll in self.polls:
            if poll.message_id == message_id:
                obj_poll = poll
                break
        else:
            return await ctx.send("Could not find poll associated with this message!")

        async with ctx.typing():
            obj_poll.view.stop()
            await obj_poll.finish()
            self.polls.remove(obj_poll)
            await ctx.tick()

    @commands.guild_only()  # type:ignore
    @commands.bot_has_permissions(embed_links=True)
    @commands.mod_or_permissions(manage_messages=True)
    @commands.command()
    async def listpolls(self, ctx: commands.Context):
        """List all currently running polls"""
        if not self.polls:
            return await ctx.send("There are no polls currently running!")

        text = ""
        for poll in self.polls:
            text += (
                f"**{poll.question}**\nMessage ID `{poll.message_id}`\n"
                f"https://discord.com/channels/{poll.guild_id}/{poll.channel_id}/{poll.message_id}"
                "\n\n"
            )

        for p in pagify(text):
            embed = discord.Embed(
                title="Current Polls",
                description=p,
                color=ctx.author.color,
            )
            await ctx.send(embed=embed)

    async def buttonpoll_loop(self):
        """Background loop for checking for finished polls."""
        await self.bot.wait_until_red_ready()
        while True:
            try:
                log.verbose("ButtonPoll loop starting.")
                self.loop_meta.iter_start()
                await self.check_for_finished_polls()
                self.loop_meta.iter_finish()
                log.verbose("ButtonPoll loop finished.")
            except Exception as e:
                log.exception(
                    "Something went wrong with the ButtonPoll loop. Please report this to Vexed.",
                    exc_info=e,
                )
                self.loop_meta.iter_error(e)

            await self.loop_meta.sleep_until_next()

    async def check_for_finished_polls(self):
        polls = self.polls.copy()
        for poll in polls:
            if poll.poll_finish < datetime.datetime.now(datetime.timezone.utc):
                log.info(f"Poll {poll.unique_poll_id} has finished.")
                await poll.finish()
                poll.view.stop()
                self.polls.remove(poll)
