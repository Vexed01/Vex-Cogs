# Yes, it's simpler to use a dict for these, but I've used this as an
# opportunity to learn about making and working with objects. Objects are fun!

import datetime
from typing import Dict, List

from discord import Embed

from .consts import FEED_URLS


class UpdateField(object):
    """An object representing an update in a FeedDict"""

    def __init__(self, name: str, value: str):
        self.name = name
        self.value = value


class FeedDict(object):
    """An object representing a fully parsed service status."""

    def __init__(self, fields: List[UpdateField], time: datetime.datetime, title: str, link: str):
        self.fields = fields
        self.time = time
        self.title = title
        self.link = link

    def to_dict(self):
        """Get a dict of the data held in the object."""
        fields = []
        for field in self.fields:
            fields.append({"name": field.name, "value": field.value})

        return {
            "fields": fields,
            "time": self.time,
            "title": self.title,
            "link": self.link,
        }

    def from_dict(self, dict: dict):
        """Returns a new object from a dict."""
        fields = []
        for field in dict.get("fields"):
            fields.append(UpdateField(name=field.get("name"), value=field.get("value")))

        return FeedDict(
            fields=fields,
            time=dict.get("time"),
            title=dict.get("title"),
            link=dict.get("link"),
        )


class SendCache(object):
    """Holds the send cache."""

    def __init__(self, embed_all: Embed, embed_latest: Embed, plain_all: str, plain_latest: str):
        self.embed_latest = embed_latest
        self.embed_all = embed_all
        self.plain_all = plain_all
        self.plain_latest = plain_latest

    def empty():
        """Get an empty SendCache object."""


class UsedFeeds(object):
    """Hold counts of feeds that are used."""

    def __init__(self, all_channels: Dict[str, Dict[str, dict]]):
        used_feeds = dict.fromkeys(FEED_URLS.keys(), 0)

        for id, data in all_channels.items():
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
