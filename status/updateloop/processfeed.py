from __future__ import annotations

import re

from dateutil.parser import parse as parse_time
from markdownify import markdownify
from redbot.core.utils.chat_formatting import humanize_list, pagify

from ..core import TYPES_LITERAL
from ..objects import IncidentData, UpdateField
from ..vexutils.chat import datetime_to_timestamp


def _handle_long_fields(
    old_fields: list[UpdateField],
) -> list[UpdateField]:
    """Split long fields (over 1024 chars) into multiple, retaining order.

    Parameters
    ----------
    old_fields : List[UpdateField]
        List of fields which may exceed per-field embed limits.

    Returns
    -------
    List[UpdateField]
        New list of fields which may be split to not exceed per-field embed limits
    """
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
                new_fields.append(UpdateField("\u200b", page, field.update_id))

    return new_fields


def _handle_html(text: str) -> str:
    """Why tf do you put HTML tags in the API...

    At least I'm being kind and replacing them properly.

    Culprits:
    - Oracle
    - Cloudflare
    - GitHub

    Parameters
    ----------
    text : str
        Text to strip/replace

    Returns
    -------
    str
        Stripped/replaced string
    """
    return markdownify(text)


def _process(incident: dict, type: TYPES_LITERAL) -> IncidentData:
    """Turn a API JSON incident/maintenance into IncidentData

    Parameters
    ----------
    incident : dict
        JSON resp from Status API
    type : TYPES_LITERAL
        Either "incidents" or "scheduled"

    Returns
    -------
    IncidentData
        Standard object for further processing.
    """
    fields = []
    for update in incident["incident_updates"]:
        # this is exactly how they are displayed on the website
        dt = parse_time(update["created_at"])

        fields.append(
            UpdateField(
                name="{} - {}".format(
                    update["status"].replace("_", " ").capitalize(), datetime_to_timestamp(dt)
                ),
                value=_handle_html(update["body"]),
                update_id=update["id"],
            )
        )

    actual_update_time = parse_time(incident["incident_updates"][0]["created_at"])

    # statuspage why do you give everything in the wrong order...
    fields.reverse()
    fields = _handle_long_fields(fields)

    affected_components = (
        humanize_list([c["name"] for c in incident.get("components", [])]) or "_Unknown_"
    )

    desc = f"Impact: **{incident['impact'].capitalize()}**\nAffects: {affected_components}"

    if type == "scheduled":
        start = datetime_to_timestamp(parse_time(incident["scheduled_for"]))
        end = datetime_to_timestamp(parse_time(incident["scheduled_until"]))

        desc += f"\nScheduled for: **{start}** to **{end}**"

        scheduled_for = parse_time(incident["scheduled_for"])
    else:
        scheduled_for = None

    if len(desc) > 4096:
        desc = desc[0:4050] + "\n..."  # v unlikely to happen... so im being lazy

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


def process_json(json_resp: dict, type: TYPES_LITERAL) -> list[IncidentData]:
    """Turn the API into life

    Parameters
    ----------
    json_resp : dict
        Response from Status API

    Returns
    -------
    List[IncidentData]
        List of parsed IncidentData
    """
    if type == "incidents":
        return [_process(j_data, "incidents") for j_data in json_resp.get("incidents", [])]
    elif type == "scheduled":
        return [
            _process(j_data, "scheduled") for j_data in json_resp.get("scheduled_maintenances", [])
        ]
    return []
