import asyncio
import logging
import re
from time import monotonic
from typing import Optional

import discord
import sentry_sdk
import tabulate
import vexcogutils
from discord.emoji import Emoji
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box
from vexcogutils import format_help, format_info
from vexcogutils.meta import out_of_date_check

from .objects import Cache, Settings

log = logging.getLogger("red.vex.anotherpingcog")


DEFAULT = "default"

DEFAULT_CONF = {
    "red": {"emoji": None, "colour": None},
    "orange": {"emoji": None, "colour": None},
    "green": {"emoji": None, "colour": None},
}

DEFAULT_FOOTER = (
    "If the bot feels fast, don't worry about high numbers\nScale: Excellent | "
    "Good | Alright | Bad | Very Bad"
)

LEFT_ARROW = "\N{LEFTWARDS BLACK ARROW}\N{VARIATION SELECTOR-16}"


old_ping = None


class AnotherPingCog(commands.Cog):
    """
    A rich embed ping command with latency timings.

    You can customise the emojis, colours or force embeds with `[p]pingset`.
    """

    __version__ = "1.1.5"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(force_embed=True, footer="default")
        self.config.register_global(custom_settings=DEFAULT_CONF)

        asyncio.create_task(self.async_init())

        # =========================================================================================
        # NOTE: IF YOU ARE EDITING MY COGS, PLEASE ENSURE SENTRY IS DISBALED BY FOLLOWING THE INFO
        # IN async_init(...) BELOW (SENTRY IS WHAT'S USED FOR TELEMETRY + ERROR REPORTING)
        self.sentry_hub: Optional[sentry_sdk.Hub] = None
        # =========================================================================================

    async def async_init(self):
        await out_of_date_check("anotherpingcog", self.__version__)

        self.cache = Cache(
            await self.config.custom_settings(),
            await self.config.force_embed(),
            await self.config.footer(),
            self.bot,
        )

        # =========================================================================================
        # TO DISABLE SENTRY FOR THIS COG (EG IF YOU ARE EDITING THIS COG) EITHER DISABLE SENTRY
        # WITH THE `[p]vextelemetry` COMMAND, OR UNCOMMENT THE LINE BELOW, OR REMOVE IT COMPLETELY:
        # return

        while vexcogutils.sentryhelper.ready is False:
            await asyncio.sleep(0.1)

        if vexcogutils.sentryhelper.sentry_enabled is False:
            log.debug("Sentry detected as disabled.")
            return

        log.debug("Sentry detected as enabled.")
        self.sentry_hub = await vexcogutils.sentryhelper.get_sentry_hub(
            "anotherpingcog", self.__version__
        )
        # =========================================================================================

    async def cog_command_error(self, ctx: commands.Context, error: commands.CommandError):
        await self.bot.on_command_error(ctx, error, unhandled_by_cog=True)

        if self.sentry_hub is None:  # sentry disabled
            return

        with self.sentry_hub:
            sentry_sdk.add_breadcrumb(
                category="command", message="Command used was " + ctx.command.qualified_name
            )
            sentry_sdk.capture_exception(error.original)  # type:ignore
            log.debug("Above exception successfully reported to Sentry")

    def cog_unload(self):
        self.sentry_hub.end_session()
        self.sentry_hub.client.close()

        global old_ping
        if old_ping:
            try:
                self.bot.remove_command("ping")
            except Exception:
                pass
            self.bot.add_command(old_ping)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def apcinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(self.qualified_name, self.__version__))

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
            if settings.footer == "default":
                embed.set_footer(text=DEFAULT_FOOTER)
            elif settings.footer != "none":
                embed.set_footer(text=settings.footer)
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
            embed.add_field(name="Message Send", value=f"{m_latency_text}{extra}")
            embed.colour = colour
            await message.edit(embed=embed)
        else:
            data = [
                ["Discord WS", "Message Send"],
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

    @commands.group()
    @commands.is_owner()
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

    @pingset.command(require_var_positional=True)
    async def footer(self, ctx: commands.Context, *, text: str):
        """
        Set a custom footer for the ping embed.

        If `none` is provided as the parameter, there will be no embed footer.

        If `default` is provided as the parameter, the default footer will be used.

        Otherwise, the provided text will be used as the custom footer.
        """
        if text.lower() == "default":
            text = "default"
            await ctx.send(
                f"The default footer text will now be used for `{ctx.clean_prefix}ping`."
            )
        elif text.lower() == "none":
            text = "none"
            await ctx.send(f"There will no longer be a footer for `{ctx.clean_prefix}ping`.")
        else:
            await ctx.send(
                f"The provided footer text will now be used for `{ctx.clean_prefix}ping`."
            )
        await self.config.footer.set(text)
        self.cache.footer = text

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

        **Examples:**
            - `[p]pingset red :emoji: #F04747`
            - `[p]pingset red :emoji: default`
            - `[p]pingset red default #F04747`
            - `[p]pingset red default default`
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
            hex_colour = hex_colour.lstrip("#")
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

        **Examples:**
            - `[p]pingset orange :emoji: #FAA61A`
            - `[p]pingset orange :emoji: default`
            - `[p]pingset orange default #FAA61A`
            - `[p]pingset orange default default`
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
            hex_colour = hex_colour.lstrip("#")
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

        **Examples:**
            - `[p]pingset green :emoji: #43B581`
            - `[p]pingset green :emoji: default`
            - `[p]pingset green default #43B581`
            - `[p]pingset green default default`
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
            hex_colour = hex_colour.lstrip("#")
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
        embed = discord.Embed(
            title="Global settings for the `ping` command.", color=await ctx.embed_color()
        )
        embeds = "**Force embed setting:**\n"
        embeds += (
            "True - will send as an embed, unless the bot doesn't have permission to send them."
            if settings.force_embed
            else "False - `embedset` is how embeds will be determined (defaults to True)."
        )
        embed.add_field(name="Embeds", value=embeds, inline=False)
        footer = "**Embed footer setting:**\n"
        footer += (
            "Default - the default text will be used in the embed footer."
            if settings.footer == "default"
            else "None - there will not be any footer text in the embed."
            if settings.footer == "none"
            else f"Custom - {settings.footer}"
        )
        embed.add_field(name="Footer", value=footer, inline=False)

        # these 3 are alright with the 5/5 rate limit, plus it's owner only.
        # if anyone wants to PR something with image generation, don't as it's wayyyyy to complex
        # for this
        await ctx.send(embed=embed)
        await ctx.send(
            embed=discord.Embed(
                title=f'Emoji for green: {self.cache.green.emoji}',
                description=f"{LEFT_ARROW} Colour for green",
                colour=self.cache.green.colour,
            )
        )

        await ctx.send(
            embed=discord.Embed(
                title=f'Emoji for orange: {self.cache.orange.emoji}',
                description=f"{LEFT_ARROW} Colour for orange",
                colour=self.cache.orange.colour,
            )
        )

        await ctx.send(
            embed=discord.Embed(
                title=f'Emoji for red: {self.cache.red.emoji}',
                description=f"{LEFT_ARROW} Colour for red",
                colour=self.cache.red.colour,
            )
        )


def setup(bot: Red) -> None:
    global old_ping
    old_ping = bot.get_command("ping")
    if old_ping:
        bot.remove_command(old_ping.name)

    apc = AnotherPingCog(bot)
    bot.add_cog(apc)
