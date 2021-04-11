from redbot.core.bot import Red

from .beautify import Beautify


def setup(bot: Red):
    bot.add_cog(Beautify(bot))
