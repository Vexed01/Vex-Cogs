from __future__ import annotations

import contextlib
import importlib
import json
from pathlib import Path

from redbot.core import VersionInfo
from redbot.core.bot import Red
from redbot.core.errors import CogLoadError

from . import vexutils
from .caseinsensitive import CaseInsensitive
from .vexutils.meta import out_of_date_check

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]

INCOMPATIBLE_COGS: list[str] = [""]


async def setup(bot: Red):
    for cog in INCOMPATIBLE_COGS:
        if cog in bot.cogs:
            raise CogLoadError(f"Cog {cog} is incompatible with this cog.")

    cog = CaseInsensitive(bot)
    await out_of_date_check("caseinsensitive", cog.__version__)
    await bot.add_cog(cog)
