import json
from pathlib import Path

from redbot.core.bot import Red

from .stattrack import StatTrack

with open(Path(__file__).parent / "info.json", encoding="utf8") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


def setup(bot: Red) -> None:
    bot.add_cog(StatTrack(bot))
