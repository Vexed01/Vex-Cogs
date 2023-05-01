from redbot.core.errors import CogLoadError


async def setup(_):
    raise CogLoadError(
        "This cog will not be updated to be compatible with Red 3.5 due to irrelevance and data "
        "issues, and has therefore been removed."
    )
