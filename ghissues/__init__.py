import importlib
import json
from pathlib import Path

import discord
from redbot.core import VersionInfo
from redbot.core.bot import Red
from redbot.core.errors import CogLoadError

from .vexutils.meta import out_of_date_check

if discord.__version__.startswith("1"):
    raise CogLoadError(
        "This cog requires Red 3.5/discord.py 2, which is unstable and incompatible with most  "
        "other cogs. This cog is marked as hidden for a reason."
    )

from .ghissues import GHIssues  # this has dpy 2 stuff in it

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    cog = GHIssues(bot)
    await out_of_date_check("ghissues", cog.__version__)
    await bot.add_cog(cog)
