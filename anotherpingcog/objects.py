from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, TypedDict

from discord import Emoji
from redbot.core.bot import Red

COLOURS = Literal["red", "orange", "green"]


class ColourName(TypedDict):
    emoji: str | int
    colour: int


class Defaults(TypedDict):
    red: ColourName
    orange: ColourName
    green: ColourName


DEFAULTS = Defaults(
    red=ColourName(emoji="\N{LARGE RED CIRCLE}", colour=14495300),
    orange=ColourName(emoji="\N{LARGE ORANGE CIRCLE}", colour=16027660),
    green=ColourName(emoji="\N{LARGE GREEN CIRCLE}", colour=7909721),
)


@dataclass
class Settings:
    emoji: int | None
    colour: int | None


@dataclass
class FullSettings:
    emoji: str | Emoji
    colour: int

    def __repr__(self) -> str:
        emoji = f'"{self.emoji}"' if isinstance(self.emoji, str) else self.emoji
        return f"FullSettings({emoji}, {self.colour})"


class Cache:
    def __init__(self, settings: Defaults, embed: bool, footer: str, bot: Red) -> None:
        """Initialize with the dict from config."""
        self.force_embed = embed
        self.footer = footer
        self.__data = settings
        self.__bot = bot

    def __repr__(self) -> str:
        return f"Cache({self.__data}, {self.force_embed}, {self.footer}, bot)"

    def set(self, colour_name: COLOURS, settings: Settings) -> None:
        self.__data[colour_name]["emoji"] = settings.emoji or DEFAULTS[colour_name]["emoji"]
        self.__data[colour_name]["colour"] = settings.colour or DEFAULTS[colour_name]["colour"]

    def __get_settings(self, colour_name: COLOURS) -> FullSettings:
        emoji_id = self.__data[colour_name].get("emoji", "")

        if isinstance(emoji_id, int):
            emoji = self.__bot.get_emoji(emoji_id) or DEFAULTS[colour_name]["emoji"]  # type:ignore
        else:
            emoji = DEFAULTS[colour_name]["emoji"]

        colour = self.__data[colour_name]["colour"] or DEFAULTS[colour_name]["colour"]

        return FullSettings(emoji, colour)  # type:ignore
        # its being rly picky for whatever reason........

    @property
    def red(self) -> FullSettings:
        return self.__get_settings("red")

    @property
    def orange(self) -> FullSettings:
        return self.__get_settings("orange")

    @property
    def green(self) -> FullSettings:
        return self.__get_settings("green")
