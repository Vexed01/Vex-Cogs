import contextlib
import importlib
import json
from pathlib import Path

import discord
from redbot.core import VersionInfo
from redbot.core.bot import Red
from redbot.core.errors import CogLoadError

from . import vexutils
from .vexutils.meta import out_of_date_check

if discord.__version__.startswith("1"):
    raise CogLoadError(
        "This cog requires discord.py 2.x, which is currently incompatible with Red and most "
        "other cogs. This cog is marked as hidden for a reason."
    )

from .buttonopll import ButtonPoll

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red):
    cog = ButtonPoll(bot)
    await cog.async_init()
    await out_of_date_check("buttonpoll", cog.__version__)
    bot.add_cog(cog)
