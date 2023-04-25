from __future__ import annotations

import random
from typing import Optional
from urllib.parse import urlencode

import aiohttp
import discord
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

from .langs import LANGS
from .vexutils import format_help, format_info, get_vex_logger

log = get_vex_logger(__name__)

ARROW = " → "


class ForbiddenExc(Exception):
    pass


BASE = "https://clients5.google.com/translate_a/t?"
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/90.0.4430.212 Safari/537.36"
    )
}


async def get_translation(session: aiohttp.ClientSession, sl: str, tl: str, q: str) -> str:
    query = {
        "client": "dict-chrome-ex",
        "sl": sl,  # source language
        "tl": tl,  # target language
        "q": q,  # query
    }
    resp = await session.get(BASE + urlencode(query))
    if resp.status == 403:
        raise ForbiddenExc

    as_json = await resp.json()
    return as_json[0]


def gen_langs(count: int, seed: int | None = None) -> tuple[str, list[tuple[str, str]]]:
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

    __version__ = "1.0.3"
    __author__ = "Vexed#0714"

    def __init__(self, bot: Red):
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def madtranslateinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

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
                    q = await get_translation(session, sl, tl, q)
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
                    q = await get_translation(session, sl, tl, q)
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
