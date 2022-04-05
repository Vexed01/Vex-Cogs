import json
from pathlib import Path

from redbot.core.bot import Red

from .aliases import Aliases
from .vexutils.meta import out_of_date_check

with open(Path(__file__).parent / "info.json", encoding="utf8") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    cog = Aliases(bot)
    await out_of_date_check("aliases", cog.__version__)

    r = bot.add_cog(cog)
    if r is not None:
        await r
