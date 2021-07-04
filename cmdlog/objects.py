import datetime
from dataclasses import dataclass
from sys import getsizeof
from typing import Optional

from discord.channel import DMChannel
from discord.message import Message
from redbot.core import commands

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass
class IDFKWhatToNameThis:
    id: int
    name: str

    def __sizeof__(self) -> int:
        # using getsizeof includes things like garbage
        return getsizeof(self.id) + getsizeof(self.name)


class LogMixin:
    """Base for logged data"""

    def __init__(self, ctx: commands.Context, log_content: Optional[bool]):
        self.command = ctx.command.qualified_name
        self.user = IDFKWhatToNameThis(
            id=ctx.author.id, name=f"{ctx.author.name}#{ctx.author.discriminator}"
        )
        self.msg_id = ctx.message.id
        self.channel: Optional[IDFKWhatToNameThis] = None
        self.guild: Optional[IDFKWhatToNameThis] = None
        if ctx.guild:
            assert not isinstance(ctx.channel, DMChannel)
            self.channel = IDFKWhatToNameThis(id=ctx.channel.id, name=f"#{ctx.channel.name}")
            self.guild = IDFKWhatToNameThis(id=ctx.guild.id, name=ctx.guild.name)
        self.content: Optional[str] = None
        if log_content and ctx.message is not None:
            assert isinstance(ctx.message, Message)
            self.content = ctx.message.content

        self.time = datetime.datetime.now().strftime(TIME_FORMAT)

    def __str__(self) -> str:
        raise NotImplementedError()

    def __sizeof__(self) -> int:
        # using getsizeof here will include other stuff eg garbage
        size = 0

        size += getsizeof(self.command)
        size += getsizeof(self.user)
        size += getsizeof(self.msg_id)
        size += getsizeof(self.channel)
        size += getsizeof(self.guild)
        size += getsizeof(self.time)

        return size


class LoggedCommand(LogMixin):
    """Inherits from LogMixin, for a logged command"""

    def __str__(self) -> str:
        com = self.content or self.command
        if not self.guild or not self.channel:
            return f"'{com}' ran by {self.user.id} ({self.user.name}) in our DMs."

        return (
            f"'{com}' ran by {self.user.id} ({self.user.name}) "
            f"with message ID {self.msg_id} "
            f"in channel {self.channel.id} ({self.channel.name}) "
            f"in guild {self.guild.id} ({self.guild.name})"
        )


class LoggedCheckFailure(LogMixin):
    """Inherits from LogMixin, for a logged check failure"""

    def __str__(self) -> str:
        com = self.content or self.command
        if not self.guild or not self.channel:
            return f"'{com}' ran by {self.user.id} ({self.user.name}) in our DMs."

        return (
            f"'{com}' raised a check failure by {self.user.id} ({self.user.name}) "
            f"with message ID {self.msg_id} "
            f"in channel {self.channel.id} ({self.channel.name}) "
            f"in guild {self.guild.id} ({self.guild.name})"
        )
