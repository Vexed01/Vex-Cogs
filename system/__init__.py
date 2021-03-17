from .system import System


def setup(bot):
    bot.add_cog(System(bot))
