import json
from pathlib import Path

from redbot.core.bot import Red

from .uptimeresponder import UptimeResponder
from .vexutils import out_of_date_check

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def setup(bot: Red) -> None:
    cog = UptimeResponder(bot)
    await out_of_date_check("uptimeresponder", cog.__version__)
    await bot.add_cog(cog)
