from .status import Status


def setup(bot):
    bot.add_cog(Status(bot))
