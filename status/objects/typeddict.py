from __future__ import annotations

import datetime
from typing import TypedDict

from status.core import MODES_LITERAL

from .incidentdata import UpdateField


class ConfChannelSettings(TypedDict):
    mode: MODES_LITERAL
    webhook: bool
    edit_id: dict[str, int]


class _ConfFeedsFields(TypedDict):
    name: str
    value: str
    update_id: str


class ConfFeeds(TypedDict):
    fields: list[_ConfFeedsFields]
    time: int
    title: str
    link: str
    actual_time: int
    description: str
    incident_id: str
    scheduled_for: int


class IncidentDataDict(TypedDict, total=False):
    fields: list[UpdateField]
    time: datetime.datetime | None
    title: str
    link: str
    actual_time: datetime.datetime | None
    description: str
    incident_id: str
    scheduled_for: datetime.datetime | None
