from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Dict, List, Optional

import discord
import pandas as pd
import plotly.express as px
from discord.channel import TextChannel
from discord.embeds import EmptyEmbed
from discord.enums import ButtonStyle

from .pollview import PollView

if TYPE_CHECKING:
    from plotly.graph_objs._figure import Figure

    from .buttonopll import ButtonPoll
else:
    from plotly.graph_objs import Figure


log = logging.getLogger("red.vex.buttonpoll.poll")


@dataclass
class PollOption:
    """
    A poll option.
    """

    name: str
    style: ButtonStyle


class Poll:
    """
    A poll object.
    """

    def __init__(
        self,
        unique_poll_id: str,
        guild_id: int,
        channel_id: int,
        question: str,
        description: Optional[str],
        options: List[PollOption],
        allow_vote_change: bool,
        view_while_live: bool,
        send_msg_when_over: bool,
        poll_finish: datetime,
        cog: "ButtonPoll",
        view: "PollView",
        message_id: int = 0,
    ):
        self.unique_poll_id = unique_poll_id
        self.guild_id = guild_id
        self.channel_id = channel_id
        self.message_id = message_id  # will be set later
        self.question = question
        self.description = description
        self.options = options
        self.allow_vote_change = allow_vote_change
        self.view_while_live = view_while_live
        self.send_msg_when_over = send_msg_when_over
        self.poll_finish = poll_finish
        self.view = view

        self.cog = cog

    def __eq__(self, __o: object) -> bool:
        if isinstance(__o, Poll):
            return self.unique_poll_id == __o.unique_poll_id
        return False

    def set_msg_id(self, msg_id: int):
        """Set the message id of the poll, to be used once sent."""
        self.message_id = msg_id

    @classmethod
    def from_dict(cls, data: dict, cog: "ButtonPoll"):
        """
        Create a Poll object from a dict.
        """
        if isinstance(data["poll_finish"], (int, float)):
            finish = datetime.fromtimestamp(data["poll_finish"], tz=timezone.utc)
        else:
            finish = data["poll_finish"]

        cls = cls(
            unique_poll_id=data["unique_poll_id"],
            guild_id=int(data["guild_id"]),
            channel_id=int(data["channel_id"]),
            message_id=int(data["message_id"]),
            question=data["question"],
            description=data["description"],
            options=[PollOption(n, s) for n, s in data["options"].items()],
            allow_vote_change=bool(data["allow_vote_change"]),
            view_while_live=bool(data["view_while_live"]),
            send_msg_when_over=bool(data["send_msg_when_over"]),
            poll_finish=finish,
            cog=cog,
            view=None,  # type:ignore
        )
        cls.view = PollView(cog.config, cls)
        return cls

    def to_dict(self) -> dict:
        data = self
        return {
            "unique_poll_id": data.unique_poll_id,
            "guild_id": str(data.guild_id),
            "channel_id": str(data.channel_id),
            "message_id": str(data.message_id),
            "question": data.question,
            "description": data.description,
            "options": {option.name: option.style.value for option in data.options},
            "allow_vote_change": data.allow_vote_change,
            "view_while_live": data.view_while_live,
            "send_msg_when_over": data.send_msg_when_over,
            "poll_finish": data.poll_finish.timestamp(),
        }

    async def get_results(self) -> Dict[str, int]:
        """Get poll results.

        Returns
        -------
        Dict[str, int]
            A dictionary with the key as the poll label and the value as the number of votes.
        """
        results: Dict[str, int] = {}
        for option in self.options:
            results[option.name] = 0

        all_poll_vote_data = await self.cog.config.guild_from_id(self.guild_id).poll_user_choices()
        raw_vote_data = all_poll_vote_data.get(self.unique_poll_id, {})

        for str_option in raw_vote_data.values():
            results[str_option] += 1

        return results

    async def finish(self):
        """Finish this poll."""
        channel = self.cog.bot.get_channel(self.channel_id)
        if not isinstance(channel, TextChannel):
            log.warning(
                f"Channel {self.channel_id} does not exist. Removing poll {self.unique_poll_id} "
                "without properly finishing it."
            )
            return
        poll_msg = channel.get_partial_message(self.message_id)
        poll_results = await self.get_results()

        embed = discord.Embed(
            colour=await self.cog.bot.get_embed_color(channel),
            title=self.question,
            description=self.description or EmptyEmbed,
        )
        sorted_results = {
            k: v for k, v in sorted(poll_results.items(), key=lambda x: x[1], reverse=True)
        }

        embed.add_field(
            name="Results",
            value="\n".join(f"{k}: {v}" for k, v in sorted_results.items()),
            inline=False,
        )

        try:
            await poll_msg.edit(embed=embed, content="", view=None)
        except discord.NotFound:
            log.warning(
                f"Poll {self.unique_poll_id}'s message was not found in channel {self.channel_id},"
                " so I cannot end it."
            )
            return

        if self.send_msg_when_over:
            embed_2 = discord.Embed(
                title="Poll finished",
                colour=await self.cog.bot.get_embed_color(channel),
                description=f"**{self.question}** has finished!",
            )
            embed_2.add_field(
                name="Results",
                value="\n".join(f"{k}: {v}" for k, v in sorted_results.items()),
                inline=False,
            )
            view = discord.ui.View()
            view.add_item(
                discord.ui.Button(
                    label="Original message", style=ButtonStyle.link, url=poll_msg.jump_url
                )
            )
            plot = await self.plot()
            embed_2.set_image(url="attachment://plot.png")
            await channel.send(embed=embed_2, file=plot, view=view)
            view.stop()

        async with self.cog.config.guild_from_id(self.guild_id).poll_settings() as poll_settings:
            del poll_settings[self.unique_poll_id]
        async with self.cog.config.guild_from_id(
            self.guild_id
        ).poll_user_choices() as poll_user_choices:
            del poll_user_choices[self.unique_poll_id]

    async def plot(self) -> discord.File:
        results = await self.get_results()
        df = pd.DataFrame.from_dict(results, orient="index", columns=["count"])  # type:ignore

        df = df.loc[df["count"] != 0]

        def _plot() -> discord.File:
            """blocking"""
            fig: Figure = px.pie(
                df, template="plotly_dark", values="count", names=df.index, title=self.question
            )
            fig.update_traces(textfont_size=18)

            # set legend font size to 18
            fig.update_layout(
                legend=dict(
                    font=dict(size=18),
                ),
                title=dict(
                    font=dict(size=20),
                ),
            )

            bytes = fig.to_image(format="png", width=800, height=500, scale=1)
            buffer = io.BytesIO(bytes)
            buffer.seek(0)
            file = discord.File(buffer, filename="plot.png")
            buffer.close()
            return file

        return await self.cog.bot.loop.run_in_executor(self.cog.plot_executor, _plot)
