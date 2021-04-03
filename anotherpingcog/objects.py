from typing import Dict, Union

from discord import Emoji
from redbot.core.bot import Red

DEFAULTS = {
    "red": {"emoji": "\N{LARGE RED CIRCLE}", "colour": 14495300},
    "orange": {"emoji": "\N{LARGE ORANGE CIRCLE}", "colour": 16027660},
    "green": {"emoji": "\N{LARGE GREEN CIRCLE}", "colour": 7909721},
}


class Settings:
    def __init__(self, emoji: Union[Emoji, str, int], colour: int):
        self.emoji = emoji
        self.colour = colour

    def __repr__(self):
        return f"Cache({self.emoji}, {self.colour})"


class Cache:
    def __init__(self, settings: Dict[str, Dict[str, Union[str, int]]], embed: bool, bot: Red):
        """Initialize with the dict from config."""
        self.force_embed = embed
        self.__data = settings
        self.__bot = bot

    def __repr__(self):
        return f"Cache({self.__data}, {self.force_embed}, bot)"

    def __set_settings(self, colour_name: str, settings: Settings):
        self.__data[colour_name]["emoji"] = settings.emoji or DEFAULTS[colour_name]["emoji"]
        self.__data[colour_name]["colour"] = settings.colour or DEFAULTS[colour_name]["colour"]

    def __get_settings(self, colour_name: str):
        emoji_id = self.__data[colour_name].get("emoji")
        if emoji_id is None:
            emoji = DEFAULTS[colour_name]["emoji"]
        else:
            emoji = self.__bot.get_emoji(emoji_id) or DEFAULTS[colour_name]["emoji"]

        colour = self.__data[colour_name].get("colour") or DEFAULTS[colour_name]["colour"]

        return Settings(emoji, colour)

    # TODO: use __setter__ and __getter__

    @property
    def red(self):
        return self.__get_settings("red")

    @red.setter
    def red(self, value: Settings):
        self.__set_settings("red", value)

    @property
    def orange(self):
        return self.__get_settings("orange")

    @orange.setter
    def orange(self, value: Settings):
        self.__set_settings("orange", value)

    @property
    def green(self):
        return self.__get_settings("green")

    @green.setter
    def green(self, value: Settings):
        return self.__set_settings("green", value)
