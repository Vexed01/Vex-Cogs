import contextlib
import importlib
import json
from pathlib import Path

import discord
from redbot.core import VersionInfo
from redbot.core.bot import Red
from redbot.core.errors import CogLoadError

from . import vexutils
from .calc import Calc
from .vexutils.meta import out_of_date_check

with open(Path(__file__).parent / "info.json", encoding="utf8") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    cog = Calc(bot)
    await out_of_date_check("calc", cog.__version__)
    await bot.add_cog(cog)
