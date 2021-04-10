import datetime
import re
from typing import List, Optional

import pytz
from dateutil.parser import parse as parse_time
from redbot.core.utils.chat_formatting import humanize_list, pagify

from status.objects.incidentdata import IncidentData, UpdateField


def _handle_long_fields(
    old_fields: List[UpdateField],
) -> List[UpdateField]:  # using updatefield because idk really
    """Split long fields (over 1024 chars) into multiple, retaining order."""
    new_fields = []
    for field in old_fields:
        field.value = re.sub(
            r"(\n\n\n)(\n)*", "\n\n", field.value
        )  # excessive new lines (looking at you cloudflare)
        if len(field.value) <= 1024:
            new_fields.append(field)
        else:
            paged = list(pagify(field.value, page_length=1024))
            new_fields.append(UpdateField(field.name, paged[0], field.update_id))
            for page in paged[1:]:
                new_fields.append(
                    UpdateField("Above continued (hit field limits)", page, field.update_id)
                )

    return new_fields


def _process(incident: dict, type: str) -> IncidentData:
    fields = []
    for update in incident["incident_updates"]:
        # this is exactly how they are displayed on the website
        friendly_time = (
            parse_time(update["created_at"]).astimezone(pytz.utc).strftime("%b %d, %H:%M %Z")
        )

        fields.append(
            UpdateField(
                name="{} - {}".format(
                    update["status"].replace("_", " ").capitalize(), friendly_time
                ),
                value=update["body"],
                update_id=update["id"],
            )
        )

    actual_update_time = parse_time(incident["incident_updates"][0]["created_at"])

    # statuspage why do you give everything in the wrong order...
    fields.reverse()
    fields = _handle_long_fields(fields)

    affected_components = humanize_list([c["name"] for c in incident["components"]]) or "_Unknown_"

    desc = f"Impact: **{incident['impact'].capitalize()}**\nAffects: {affected_components}"

    if type == "scheduled":
        start = (
            parse_time(incident["scheduled_for"]).astimezone(pytz.utc).strftime("%b %d, %H:%M %Z")
        )
        end = (
            parse_time(incident["scheduled_until"])
            .astimezone(pytz.utc)
            .strftime("%b %d, %H:%M %Z")
        )

        desc += f"\nScheduled for: **{start}** to **{end}**"

        scheduled_for: Optional[datetime.datetime] = parse_time(incident["scheduled_for"])
    else:
        scheduled_for = None

    return IncidentData(
        fields=fields,
        time=parse_time(incident["updated_at"]),  # when statuspage claims it was updated
        title=incident["name"],
        link=incident["shortlink"],  # for whatever reason a long link isn't available
        actual_time=actual_update_time,  # when the last update was actually posted
        description=desc,
        incident_id=incident["id"],
        scheduled_for=scheduled_for,
    )


def process_incidents(json_resp: dict) -> List[IncidentData]:
    return [_process(j_data, "incidents") for j_data in json_resp.get("incidents", [])]


def process_scheduled(json_resp: dict) -> List[IncidentData]:
    return [
        _process(j_data, "scheduled") for j_data in json_resp.get("scheduled_maintenances", [])
    ]
