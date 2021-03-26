# ======== PLEASE READ ======================================================
# Status is currently a bit of a mess. For this reason, I'll be undertaking a
# rewrite in the near future: https://github.com/Vexed01/Vex-Cogs/issues/13
#
# For this reason, unless it's minor, PLEASE DO NOT OPEN A PR.
# ===========================================================================


import datetime
from typing import Dict, List, Union

from discord import Embed
from redbot.core.utils import deduplicate_iterables

from .consts import FEED_URLS


class UpdateField:
    """An object representing an update in a FeedDict"""

    def __init__(self, name: str, value: str, time: Union[datetime.datetime, None], group_id: str = None):
        self.name = name
        self.value = value
        self.time = time
        self.group_id = group_id or name

    def __repr__(self):
        return f"UpdateField({self.name}, {self.value}, {self.time}, {self.group_id})"


class FeedDict:
    """An object representing a fully parsed service status."""

    def __init__(
        self,
        fields: List[UpdateField] = None,
        time: datetime.datetime = Embed.Empty,
        title: str = None,
        link: str = None,
        actual_time: datetime.datetime = Embed.Empty,
        description: Union[str, None] = None,
    ):
        self.fields = fields
        self.time = time
        self.title = title
        self.link = link
        self.actual_time = actual_time
        self.description = description

    def __repr__(self):
        return (
            f"FeedDict({self.fields}, {self.time}, {self.title}, {self.link}, {self.actual_time}, {self.description})"
        )

    def to_dict(self):
        """Get a dict of the data held in the object."""
        fields = [{"name": field.name, "value": field.value, "group_id": field.group_id} for field in self.fields]
        return {
            "fields": fields,
            "time": self.time,
            "title": self.title,
            "link": self.link,
            "actual_time": self.actual_time,
            "description": self.description,
        }

    def from_dict(self, dict: dict):
        """Returns a new object from a dict."""
        fields = [
            UpdateField(
                name=field.get("name"),
                value=field.get("value"),
                time=field.get("time", Embed.Empty),
                group_id=field.get("group_id"),
            )
            for field in dict.get("fields")
        ]

        return FeedDict(
            fields=fields,
            time=dict.get("time", Embed.Empty),
            title=dict.get("title"),
            link=dict.get("link"),
            actual_time=dict.get("actual_time", Embed.Empty),
            description=dict.get("description"),
        )

    def get_group_ids(self):
        """Get the group IDs for this feed, in order."""
        return deduplicate_iterables([field.group_id for field in self.fields])


class SendCache:
    """Holds the send cache."""

    def __init__(self, embed_all: Embed, embed_latest: Embed, plain_all: str, plain_latest: str):
        self.embed_latest = embed_latest
        self.embed_all = embed_all
        self.plain_all = plain_all
        self.plain_latest = plain_latest

    def __repr__(self):
        return f"SendCache({self.embed_latest}, {self.embed_all}, {self.plain_all}, {self.plain_latest})"

    def empty():
        pass


class UsedFeeds:
    """Hold counts of feeds that are used."""

    def __init__(self, all_channels: Dict[str, Dict[str, dict]]):
        used_feeds = dict.fromkeys(FEED_URLS.keys(), 0)

        for _, data in all_channels.items():
            for feed in data.get("feeds").keys():
                used_feeds[feed] = used_feeds.get(feed, 0) + 1

        self.__data = used_feeds

    def __repr__(self):
        data = " ".join(f"{i[0]}={i[1]}" for i in self.__data.items())
        return f"<{data}>"

    def add_feed(self, feedname: str):
        self.__data[feedname] = self.__data.get(feedname, 0) + 1

    def remove_feed(self, feedname: str):
        self.__data[feedname] = self.__data.get(feedname, 1) - 1

    def get_list(self) -> List[str]:
        return [k for k, v in self.__data.items() if v]


class ServiceRestrictionsCache:
    """Holds channel restrictions (for members) for when automatic updates are configured."""

    def __init__(self, all_guilds: Dict[int, Dict[str, list]]):
        __data = {}

        for g_id, data in all_guilds.items():
            __data[g_id] = data["service_restrictions"]

        self.__data = __data

    def add_restriction(self, guild_id: int, service: str, channel_id: int):
        """Add a channel to the restriction cache."""
        try:
            self.__data[guild_id]
        except KeyError:
            self.__data[guild_id] = dict.fromkeys(FEED_URLS.keys(), [])
        self.__data[guild_id][service].append(channel_id)

    def remove_restriction(self, guild_id: int, service: str, channel_id: int):
        """Remove a channel from the restriction cache."""
        try:
            self.__data[guild_id][service].remove(channel_id)
        except ValueError:
            pass

    def get_guild(self, guild_id: int, service: str = None):
        """Get the channels for a service in guild."""
        if service:
            return self.__data.get(guild_id, {}).get(service, [])
        else:
            return self.__data.get(guild_id, {})
