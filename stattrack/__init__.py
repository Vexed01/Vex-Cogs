import contextlib
import importlib
import json
from pathlib import Path

import vexcogutils
from redbot.core import VersionInfo
from redbot.core.bot import Red
from vexcogutils.meta import out_of_date_check

# VCU reload needs to be done before importing files that depend on new version
if VersionInfo.from_str(vexcogutils.__version__) < VersionInfo.from_str("1.5.9"):
    importlib.reload(vexcogutils.version)
    importlib.reload(vexcogutils.consts)

    importlib.reload(vexcogutils.chat)
    importlib.reload(vexcogutils.meta)
    importlib.reload(vexcogutils.loop)

    importlib.reload(vexcogutils)
from .stattrack import StatTrack

with open(Path(__file__).parent / "info.json", encoding="utf8") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    if vexcogutils.bot is None:
        vexcogutils.bot = bot

    cog = StatTrack(bot)
    await out_of_date_check("stattrack", cog.__version__)
    await cog.async_init()
    bot.add_cog(cog)
