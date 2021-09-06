import contextlib
import importlib
import json
from pathlib import Path

import vexcogutils
from redbot.core import VersionInfo
from redbot.core.bot import Red

# VCU reload needs to be done before importing files that depend on new version
if VersionInfo.from_str(vexcogutils.__version__) < VersionInfo.from_str("1.5.7"):
    importlib.reload(vexcogutils.version)
    importlib.reload(vexcogutils.consts)

    importlib.reload(vexcogutils.chat)
    importlib.reload(vexcogutils.meta)
    importlib.reload(vexcogutils.loop)

    with contextlib.suppress(AttributeError):  # these are not necessarily already imported
        # importlib.reload(vexcogutils.sqldriver)
        importlib.reload(vexcogutils.sentry)

    importlib.reload(vexcogutils)
from .aliases import Aliases

with open(Path(__file__).parent / "info.json", encoding="utf8") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


def setup(bot: Red) -> None:
    if vexcogutils.bot is None:
        vexcogutils.bot = bot

    bot.add_cog(Aliases(bot))
