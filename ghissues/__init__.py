import importlib
import json
from pathlib import Path

import vexcogutils
from redbot.core import VersionInfo
from redbot.core.bot import Red

# VCU reload needs to be done before importing files that depend on new version
if VersionInfo.from_str(vexcogutils.__version__) < VersionInfo.from_str("1.4.6"):
    importlib.reload(vexcogutils)

from .ghissues import GHIssues

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


def setup(bot: Red) -> None:
    bot.add_cog(GHIssues(bot))
