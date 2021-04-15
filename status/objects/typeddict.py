import datetime
from typing import Dict, List, Optional, TypedDict

from status.core import MODES_LITERAL

from .incidentdata import UpdateField


class ConfChannelSettings(TypedDict):
    mode: MODES_LITERAL
    webhook: bool
    edit_id: Dict[str, int]


class _ConfFeedsFields(TypedDict):
    name: str
    value: str
    update_id: str


class ConfFeeds(TypedDict):
    fields: List[_ConfFeedsFields]
    time: int
    title: str
    link: str
    actual_time: int
    description: str
    incident_id: str
    scheduled_for: int


class IncidentDataDict(TypedDict, total=False):
    fields: List[UpdateField]
    time: Optional[datetime.datetime]
    title: str
    link: str
    actual_time: Optional[datetime.datetime]
    description: str
    incident_id: str
    scheduled_for: Optional[datetime.datetime]
