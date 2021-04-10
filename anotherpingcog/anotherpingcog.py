import asyncio
import re
from time import monotonic
from typing import Optional

import discord
import tabulate
from discord.emoji import Emoji
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from vexcogutils import format_help, format_info

from .objects import Cache, Settings

DEFAULT = "default"

DEFAULT_CONF = {
    "red": {"emoji": None, "colour": None},
    "orange": {"emoji": None, "colour": None},
    "green": {"emoji": None, "colour": None},
}

LEFT_ARROW = "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}"


old_ping = None


class AnotherPingCog(commands.Cog):
    """
    A rich embed ping command with latency timings.

    You can customise the emojis, colours or force embeds with `[p]pingset`.
    """

    __version__ = "1.1.3"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(force_embed=True)
        self.config.register_global(custom_settings=DEFAULT_CONF)

        asyncio.create_task(self._make_cache())

    def cog_unload(self) -> None:
        global old_ping
        if old_ping:
            try:
                self.bot.remove_command("ping")
            except Exception:
                pass
            self.bot.add_command(old_ping)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    async def _make_cache(self) -> None:
        self.cache = Cache(
            await self.config.custom_settings(), await self.config.force_embed(), self.bot
        )

    @commands.command(hidden=True)
    async def apcinfo(self, ctx: commands.Context):
        await ctx.send(format_info(self.qualified_name, self.__version__))

    # cspell:disable-next-line
    @commands.command(aliases=["pinf", "pig", "png", "pign", "pjgn", "ipng", "pgn", "pnig"])
    async def ping(self, ctx: commands.Context):
        """
        A rich embed ping command with timings.

        This will show the time to send a message, and the WS latency to Discord.
        If I can't send embeds or they are disabled here, I will send a normal message instead.
        The embed has more detail and is preferred.
        """
        ws_latency = round(self.bot.latency * 1000)

        title = (
            "\N{TABLE TENNIS PADDLE AND BALL}  Pong!"
            if ctx.invoked_with == "ping"
            else "\N{SMIRKING FACE}  Nice typo!"
        )

        settings = self.cache

        if ctx.guild:
            if settings.force_embed:
                use_embed = ctx.channel.permissions_for(ctx.me).embed_links  # type:ignore
                # ignoring because already check if in guild
            else:
                use_embed = await ctx.embed_requested()
        else:
            use_embed = True

        if use_embed:
            embed = discord.Embed(title=title)
            embed.add_field(name="Discord WS", value=box(f"{ws_latency} ms", "py"))
            embed.set_footer(
                text="If the bot feels fast, don't worry about high numbers\nScale: Excellent | "
                "Good | Alright | Bad | Very Bad"
            )
            start = monotonic()
            message: discord.Message = await ctx.send(embed=embed)
        else:
            msg = f"**{title}**\nDiscord WS: {ws_latency} ms"
            start = monotonic()
            message = await ctx.send(msg)
        end = monotonic()

        # im sure there's better way to do these long ifs, haven't looked properly yet

        m_latency = round((end - start) * 1000)
        if embed:
            colour = self._get_emb_colour(ws_latency, m_latency, settings)

        ws_latency_text, m_latency_text = self._get_latency_text(
            ws_latency, m_latency, settings, use_embed
        )

        if use_embed:
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
            table = box(tabulate.tabulate(data, tablefmt="plain"), "py")  # cspell: disable-line
            msg = f"**{title}**{table}"
            await message.edit(content=msg)

    # im sure there's better way to do these two methods but i cba to find one

    def _get_emb_colour(self, ws_latency: int, m_latency: int, settings: Cache):
        if ws_latency > 250 or m_latency > 350:
            return settings.red.colour
        elif ws_latency > 150 or m_latency > 225:
            return settings.orange.colour
        else:
            return self.cache.green.colour

    def _get_latency_text(self, ws_latency: int, m_latency: int, settings: Cache, emojis: bool):
        if ws_latency < 50:
            ws_latency_text = f"{settings.green.emoji} Excellent" if emojis else "Excellent"
        elif ws_latency < 150:
            ws_latency_text = f"{settings.green.emoji} Good" if emojis else "Good"
        elif ws_latency < 250:
            ws_latency_text = f"{settings.orange.emoji} Alright" if emojis else "Alright"
        elif ws_latency < 500:
            ws_latency_text = f"{settings.red.emoji} Bad" if emojis else "Bad"
        else:
            ws_latency_text = f"{settings.red.emoji} Very Bad" if emojis else "Very Bad"

        if m_latency < 75:
            m_latency_text = f"{settings.green.emoji} Excellent" if emojis else "Excellent"
        elif m_latency < 225:
            m_latency_text = f"{settings.green.emoji} Good" if emojis else "Good"
        elif m_latency < 350:
            m_latency_text = f"{settings.orange.emoji} Alright" if emojis else "Alright"
        elif m_latency < 600:
            m_latency_text = f"{settings.red.emoji} Bad" if emojis else "Bad"
        else:
            m_latency_text = f"{settings.red.emoji} Very Bad" if emojis else "Very Bad"

        return ws_latency_text, m_latency_text

    @checks.is_owner()
    @commands.group()
    async def pingset(self, ctx: commands.Context):
        """Manage settings - emojis, embed colour, and force embed."""

    @pingset.command()
    async def forceembed(self, ctx: commands.Context):
        """
        Toggle whether embeds should be forced.

        If this is disabled, embeds will depend on the settings in `embedset`.

        If it's enabled, embeds will embeds will always be sent unless the bot doesn't
        have permission to send them.

        By default, this is True because the embed is richer and has more information.
        And it looks looks better.

        This will be removed when a global per-command settings is available in Core Red.
        """
        new_setting = not (await self.config.force_embed())
        await self.config.force_embed.set(new_setting)
        self.cache.force_embed = new_setting
        if new_setting:
            await ctx.send(
                "The `ping` command will now always be sent as an embed, unless the bot doesn't "
                "have permission to send them."
            )
        else:
            await ctx.send(
                "The `embedset` command will now decide whether or not to send an embed, which "
                "is by default True."
            )

    # DRY's gone out the window here...
    # TODO: emoji + hex converter

    @pingset.command()
    async def red(self, ctx: commands.Context, emoji: str, hex_colour: str = "default"):
        """
        Set the colour and emoji to use for the colour Red.

        If you want to go back to the defaults, just do `[p]pingset red default default`.

        **Arguments:**

        `<emoji>`
        Just send the emoji as you normally would. It must be a custom emoji and I must
        be in the sever the emoji is in.
        You can also put `default` to use \N{LARGE RED CIRCLE}

        `[hex_colour]` (optional)
        The hex code you want the colour for Red to be. It looks best when this is the
        same colour as the emoji. Google "hex colour" if you need help with this.
        """
        if emoji.casefold() == "default":
            await self.config.custom_settings.set_raw("red", "emoji", value=None)  # type:ignore
            emoji_toset = None
        else:
            match = re.match(r"(<.*:)([0-9]{17,20})(>)", str(emoji))
            bot_emoji: Optional[Emoji] = self.bot.get_emoji(int(match.group(2))) if match else None
            if not bot_emoji:
                return await ctx.send(
                    "It looks like that's not a valid custom emoji. I'm probably not in the "
                    "server the emoji was added to."
                )
            emoji_toset = bot_emoji.id
            await self.config.custom_settings.set_raw(  # type:ignore
                "red", "emoji", value=emoji_toset
            )
        if hex_colour.casefold() == "default":
            await self.config.custom_settings.set_raw("red", "colour", value=None)  # type:ignore
            hex = None
        else:
            try:
                int_colour = int(hex_colour, 16)
            except ValueError:  # not base 16
                int_colour = 16777216
            if int_colour > 16777215:  # max value
                return await ctx.send(
                    'That doesn\'t look like a valid colour. Google "hex colour" for some '
                    "converters."
                )
            await self.config.custom_settings.set_raw(  # type:ignore
                "red", "colour", value=int_colour
            )
            hex = int_colour

        self.cache.set("red", Settings(emoji_toset, hex))

        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"This is the new emoji: {str(self.cache.red.emoji)}",
                description=f"{LEFT_ARROW} This is the new colour",
                colour=self.cache.red.colour,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The emoji is {str(self.cache.red.emoji)} and I've set the colour.")

    @pingset.command()
    async def orange(self, ctx: commands.Context, emoji: str, hex_colour: str = "default"):
        """
        Set the colour and emoji to use for the colour Orange.

        If you want to go back to the defaults, just do `[p]pingset orange default default`.

        **Arguments:**

        `<emoji>`
        Just send the emoji as you normally would. It must be a custom emoji and I must
        be in the sever the emoji is in.
        You can also put `default` to use \N{LARGE ORANGE CIRCLE}

        `[hex_colour]` (optional)
        The hex code you want the colour for Red to be. It looks best when this is the
        same colour as the emoji. Google "hex colour" if you need help with this.
        """
        if emoji.casefold() == "default":
            await self.config.custom_settings.set_raw("orange", "emoji", value=None)  # type:ignore
            emoji_toset = None
        else:
            match = re.match(r"(<.*:)([0-9]{17,20})(>)", str(emoji))
            bot_emoji = self.bot.get_emoji(int(match.group(2))) if match else None
            if not bot_emoji:
                return await ctx.send(
                    "It looks like that's not a valid custom emoji. I'm probably not in the "
                    "server the emoji was added to."
                )
            emoji_toset = bot_emoji.id
            await self.config.custom_settings.set_raw(  # type:ignore
                "orange", "emoji", value=emoji_toset
            )
        if hex_colour.casefold() == "default":
            await self.config.custom_settings.set_raw(  # type:ignore
                "orange", "colour", value=None
            )
            hex = None
        else:
            try:
                int_colour = int(hex_colour, 16)
            except ValueError:  # not base 16
                int_colour = 16777216
            if int_colour > 16777215:  # max value
                return await ctx.send(
                    'That doesn\'t look like a valid colour. Google "hex colour" for some '
                    "converters."
                )
            await self.config.custom_settings.set_raw(  # type:ignore
                "orange", "colour", value=int_colour
            )
            hex = int_colour

        self.cache.set("orange", Settings(emoji_toset, hex))

        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"This is the new emoji: {str(self.cache.orange.emoji)}",
                description=f"{LEFT_ARROW} This is the new colour",
                colour=self.cache.orange.colour,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The emoji is {str(self.cache.orange.emoji)} and I've set the colour.")

    @pingset.command()
    async def green(self, ctx: commands.Context, emoji: str, hex_colour: str = "default"):
        """
        Set the colour and emoji to use for the colour Green.

        If you want to go back to the defaults, just do `[p]pingset green default default`.

        **Arguments:**

        `<emoji>`
        Just send the emoji as you normally would. It must be a custom emoji and I must
        be in the sever the emoji is in.
        You can also put `default` to use \N{LARGE GREEN CIRCLE}

        `[hex_colour]` (optional)
        The hex code you want the colour for Red to be. It looks best when this is the
        same colour as the emoji. Google "hex colour" if you need help with this.
        """
        if emoji.casefold() == "default":
            await self.config.custom_settings.set_raw("green", "emoji", value=None)  # type:ignore
            emoji_toset = None
        else:
            match = re.match(r"(<.*:)([0-9]{17,20})(>)", str(emoji))
            bot_emoji = self.bot.get_emoji(int(match.group(2))) if match else None
            if not bot_emoji:
                return await ctx.send(
                    "It looks like that's not a valid custom emoji. I'm probably not in the "
                    "server the emoji was added to."
                )
            emoji_toset = bot_emoji.id
            await self.config.custom_settings.set_raw(  # type:ignore
                "green", "emoji", value=emoji_toset
            )
        if hex_colour.casefold() == "default":
            await self.config.custom_settings.set_raw("green", "colour", value=None)  # type:ignore
            hex = None
        else:
            try:
                int_colour = int(hex_colour, 16)
            except ValueError:  # not base 16
                int_colour = 16777216
            if int_colour > 16777215:  # max value
                return await ctx.send(
                    'That doesn\'t look like a valid colour. Google "hex colour" for some '
                    "converters."
                )
            await self.config.custom_settings.set_raw(  # type:ignore
                "green", "colour", value=int_colour
            )
            hex = int_colour

        self.cache.set("green", Settings(emoji_toset, hex))

        if await ctx.embed_requested():
            embed = discord.Embed(
                title=f"This is the new emoji: {str(self.cache.green.emoji)}",
                description=f"{LEFT_ARROW} This is the new colour",
                colour=self.cache.green.colour,
            )
            await ctx.send(embed=embed)
        else:
            await ctx.send(f"The emoji is {str(self.cache.green.emoji)} and I've set the colour.")

    @pingset.command()
    async def settings(self, ctx: commands.Context):
        """See your current settings."""
        if ctx.guild and not ctx.channel.permissions_for(ctx.me).embed_links:  # type:ignore
            # checking if guild so doesn't matter
            return await ctx.send(
                "I need to send this as an embed because Vexed is lazy and won't make a "
                "non-embed version."
            )
        settings = self.cache
        embed = discord.Embed(title="Global settings for the `ping` command.")
        embeds = "**Force embed settings:**\n"
        embeds += (
            "True - will as an embed, unless the bot doesn't have permission to send them."
            if settings.force_embed
            else "False - `embedset` is how embeds will be determined (defaults to True)."
        )
        embed.add_field(name="Embeds", value=embeds)

        # these 3 are alright with the 5/5 rate limit, plus it's owner only.
        # if anyone wants to PR something with image generation, don't as it's wayyyyy to complex
        # for this
        await ctx.send(
            content=embeds,
            embed=discord.Embed(
                title=f"Emoji for green: {str(self.cache.green.emoji)}",
                description=f"{LEFT_ARROW} Colour for green",
                colour=self.cache.green.colour,
            ),
        )
        await ctx.send(
            embed=discord.Embed(
                title=f"Emoji for orange: {str(self.cache.orange.emoji)}",
                description=f"{LEFT_ARROW} Colour for orange",
                colour=self.cache.orange.colour,
            )
        )
        await ctx.send(
            embed=discord.Embed(
                title=f"Emoji for red: {str(self.cache.red.emoji)}",
                description=f"{LEFT_ARROW} Colour for red",
                colour=self.cache.red.colour,
            )
        )


def setup(bot: Red) -> None:
    apc = AnotherPingCog(bot)
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)
    bot.add_cog(apc)
