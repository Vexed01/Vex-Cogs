from redbot.core.bot import Red

from .aliases import Aliases

__red_end_user_data_statement__ = (
    "This cog does not persistently store data or metadata about users."
)


def setup(bot: Red) -> None:
    bot.add_cog(Aliases(bot))
