from __future__ import annotations

import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, List, Literal, Optional

import discord
from discord.channel import TextChannel
from redbot.core import Config, app_commands, commands
from redbot.core.bot import Red
from redbot.core.commands import parse_timedelta

from .components.setup import SetupYesNoView, StartSetupView
from .poll import Poll, PollOption
from .vexutils import format_help, format_info, get_vex_logger
from .vexutils.loop import VexLoop

log = get_vex_logger(__name__)


class ButtonPoll(commands.Cog):
    """
    Create polls with buttons, and get a pie chart afterwards!
    """

    __author__ = "Vexed#3211"
    __version__ = "1.1.2"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_guild(
            poll_settings={},
            poll_user_choices={},
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
    @commands.command(alias=["poll", "bpoll"])
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

        # these two checks are untested :)
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

        view = StartSetupView(author=ctx.author, channel=channel, cog=self)
        await ctx.send("Click below to start a poll!", view=view)

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

        str_options: set[str | None] = {choice1, choice2, choice3, choice4, choice5}
        str_options.discard(None)
        if len(str_options) < 2:
            await interaction.response.send_message(
                "You must provide at least two unique choices. No duplicates!",
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
