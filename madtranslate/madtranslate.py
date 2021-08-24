import asyncio
import logging
import random
from typing import List, Optional, Tuple
from urllib.parse import urlencode

import aiohttp
import discord
import sentry_sdk
import vexcogutils
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from vexcogutils import format_help, format_info
from vexcogutils.meta import out_of_date_check

from .langs import LANGS

log = logging.getLogger("red.vex.madtranslate")

ARROW = " → "


class ForbiddenExc(Exception):
    pass


BASE = "https://clients5.google.com/translate_a/t?"
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
}


async def get_translation(ctx: commands.Context, session: aiohttp.ClientSession, sl, tl, q) -> str:
    query = {
        "client": "dict-chrome-ex",
        "sl": sl,
        "tl": tl,
        "q": q,
    }
    resp = await session.get(BASE + urlencode(query))
    if resp.status == 403:
        raise ForbiddenExc

    as_json = await resp.json()
    if sl == "auto":
        await ctx.send(f"I've detected the input language as {as_json['src']}")
        await asyncio.sleep(0.1)
        await ctx.trigger_typing()
    return as_json["sentences"][0]["trans"]


def gen_langs(count: int, seed: Optional[int] = None) -> Tuple[str, List[Tuple[str, str]]]:
    if seed is None:
        seed = random.randrange(100_000, 999_999)
    gen = random.Random(seed)

    count_seed_par = f"{count}-{seed}"
    return count_seed_par, gen.sample(LANGS, k=count)


class MadTranslate(commands.Cog):
    """
    Translate things into lots of languages then back to English!

    This will defiantly have some funny moments... Take everything with a pinch of salt!
    """

    __version__ = "1.0.1"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red):
        self.bot = bot

        asyncio.create_task(self.async_init())

        # =========================================================================================
        # NOTE: IF YOU ARE EDITING MY COGS, PLEASE ENSURE SENTRY IS DISBALED BY FOLLOWING THE INFO
        # IN async_init(...) BELOW (SENTRY IS WHAT'S USED FOR TELEMETRY + ERROR REPORTING)
        self.sentry_hub: Optional[sentry_sdk.Hub] = None
        # =========================================================================================

    async def async_init(self):
        await out_of_date_check("madtranslate", self.__version__)

        # =========================================================================================
        # TO DISABLE SENTRY FOR THIS COG (EG IF YOU ARE EDITING THIS COG) EITHER DISABLE SENTRY
        # WITH THE `[p]vextelemetry` COMMAND, OR UNCOMMENT THE LINE BELOW, OR REMOVE IT COMPLETELY:
        # return

        while vexcogutils.sentryhelper.ready is False:
            await asyncio.sleep(0.1)

        await vexcogutils.sentryhelper.maybe_send_owners("madtranslate")

        if vexcogutils.sentryhelper.sentry_enabled is False:
            log.debug("Sentry detected as disabled.")
            return

        log.debug("Sentry detected as enabled.")
        self.sentry_hub = await vexcogutils.sentryhelper.get_sentry_hub(
            "madtranslate", self.__version__
        )
        # =========================================================================================

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.bot.on_command_error(ctx, error, unhandled_by_cog=True)  # type:ignore

        if self.sentry_hub is None:  # sentry disabled
            return

        with self.sentry_hub:
            sentry_sdk.add_breadcrumb(
                category="command", message="Command used was " + ctx.command.qualified_name
            )
            sentry_sdk.capture_exception(error.original)  # type:ignore
            log.debug("Above exception successfully reported to Sentry")

    def cog_unload(self):
        if self.sentry_hub:
            self.sentry_hub.end_session()
            self.sentry_hub.client.close()

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def madtranslateinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(self.qualified_name, self.__version__))

    @commands.command(aliases=["mtranslate", "mtrans"])
    async def madtranslate(
        self, ctx: commands.Context, count: Optional[int] = 15, *, text_to_translate: str
    ):
        """Translate something into lots of languages, then back to English!

        **Examples:**
            - `[p]mtrans This is a sentence.`
            - `[p]mtrans 25 Here's another one.`

        At the bottom of the output embed is a count-seed pair. You can use this with
        the `mtransseed` command to use the same language set.
        """
        assert count is not None
        if count > 50:
            return await ctx.send("That's a bit big... How about a lower number?")
        q = text_to_translate
        session = aiohttp.ClientSession(headers=HEADERS)
        count_seed, langs = gen_langs(count)
        langs.append(("English", "en"))
        sl = "auto"
        async with ctx.typing():
            for _, tl in langs:
                try:
                    q = await get_translation(ctx, session, sl, tl, q)
                except ForbiddenExc:
                    return await ctx.send("Something went wrong.")
                sl = tl

        await session.close()

        embed = discord.Embed(
            colour=await ctx.embed_color(), title=f"Translation through {count} languages"
        )
        embed.add_field(name="Original text", value=box(text_to_translate), inline=False)
        embed.add_field(name="Translated text", value=box(q), inline=False)
        embed.add_field(name="Languages", value=box(ARROW.join(i[0] for i in langs)), inline=False)
        embed.set_footer(text=f"count-seed pair: {count_seed}")
        await ctx.send(embed=embed)

    @commands.command()
    async def mtransseed(self, ctx: commands.Context, count_seed: str, *, text_to_translate: str):
        """Use a count-seed pair to (hopefully) get reproducible results.

        They may be unreproducible if Google Translate changes its translations.

        The count-seed pair is obtained from the main command, `mtrans`, in the embed footer.

        **Examples:**
            - `[p]mtrans 15-111111 This is a sentence.`
            - `[p]mtrans 25-000000 Here's another one.`
        """
        split = count_seed.split("-")
        if (
            len(split) != 2
            or not split[0].isdigit()
            or not split[1].isdigit()
            or len(split[0]) > 50
            or len(split[1]) != 6
        ):
            return await ctx.send("That count-seed pair doesn't look valid.")
        count, seed = int(split[0]), int(split[1])
        q = text_to_translate
        session = aiohttp.ClientSession(headers=HEADERS)
        count_seed, langs = gen_langs(count, seed)
        langs.append(("English", "en"))
        sl = "auto"
        async with ctx.typing():
            for _, tl in langs:
                try:
                    q = await get_translation(ctx, session, sl, tl, q)
                except ForbiddenExc:
                    return await ctx.send("Something went wrong.")
                sl = tl

        await session.close()

        embed = discord.Embed(
            colour=await ctx.embed_color(), title=f"Translation through {count} languages"
        )
        embed.add_field(name="Original text", value=box(text_to_translate), inline=False)
        embed.add_field(name="Translated text", value=box(q), inline=False)
        embed.add_field(name="Languages", value=box(ARROW.join(i[0] for i in langs)), inline=False)
        embed.set_footer(text=f"Seed: {count_seed}")
        await ctx.send(embed=embed)
