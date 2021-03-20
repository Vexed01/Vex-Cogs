# Yes, it's simpler to use a dict for these, but I've used this as an
# opportunity to learn about making and working with objects. Objects are fun!

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


class FeedDict:
    """An object representing a fully parsed service status."""

    def __init__(
        self,
        fields: List[UpdateField] = None,
        time: datetime.datetime = None,
        title: str = None,
        link: str = None,
        actual_time: datetime.datetime = None,
        description: Union[str, None] = None,
    ):
        self.fields = fields
        self.time = time
        self.title = title
        self.link = link
        self.actual_time = actual_time
        self.description = description

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
                time=field.get("time"),
                group_id=field.get("group_id"),
            )
            for field in dict.get("fields")
        ]

        return FeedDict(
            fields=fields,
            time=dict.get("time"),
            title=dict.get("title"),
            link=dict.get("link"),
            actual_time=dict.get("actual_time"),
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

    def empty():
        pass


class UsedFeeds:
    """Hold counts of feeds that are used."""

    def __init__(self, all_channels: Dict[str, Dict[str, dict]]):
        used_feeds = dict.fromkeys(FEED_URLS.keys(), 0)

        for _, data in all_channels.items():
            feeds = data.get("feeds").keys()
            for feed in feeds:
                used_feeds[feed] = used_feeds.get(feed, 0) + 1

        self.raw = used_feeds

    def add_feed(self, feedname: str):
        self.raw[feedname] = self.raw.get(feedname, 0) + 1

    def remove_feed(self, feedname: str):
        self.raw[feedname] = self.raw.get(feedname, 1) - 1

    def get_list(self) -> List[str]:
        return [k for k, v in self.raw.items() if v]
