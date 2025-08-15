from expr import EvaluatorError, evaluate
from redbot.core import commands
from redbot.core.bot import Red

from .vexutils import format_help, format_info
from .view import CalcView, preprocess_expression


class Calc(commands.Cog):
    """Calculate simple mathematical expressions."""

    __version__ = "0.0.4"
    __author__ = "@vexingvexed"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    @commands.command(hidden=True)
    async def calcinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    @commands.command()
    async def calc(self, ctx: commands.Context, *, expression: str = None):
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
