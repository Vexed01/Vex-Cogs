import datetime
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from redbot.core.utils import deduplicate_iterables


class UpdateField:
    """An object representing an update in a IncidentData"""

    def __init__(self, name: str, value: str, update_id: str = None):
        self.name = name
        self.value = value
        self.update_id = update_id

    def __repr__(self):
        return 'UpdateField("{}", "{}", "{}")'.format(
            self.name, self.value.replace("\n", "\\n"), self.update_id
        )


@dataclass
class IncidentData:
    """An object representing a fully parsed service status."""

    title: str
    link: str
    incident_id: str
    description: str
    fields: List[UpdateField] = field(default_factory=list)
    time: Optional[datetime.datetime] = None
    actual_time: Optional[datetime.datetime] = None
    scheduled_for: Optional[datetime.datetime] = None

    def __repr__(self):
        return (
            f'IncidentData({self.fields}, {self.time}, "{self.title}", "{self.link}", '
            f'{self.actual_time}, "{self.description}", "{self.incident_id}", '
            f'"{self.scheduled_for}")'
        )

    def to_dict(self) -> Dict[str, Any]:
        """Get a dict of the data held in the object."""
        fields = [
            {"name": field.name, "value": field.value, "update_id": field.update_id}
            for field in self.fields
        ]
        return {
            "fields": fields,
            "time": self.time,
            "title": self.title,
            "link": self.link,
            "actual_time": self.actual_time,
            "description": self.description,
            "incident_id": self.incident_id,
            "scheduled_for": self.scheduled_for,
        }

    def get_update_ids(self) -> List[str]:
        """Get the group IDs for this feed, in order."""
        return deduplicate_iterables([field.update_id for field in self.fields])


@dataclass
class Update:
    """Has the IncidentData of the valid update and the new field(s)."""

    incidentdata: IncidentData
    new_fields: List[UpdateField]
