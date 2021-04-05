from redbot.core.bot import Red

from .core.status import Status

__red_end_user_data_statement__ = "This cog does not persistently store data or metadata about users."


def setup(bot: Red):
    bot.add_cog(Status(bot))
