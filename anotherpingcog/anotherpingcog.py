from time import monotonic

import discord
import tabulate
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

GREEN = "\N{LARGE GREEN CIRCLE}"
ORANGE = "\N{LARGE ORANGE CIRCLE}"
RED = "\N{LARGE RED CIRCLE}"

old_ping = None


class AnotherPingCog(commands.Cog):
    """A rich embed ping command with latency timings."""

    __version__ = "1.0.0"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        docs = "This cog has docs! Check them out at\nhttps://vex-cogs.readthedocs.io/en/latest/cogs/anotherpingcog.html"
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**\n{docs}"
        # adding docs link here so doesn't show up in auto generated docs

    def __init__(self, bot: Red):
        self.bot = bot

    def cog_unload(self):
        global old_ping
        if old_ping:
            try:
                self.bot.remove_command("ping")
            except:
                pass
            self.bot.add_command(old_ping)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    @commands.command(aliases=["pinf", "pig", "png", "pign", "pjgn", "ipng", "pgn", "pnig"])
    async def ping(self, ctx):
        """
        A rich embed ping command with timings.

        This will show the time to send a message, and the WS latency to Discord.
        If I can't send embeds or they are disabled, I will send a message instead.
        The embed has more detail and is preferred.
        """
        ws_latency = round(self.bot.latency * 1000)

        if ctx.invoked_with == "ping":
            title = "\N{TABLE TENNIS PADDLE AND BALL}  Pong!"
        else:
            title = "\N{SMIRKING FACE}  Nice typo!"

        embed = await ctx.embed_requested()

        if embed:
            embed = discord.Embed(title=title)
            embed.add_field(name="Discord WS", value=box(f"{ws_latency} ms", "py"))
            embed.set_footer(
                text="As long as these numbers are below 300, it's nothing to worry about\nScale: Excellent | Good | Alright | Bad | Very Bad"
            )
            start = monotonic()
            message = await ctx.send(embed=embed)
        else:
            msg = f"**{title}**\nDiscord WS: {ws_latency} ms"
            start = monotonic()
            message = await ctx.send(msg)
        end = monotonic()

        m_latency = round((end - start) * 1000)

        # these colours match the emojis
        if ws_latency > 225 or m_latency > 300:
            colour = 14495300  # red
        elif ws_latency > 150 or m_latency > 225:
            colour = 16027660  # orange
        else:
            colour = 7909721  # green

        # im sure there's better way to do this, haven't looked properly yet
        if ws_latency < 50:
            ws_latency_text = f"{GREEN} Excellent"
        elif ws_latency < 150:
            ws_latency_text = f"{GREEN} Good"
        elif ws_latency < 250:
            ws_latency_text = f"{ORANGE} Alright"
        elif ws_latency < 500:
            ws_latency_text = f"{RED} Bad"
        else:
            ws_latency_text = f"{RED} Very Bad"

        if m_latency < 75:
            m_latency_text = f"{GREEN} Excellent"
        elif m_latency < 225:
            m_latency_text = f"{GREEN} Good"
        elif m_latency < 300:
            m_latency_text = f"{ORANGE} Alright"
        elif m_latency < 600:
            m_latency_text = f"{RED} Bad"
        else:
            m_latency_text = f"{RED} Very Bad"

        if embed:
            extra = box(f"{ws_latency} ms", "py")
            embed.set_field_at(0, name="Discord WS", value=f"{ws_latency_text}{extra}")
            extra = box(f"{m_latency} ms", "py")
            embed.add_field(name="Message send time", value=f"{m_latency_text}{extra}")
            embed.colour = colour
            await message.edit(embed=embed)
        else:
            data = [
                ["Discord WS", "Message send time"],
                [ws_latency_text, m_latency_text],
                [f"{ws_latency} ms", f"{m_latency} ms"],
            ]
            table = box(tabulate.tabulate(data, tablefmt="plain"), "py")
            msg = f"**{title}**{table}"
            await message.edit(content=msg)


def setup(bot: Red):
    apc = AnotherPingCog(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(apc)
