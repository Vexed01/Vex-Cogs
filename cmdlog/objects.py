from __future__ import annotations

import datetime
from dataclasses import dataclass
from sys import getsizeof
from typing import Literal

import discord

TIME_FORMAT = "%Y-%m-%d %H:%M:%S"


@dataclass()
class BasicDiscordObject:
    id: int
    name: str

    def __sizeof__(self) -> int:
        # using getsizeof includes things like garbage
        return getsizeof(self.id) + getsizeof(self.name)


class Log:
    """Base for logged data"""


class LoggedCommand(Log):
    """Inherits from LogMixin, for a logged command"""

    def __init__(
        self,
        command: str,
        log_content: bool | None,
        content: str,
        user: discord.Member | discord.User,
        msg_id: int,
        channel: discord.abc.MessageableChannel | None = None,
        guild: discord.Guild | None = None,
    ):
        self.command = command
        if log_content:
            self.content = content
        else:
            self.content = None
        self.user = BasicDiscordObject(user.id, user.name)
        self.msg_id = msg_id
        self.channel = (
            BasicDiscordObject(channel.id, channel.name)
            if channel and not isinstance(channel, discord.DMChannel)
            else None
        )
        self.guild = BasicDiscordObject(guild.id, guild.name) if guild else None

        self.time = datetime.datetime.now().strftime(TIME_FORMAT)

    def __str__(self) -> str:  # this is what is logged locally
        com = self.content or self.command
        if not self.guild or not self.channel:
            return f"Text command '{com}' ran by {self.user.id} ({self.user.name}) in our DMs."

        return (
            f"Text command [{com}] ran by {self.user.id} [{self.user.name}] "
            f"with message ID {self.msg_id} "
            f"in channel {self.channel.id} [{self.channel.name}] "
            f"in guild {self.guild.id} [{self.guild.name}]"
        )

    def __sizeof__(self) -> int:
        # using getsizeof here will include other stuff eg garbage
        size = 0

        size += getsizeof(self.command)
        size += getsizeof(self.content)
        size += getsizeof(self.user)
        size += getsizeof(self.msg_id)
        size += getsizeof(self.channel)
        size += getsizeof(self.guild)
        size += getsizeof(self.time)

        return size


class LoggedComError(Log):
    def __init__(
        self,
        command: str,
        log_content: bool | None,
        content: str,
        user: discord.Member | discord.User,
        msg_id: int,
        channel: discord.abc.MessageableChannel | None = None,
        guild: discord.Guild | None = None,
        error_info: str = "an unknown",
    ):
        self.command = command
        if log_content:
            self.content = content
        else:
            self.content = None
        self.user = BasicDiscordObject(user.id, user.name)
        self.msg_id = msg_id
        self.error_info = error_info
        self.channel = (
            BasicDiscordObject(channel.id, channel.name)
            if channel and not isinstance(channel, discord.DMChannel)
            else None
        )
        self.guild = BasicDiscordObject(guild.id, guild.name) if guild else None

        self.time = datetime.datetime.now().strftime(TIME_FORMAT)

    def __str__(self) -> str:  # this is what is logged locally
        com = self.content or self.command
        if not self.guild or not self.channel:
            return (
                f"Text command '{com}' failed due to {self.error_info} by user {self.user.id} "
                f"({self.user.name}) in our DMs."
            )

        return (
            f"Text command [{com}] failed due to {self.error_info} by user {self.user.id} "
            f"[{self.user.name}] with message ID {self.msg_id} "
            f"in channel {self.channel.id} [{self.channel.name}] "
            f"in guild {self.guild.id} [{self.guild.name}]"
        )

    def __sizeof__(self) -> int:
        # using getsizeof here will include other stuff eg garbage
        size = 0

        size += getsizeof(self.command)
        size += getsizeof(self.content)
        size += getsizeof(self.user)
        size += getsizeof(self.msg_id)
        size += getsizeof(self.channel)
        size += getsizeof(self.guild)
        size += getsizeof(self.time)

        return size


class LoggedAppCom(Log):
    """Inherits from LogMixin, for a logged Application Command."""

    target: BasicDiscordObject | discord.PartialMessage | None

    def __init__(
        self,
        author: discord.Member | discord.User,
        com_name: str,
        channel: discord.interactions.InteractionChannel | None,
        guild: discord.Guild | None,
        app_type: Literal[1, 2, 3],
        target: discord.PartialMessage | discord.User | None,
    ):
        self.author = BasicDiscordObject(author.id, str(author))
        self.command = com_name
        self.channel = (
            BasicDiscordObject(channel.id, channel.name)
            if channel and not isinstance(channel, discord.DMChannel)
            else None
        )
        self.guild = BasicDiscordObject(guild.id, guild.name) if guild else None
        self.app_type = app_type

        if isinstance(target, discord.User):
            self.target = BasicDiscordObject(target.id, target.name)
        else:
            target = target

        self.time = datetime.datetime.now().strftime(TIME_FORMAT)

    def __str__(self) -> str:  # this is what's logged locally
        if self.app_type == 1:  # slash com
            if not self.guild or not self.channel:
                return (
                    f"Slash command [{self.command}] ran by {self.author.id} [{str(self.author)}]"
                    " in our DMs."
                )
            return (
                f"Slash command [{self.command}] ran by {self.author.id} [{str(self.author)}] "
                f"in channel {self.channel.id} [{self.channel.name}] "
                f"in guild {self.guild.id} [{self.guild.name}]"
            )

        if self.app_type == 2:  # user command
            if not isinstance(self.target, BasicDiscordObject):
                return (
                    "User not in cache so I cannot show the target of this application user"
                    " command."
                )
            if not self.guild or not self.channel:
                return (
                    f"User command [{self.command}] ran by {self.author.id} [{str(self.author)}] "
                    f"targeting user {self.target.name} [{self.target.id}]"
                    "in our DMs."
                )

            return (
                f"User command [{self.command}] ran by {self.author.id} [{str(self.author)}] "
                f"targeting user {self.target.name} [{self.target.id}]"
                f"in channel {self.channel.id} [{self.channel.name}] "
                f"in guild {self.guild.id} [{self.guild.name}]"
            )

        if self.app_type == 3:  # message command
            if not isinstance(self.target, discord.PartialMessage):  # this should never happen
                return "Something really bad went wrong so I can't show this."
            if not self.guild or not self.channel:
                return (
                    f"Message command [{self.command}] ran by"
                    f" {self.author.id} [{str(self.author)}] targeting message {self.target.id}in"
                    " our DMs."
                )

            return (
                f"Message command [{self.command}] ran by {self.author.id} [{str(self.author)}] "
                f"targeting message {self.target.id}"
                f"in channel {self.channel.id} [{self.channel.name}] "
                f"in guild {self.guild.id} [{self.guild.name}]"
            )

        return ""

    def __sizeof__(self) -> int:
        # using getsizeof here will include other stuff eg garbage
        size = 0

        size += getsizeof(self.command)
        size += getsizeof(self.author)
        size += getsizeof(self.app_type)
        size += getsizeof(self.channel)
        size += getsizeof(self.guild)
        size += getsizeof(self.time)
        size += getsizeof(self.target)

        return size
