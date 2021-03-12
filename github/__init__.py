from .github import GitHub


def setup(bot):
    bot.add_cog(GitHub(bot))