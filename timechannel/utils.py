import datetime
from typing import Dict

import pytz

from .data import ZONE_KEYS


def gen_replacements() -> Dict[str, str]:
    # there are roughly 500 items so 5 opportunities to hand back control with a step of 100
    replacements: Dict[str, str] = {}
    for key, zone in ZONE_KEYS.items():
        foramtted_time = datetime.datetime.now(pytz.timezone(zone)).strftime("%I:%M%p").lstrip("0")
        replacements[key] = foramtted_time
    return replacements
