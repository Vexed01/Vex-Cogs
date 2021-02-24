from time import monotonic

import discord
import tabulate
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

GREEN = "\N{LARGE GREEN CIRCLE}"
ORANGE = "\N{LARGE ORANGE CIRCLE}"
RED = "\N{LARGE RED CIRCLE}"


class AnotherPingCog(commands.Cog):
    """A rich embed ping command with timings"""

    __version__ = "1.0.0"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**"

    def __init__(self, bot: Red):
        bot.remove_command("ping")
        self.bot = bot

    @commands.command(aliases=["pinf", "pig", "png", "pign", "pjgn", "ipng", "pgn"])
    async def ping(self, ctx):
        """A rich embed ping command with timings"""
        discordlatency = round(self.bot.latency * 1000)

        if ctx.invoked_with == "ping":
            title = "\N{TABLE TENNIS PADDLE AND BALL}  Pong!"
        else:
            title = "\N{SMIRKING FACE}  Nice typo!"

        embed = await ctx.embed_requested()

        if embed:
            embed = discord.Embed(title=title)
            embed.add_field(name="Discord API", value=box(f"{discordlatency} ms", "py"))
            embed.set_footer(
                text="As long as these numbers are below 300, it's nothing to worry about\nScale: Excellent | Good | Bad | Very Bad"
            )
            start = monotonic()
            message = await ctx.send(embed=embed)
        else:
            msg = f"**{title}**\nDiscord API: {discordlatency} ms"
            start = monotonic()
            message = await ctx.send(msg)
        end = monotonic()

        messagelatency = round((end - start) * 1000)

        # these colours match the emojis
        if discordlatency > 225 or messagelatency > 300:
            colour = 14495300  # red
        elif discordlatency > 150 or messagelatency > 225:
            colour = 16027660  # orange
        else:
            colour = 7909721  # green

        if discordlatency < 50:
            discordlatencym = f"{GREEN} Excellent"
        elif discordlatency < 150:
            discordlatencym = f"{GREEN} Good"
        elif discordlatency < 250:
            discordlatencym = f"{ORANGE} Alright"
        elif discordlatency < 500:
            discordlatencym = f"{RED} Bad"
        else:
            discordlatencym = f"{RED} Very Bad"

        if messagelatency < 75:
            messagelatencym = f"{GREEN} Excellent"
        elif messagelatency < 225:
            messagelatencym = f"{GREEN} Good"
        elif messagelatency < 300:
            messagelatencym = f"{ORANGE} Alright"
        elif messagelatency < 600:
            messagelatencym = f"{RED} Bad"
        else:
            messagelatencym = f"{RED} Very Bad"

        if embed:
            extra = box(f"{discordlatency} ms", "py")
            embed.set_field_at(0, name="Discord API", value=f"{discordlatencym}{extra}")
            extra = box(f"{messagelatency} ms", "py")
            embed.add_field(name="Message send", value=f"{messagelatencym}{extra}")
            embed.colour = colour
            await message.edit(embed=embed)
        else:
            data = [
                ["Discord API", "Message Send"],
                [discordlatencym, messagelatencym],
                [f"{discordlatency} ms", f"{messagelatency} ms"],
            ]
            table = box(tabulate.tabulate(data, tablefmt="plain"), "py")
            msg = f"**{title}**{table}"
            await message.edit(content=msg)
