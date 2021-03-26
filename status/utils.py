# ======== PLEASE READ ======================================================
# Status is currently a bit of a mess. For this reason, I'll be undertaking a
# rewrite in the near future: https://github.com/Vexed01/Vex-Cogs/issues/13
#
# For this reason, unless it's minor, PLEASE DO NOT OPEN A PR.
# ===========================================================================


import datetime

from discord import Embed

from .objects import FeedDict


def serialize(feeddict: dict):
    """Serialize a feeddict."""
    if isinstance(feeddict["time"], datetime.datetime):
        feeddict["time"] = feeddict["time"].timestamp()
    else:
        feeddict["time"] = ""
    if isinstance(feeddict["actual_time"], datetime.datetime):
        feeddict["actual_time"] = feeddict["actual_time"].timestamp()
    elif isinstance(feeddict["actual_time"], float):  # can happen, not a proper fix
        pass
    else:
        feeddict["actual_time"] = ""
    return feeddict


def deserialize(feeddict: dict):
    """Deserialize a feeddict."""
    if feeddict["time"]:
        feeddict["time"] = datetime.datetime.fromtimestamp(feeddict["time"])
    else:
        feeddict["time"] = Embed.Empty
    if feeddict["actual_time"]:
        feeddict["actual_time"] = datetime.datetime.fromtimestamp(feeddict["actual_time"])
    else:
        feeddict["actual_time"] = Embed.Empty
    return FeedDict().from_dict(feeddict)
