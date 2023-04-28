from redbot.core.bot import Red
from redbot.core.errors import CogLoadError


async def setup(bot: Red) -> None:
    raise CogLoadError(
        "This cog has been replaced by my `ghissues` cog. Please uninstall this cog and install "
        "that instead."
    )
