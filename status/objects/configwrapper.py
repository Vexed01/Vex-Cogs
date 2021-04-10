import datetime
from typing import Any, Dict, List, Optional, Tuple, TypedDict, Union

from discord import Embed
from redbot.core import Config

from status.objects.caches import LastChecked
from status.objects.incidentdata import IncidentData, Update, UpdateField


class _ConfDict(TypedDict):
    fields: List[UpdateField]
    time: datetime.datetime


class ConfigWrapper:
    """A wrapper which does a few things."""

    def __init__(self, config: Config, last_checked: LastChecked):
        self.config = config
        self.last_checked = last_checked

    async def get_latest(
        self, service: str
    ) -> Union[
        Tuple[IncidentData, Dict[str, Union[str, float]]], Tuple[None, None]
    ]:  # ... this is long
        incident: Optional[dict] = (await self.config.feed_store()).get(service)
        if not incident:
            return None, None
        extra_info = {"checked": self.last_checked.get_time(service)}

        deserialised: Dict[str, Union[List[UpdateField], str, datetime.datetime]] = {"fields": []}
        if incident["time"]:
            deserialised["time"] = datetime.datetime.fromtimestamp(incident["time"])
        if incident["actual_time"]:
            deserialised["actual_time"] = datetime.datetime.fromtimestamp(incident["actual_time"])
        if incident.get("scheduled_for"):
            deserialised["scheduled_for"] = datetime.datetime.fromtimestamp(
                incident["scheduled_for"]
            )

        for field in incident["fields"]:
            deserialised["fields"].append(
                UpdateField(field["name"], field["value"], field["update_id"])
            )

        incidentdata = IncidentData(
            fields=deserialised["fields"],
            time=deserialised["time"],
            title=incident["title"],
            link=incident["link"],
            actual_time=deserialised["actual_time"],
            description=deserialised.get("description"),
            scheduled_for=deserialised["scheduled_for"],
        )

        return incidentdata, extra_info

    async def update_incidents(self, service: str, incidentdata: IncidentData) -> None:
        feeddict = incidentdata.to_dict()
        if isinstance(feeddict["time"], datetime.datetime):
            feeddict["time"] = feeddict["time"].timestamp()
        else:
            feeddict["time"] = ""
        if isinstance(feeddict["actual_time"], datetime.datetime):
            feeddict["actual_time"] = feeddict["actual_time"].timestamp()
        else:
            feeddict["actual_time"] = ""
        if isinstance(feeddict["scheduled_for"], datetime.datetime):
            feeddict["scheduled_for"] = feeddict["scheduled_for"].timestamp()
        else:
            feeddict["scheduled_for"] = ""

        await self.config.feed_store.set_raw(service, value=feeddict)  # type:ignore
        self.last_checked.update_time(service)

    async def get_channels(self, service: str) -> Dict[str, dict]:
        """Get the channels for a feed. The list is channel IDs from config, they may be
        invalid."""
        feeds = await self.config.all_channels()
        return {
            name: data["feeds"][service]
            for name, data in feeds.items()
            if service in data["feeds"].keys()
        }

    async def update_edit_id(self, c_id: int, service: str, incident_id: str, msg_id: int) -> None:
        async with self.config.channel_from_id(c_id).feeds() as feeds:
            if feeds[service].get("edit_id") is None:
                feeds[service]["edit_id"] = {incident_id: msg_id}
            else:
                feeds[service]["edit_id"][incident_id] = msg_id
