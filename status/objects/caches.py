from collections import defaultdict, deque
from time import time
from typing import Deque, Dict, List, Literal, Union

from status.core import FEEDS, SERVICE_LITERAL


class UsedFeeds:
    """Counts for used feeds, for the update loop."""

    def __init__(self, all_channels: Dict[str, Dict[str, Dict[SERVICE_LITERAL, dict]]]):
        used_feeds = dict.fromkeys(FEEDS.keys(), 0)

        for _, data in all_channels.items():
            for feed in data.get("feeds", {}).keys():
                used_feeds[feed] = used_feeds.get(feed, 0) + 1

        self.__data = used_feeds

    def __repr__(self):
        data = " ".join(f"{i[0]}={i[1]}" for i in self.__data.items())
        return f"<{data}>"

    def add_feed(self, feedname: SERVICE_LITERAL) -> None:
        self.__data[feedname] = self.__data.get(feedname, 0) + 1

    def remove_feed(self, feedname: SERVICE_LITERAL) -> None:
        self.__data[feedname] = self.__data.get(feedname, 1) - 1

    def get_list(self) -> list:
        return [k for k, v in self.__data.items() if v]


class ServiceRestrictionsCache:
    """Holds channel restrictions (for members) for when automatic updates are configured."""

    def __init__(self, all_guilds: Dict[int, Dict[str, list]]):
        __data: dict = {}

        for g_id, data in all_guilds.items():
            __data[g_id] = data["service_restrictions"]

        self.__data = __data

    def add_restriction(self, guild_id: int, service: str, channel_id: int) -> None:
        """Add a channel to the restriction cache."""
        try:
            self.__data[guild_id]
        except KeyError:
            self.__data[guild_id] = dict.fromkeys(FEEDS.keys(), [])
        self.__data[guild_id][service].append(channel_id)

    def remove_restriction(self, guild_id: int, service: str, channel_id: int) -> None:
        """Remove a channel from the restriction cache."""
        try:
            self.__data[guild_id][service].remove(channel_id)
        except ValueError:
            pass

    def get_guild(self, guild_id: int, service: str = None) -> Union[dict, list]:
        """Get the channels, optionally for a specific service, in a guild."""
        if service:
            return self.__data.get(guild_id, {}).get(service, [])
        else:
            return self.__data.get(guild_id, {})


class LastChecked:
    """Store when incidents were last checked."""

    def __init__(self) -> None:
        self.last_checked: Dict[str, float] = {}

    def __repr__(self):
        m = "<"
        for service in FEEDS.keys():
            m += f"{service}={getattr(self, service, 0.0)} "
        m = m.rstrip()
        return m + ">"

    def get_time(self, service: str) -> float:
        return self.last_checked.get(service, 0.0)

    def update_time(self, service: str) -> None:
        self.last_checked[service] = time()


class ServiceCooldown:
    def __init__(self) -> None:
        self.__data: Dict[int, Dict[str, Deque[float]]] = defaultdict(dict)

    def __repr__(self):
        return str(self.__data)

    # so, the data for each service is like this: [float, float]
    # pos 0 is the latest invoke
    # pos 1 is the second most recent
    # all others aren't stored because they dont matter
    #
    # so if pos 1 was within the last 120 seconds there have been 2 valid invocations
    # which means there needs to be a cooldown
    #
    # otherwise, basically pos 0 moves to pos 1 with append_left
    # and pos 0 becomes the current time

    def handle(self, user_id: int, service: str) -> Union[float, Literal[False]]:
        cooldown_data = self.__data.get(user_id, {}).get(service, deque([0.0, 0.0], maxlen=2))
        time_since = abs(time() - cooldown_data[1])  # their second to last invoke
        if time_since < 120:  # their second to last invoke was within last 2 mins
            return 120 - time_since

        cooldown_data.appendleft(time())

        self.__data[user_id][service] = cooldown_data

        return False

    def get_from_id(self, user_id: int) -> dict:
        return self.__data.get(user_id, {})
