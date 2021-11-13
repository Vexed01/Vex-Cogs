import datetime
import logging
from typing import List, Optional

import discord
from discord.channel import TextChannel
from discord.message import Message
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.commands.converter import parse_timedelta
from redbot.core.utils.predicates import MessagePredicate

from buttonpoll.poll import Poll, PollOption
from buttonpoll.pollview import PollView

from .vexutils import format_help, format_info
from .vexutils.button_pred import wait_for_yes_no
from .vexutils.chat import datetime_to_timestamp
from .vexutils.loop import VexLoop

log = logging.getLogger("red.vex.buttonpoll")


class ButtonPoll(commands.Cog):
    """
    Create polls with buttons, and get a pie chart afterwards!
    """

    __author__ = "Vexed#3211"
    __version__ = "1.0.0"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_guild(
            poll_settings={},
            poll_user_choices={},
        )

        self.loop = bot.loop.create_task(self.buttonpoll_loop())
        self.loop_meta = VexLoop("ButtonPoll", 60.0)

        self.views: List[PollView] = []

        bot.add_dev_env_value("bpoll", lambda _: self)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    def cog_unload(self) -> None:
        self.loop.cancel()
        self.bot.remove_dev_env_value("bpoll")

        # if the cog will be reloaded, best to clean up views as they are re-initialised on load
        for view in self.views:
            view.stop()

    @commands.command(hidden=True)
    async def cmdloginfo(self, ctx: commands.Context):
        main = await format_info(ctx, self.qualified_name, self.__version__)
        return await ctx.send(main)

    async def async_init(self) -> None:
        # re-initialise views
        all_polls = await self.config.all_guilds()
        for guild_polls in all_polls.values():
            for poll in guild_polls["poll_settings"].values():
                obj_poll = Poll.from_dict(poll, self)
                view = PollView(self.config, obj_poll)
                self.views.append(view)
                self.bot.add_view(view, message_id=obj_poll.message_id)
                log.debug(f"Re-initialised view for poll {obj_poll.unique_poll_id}")

    @commands.command(name="buttonpoll", aliases=["bpoll"])
    async def buttonpoll(self, ctx: commands.Context, channel: Optional[TextChannel] = None):
        channel = channel or ctx.channel  # type:ignore
        unique_poll_id = (  # last 8 didgits of msg ID and first 50 of sanitised question
            str(ctx.message.id)[8:]
            + "_"
            + "".join(c for c in ctx.message.content if c.isalnum())[:50]
        )

        # TODO: catch timeouterror

        # TODO: let user choose colour of buttons

        # TITLE
        await ctx.send(
            f"I'll be creating a poll in {channel.mention}.\n"
            "What do you want the question to be? Keep it short, if you want to add more detail "
            "you can later on. 1 minute timeout, say `cancel` to cancel."
        )
        t_msg: Message = await self.bot.wait_for(
            "message", check=MessagePredicate.same_context(ctx), timeout=60
        )
        if t_msg.content.lower() == "cancel":
            return await ctx.send("Cancelled.")
        question = t_msg.content

        # DESCRIPTION
        await ctx.send(
            "Great! If you want an extended description, enter it now or say `skip` if you don't. "
            "5 minute timeout."
        )
        d_msg: Message = await self.bot.wait_for(
            "message", check=MessagePredicate.same_context(ctx), timeout=300
        )
        if d_msg.content.lower() == "skip":
            await ctx.send("Okay, they'll be no description.")
            description = None
        elif d_msg.content.lower() == "cancel":
            return await ctx.send("Cancelled.")
        else:
            description = d_msg.content

        # OPTIONS
        await ctx.send(
            "What do you want the options to be? Enter up to five, seperated by a new line "
            "(on desktop do Shift+Enter). 5 minute timeout, say just `cancel` to cancel."
        )
        o_msg: Message = await self.bot.wait_for(
            "message", check=MessagePredicate.same_context(ctx), timeout=300
        )
        if o_msg.content.lower() == "cancel":
            return await ctx.send("Cancelled.")
        str_options = o_msg.content.split("\n")
        if len(str_options) > 5:
            return await ctx.send("Too many options, max is 5.")
        elif len(str_options) < 2:
            return await ctx.send("You need at least two options.")

        options: List[PollOption] = []
        for str_option in str_options:
            option = PollOption(str_option, discord.ButtonStyle.primary)
            options.append(option)

        # TIME
        await ctx.send(
            "How long do you want the poll to be? Valid units are `seconds`, `minutes`, `hours`, "
            "`days` and `weeks`.\nExamples: `1 week` or `1 day 12 hours`"
        )
        ti_msg: Message = await self.bot.wait_for(
            "message", check=MessagePredicate.same_context(ctx), timeout=60
        )
        try:
            duration = parse_timedelta(ti_msg.content)
        except Exception:
            return await ctx.send("Invalid time format. Cancelled.")
        if duration is None:
            return await ctx.send("Invalid time format. Cancelled.")
        poll_finish = datetime.datetime.now(datetime.timezone.utc) + duration

        # YES/NO QS
        change_vote = await wait_for_yes_no(
            ctx,
            content="Almost there! Just a few yes/no questions left.\nDo you want to allow people "
            "to change their vote while the poll is live?",
            timeout=60,
        )
        view_while_live = await wait_for_yes_no(
            ctx,
            content="Do you want to allow people to view the results while the poll is live? If "
            "you say yes, only people who've voted will be able to see.",
            timeout=60,
        )
        send_msg_when_over = await wait_for_yes_no(
            ctx,
            content="Do you want to send a message when the poll is over, or just edit the old "
            "one?",
            timeout=60,
        )

        await ctx.send("All done!")

        poll = Poll(
            unique_poll_id=unique_poll_id,
            guild_id=ctx.guild.id,  # type:ignore
            channel_id=ctx.channel.id,
            question=question,
            description=description,
            options=options,
            allow_vote_change=change_vote,
            view_while_live=view_while_live,
            send_msg_when_over=send_msg_when_over,
            poll_finish=poll_finish,
            cog=self,
        )
        view = PollView(self.config, poll)

        m = await ctx.send(
            f"{poll.question}\n\nPoll ends at {datetime_to_timestamp(poll.poll_finish)}, "
            f"{datetime_to_timestamp(poll.poll_finish, 'R')}",
            view=view,
        )
        poll.set_msg_id(m.id)
        async with self.config.guild(ctx.guild).poll_settings() as poll_settings:
            poll_settings[poll.unique_poll_id] = poll.to_dict()
        self.views.append(view)

    async def buttonpoll_loop(self):
        """Background loop for checking for finished polls."""
        await self.bot.wait_until_red_ready()
        while True:
            try:
                log.debug("ButtonPoll loop starting.")
                self.loop_meta.iter_start()
                await self.check_for_finished_polls()
                self.loop_meta.iter_finish()
                log.debug("ButtonPoll loop finished.")
            except Exception as e:
                log.error(
                    "Something went wrong with the ButtonPoll loop. Please report this to Vexed.",
                    exc_info=e,
                )
                self.loop_meta.iter_error(e)
            finally:
                await self.loop_meta.sleep_until_next()

    # code a loop that checks for polls that have finished, and then runs self.finish_poll
    async def check_for_finished_polls(self):
        all_polls = await self.config.all_guilds()
        for guild_polls in all_polls.values():
            for poll in guild_polls["poll_settings"].values():
                if poll["poll_finish"] < datetime.datetime.now(datetime.timezone.utc).timestamp():
                    obj_poll = Poll.from_dict(poll, self)
                    log.info(f"Poll {obj_poll.unique_poll_id} has finished.")
                    await obj_poll.finish()
