import re
from typing import Optional

import discord
from expr import EvaluatorError, evaluate
from redbot.core import Config, commands
from redbot.core.bot import Red
import decimal

from .vexutils import format_help, format_info, get_vex_logger
from .view import CalcView, preprocess_expression


log = get_vex_logger(__name__)


class Calc(commands.Cog):
    """Calculate simple mathematical expressions.

    Use the `calc` command to open an interactive calculator using buttons.

    You can also enable automatic calculation detection with the `calcset autocal` command.
    When enabled, the bot will react with ➕ to messages containing valid calculations."""

    __version__ = "0.1.0"
    __author__ = "@vexingvexed"
    __contributors__ = ["@evanroby"]

    def __init__(self, bot: Red) -> None:
        self.bot = bot
        self.config = Config.get_conf(self, identifier=65465447941649894594798)
        default_guild = {"auto_calc": False}
        self.config.register_guild(**default_guild)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def calcinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    def is_valid_calculation(self, text: str) -> bool:
        text = text.strip()
        if len(text) < 3 or len(text) > 200:
            return False

        math_pattern = r"^[0-9+\-*/().eE\s,kmbtKMBT]+$"

        if not re.match(math_pattern, text):
            return False

        if not re.search(r"[+\-*/]", text):
            return False

        try:
            preprocessed = preprocess_expression(text)
            result = evaluate(preprocessed)
            return isinstance(result, (int, float, decimal.Decimal)) and not (
                isinstance(result, bool)
            )
        except Exception:
            return False

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot or not message.guild:
            return

        if not await self.config.guild(message.guild).auto_calc():
            return

        prefixes = await self.bot.get_valid_prefixes(message.guild)
        if any(message.content.startswith(p) for p in prefixes):
            return

        if self.is_valid_calculation(message.content):
            try:
                await message.add_reaction("➕")
            except discord.HTTPException as e:
                log.warning(
                    f"Failed to add reaction to message {message.id} in guild {message.guild.id}: {e}"
                )

    @commands.Cog.listener()
    async def on_reaction_add(self, reaction: discord.Reaction, user: discord.User) -> None:
        if user.bot:
            return

        if str(reaction.emoji) != "➕" or user != reaction.message.author:
            return

        if (
            not reaction.message.guild
            or not await self.config.guild(reaction.message.guild).auto_calc()
        ):
            return

        bot_reacted = False
        async for reaction_user in reaction.users():
            if reaction_user == self.bot.user:
                bot_reacted = True
                break

        if not bot_reacted:
            return

        if not self.is_valid_calculation(reaction.message.content):
            return

        view = CalcView(self.bot, user.id)

        try:
            preprocessed = preprocess_expression(reaction.message.content)
            result = evaluate(preprocessed)
            view.input = reaction.message.content
            view.output = str(result)
        except EvaluatorError:
            view.input = reaction.message.content
            view.output = "Math Error"

        try:
            channel = reaction.message.channel
            embed_color = discord.Color.blurple()

            embed = await view.build_embed(embed_color)
            message = await channel.send(embed=embed, view=view, reference=reaction.message)
            view.message = message
            view.ready.set()
        except discord.HTTPException:
            pass

    @commands.group()
    async def calcset(self, ctx: commands.Context):
        """Calculator settings."""
        pass

    @calcset.command()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    async def autocal(self, ctx: commands.Context, enabled: Optional[bool] = None):
        """
        Toggle automatic calculation detection.

        When enabled, the bot will react with ➕ to messages containing valid calculations.
        If the message author reacts with ➕ too, the bot will send the calculation result.
        """
        assert ctx.guild is not None

        if enabled is None:
            current = await self.config.guild(ctx.guild).auto_calc()
            await ctx.send(
                f"Automatic calculation detection is currently **{'enabled' if current else 'disabled'}**."
            )
            return

        await self.config.guild(ctx.guild).auto_calc.set(enabled)
        status = "enabled" if enabled else "disabled"
        await ctx.send(f"Automatic calculation detection has been **{status}**.")

    @commands.command()
    async def calc(self, ctx: commands.Context, *, expression: Optional[str] = None):
        """
        Start an interactive calculator using buttons.

        If an expression is given, it will be prefilled and calculated.
        """
        view = CalcView(self.bot, ctx.author.id)

        if expression:
            try:
                preprocessed = preprocess_expression(expression)
                result = evaluate(preprocessed)
                view.input = expression
                view.output = str(result)
            except EvaluatorError:
                view.input = expression
                view.output = "Math Error"

        embed = await view.build_embed(await ctx.embed_colour())
        message = await ctx.send(embed=embed, view=view)
        view.message = message
        view.ready.set()
