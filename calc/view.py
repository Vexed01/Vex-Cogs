from __future__ import annotations

import asyncio
from typing import NoReturn

import discord
from discord.colour import Colour
from discord.enums import ButtonStyle
from expr import EvaluatorError, evaluate
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box

ZERO_WIDTH = "\u200b"

EQUALS_LABEL = (ZERO_WIDTH + " ") * 16 + "=" + (" " + ZERO_WIDTH) * 15


def preprocess_expression(expr: str) -> str:
    expr = expr.replace(",", "")
    output = ""
    i = 0
    while i < len(expr):
        ch = expr[i]
        if ch.isdigit() or ch == ".":
            num_start = i
            while i < len(expr) and (expr[i].isdigit() or expr[i] == "."):
                i += 1
            number = expr[num_start:i]
            if i < len(expr) and expr[i].lower() in "kmbt":
                suffix = expr[i].lower()
                multiplier = {
                    "k": "*1000",
                    "m": "*1000000",
                    "b": "*1000000000",
                    "t": "*1000000000000",
                }[suffix]
                output += f"({number}{multiplier})"
                i += 1
            else:
                output += number
        else:
            output += ch
            i += 1
    return output


def format_number(value: float | int | str) -> str:
    try:
        num = float(value)
        if num.is_integer():
            return f"{int(num):,}"
        return f"{num:,.10f}".rstrip("0").rstrip(".")
    except (ValueError, TypeError):
        return str(value)


class ClosedView(discord.ui.View):
    @discord.ui.button(label="Calculator closed", style=ButtonStyle.gray, disabled=True)
    async def btn(self, *args, **kwargs):
        pass


class TimedOutView(discord.ui.View):
    @discord.ui.button(label="Calculator timed out", style=ButtonStyle.gray, disabled=True)
    async def btn(self, *args, **kwargs):
        pass


class CalcView(discord.ui.View):
    """An interactive button-based calculator."""

    def __init__(self, bot: Red, author_id: int, timeout=180):
        super().__init__(timeout=timeout)

        self.bot = bot
        self.message: discord.Message | None = None
        self.author_id = author_id

        self.ready = asyncio.Event()

        self.lazy_edit_task = bot.loop.create_task(self.calc_lazy_edit())

        self.new_edits_avaible = asyncio.Event()

        self.input_reset_ready = True

        self.input = "..."
        self.output: str | int | float = "..."

    async def on_timeout(self) -> None:
        await self.ready.wait()
        assert self.message is not None

        self.lazy_edit_task.cancel()

        self.stop()

        await self.message.edit(view=TimedOutView())

    async def calc_lazy_edit(self) -> NoReturn:
        """Lazily edit the calculator screen, accounting for rate limits."""
        await self.ready.wait()
        assert self.message is not None

        while True:
            await self.new_edits_avaible.wait()

            embed = await self.build_embed()
            self.new_edits_avaible.clear()
            await self.message.edit(embed=embed)

            await asyncio.sleep(1)

        # reminder this task is cancelled on timeout and view close via exit button :)

    async def build_embed(self, colour: Colour | None = None) -> discord.Embed:
        """Build the embed for the calculator."""
        if colour is None:
            await self.ready.wait()
            assert self.message is not None

        embed = discord.Embed(
            colour=colour or await self.bot.get_embed_color(self.message.channel),  # type:ignore
            title="Calculator",
        )
        raw_input = self.input
        friendly_input = raw_input.replace("*", "×").replace("/", "÷")
        formatted_output = format_number(self.output)
        embed.description = (
            "**Input:**\n" + box(friendly_input) + "\n**Output:**\n" + box(formatted_output)
        )
        # yes i dont handle over 4k embed limit.... but i dont care!! whos gunna do smth that long?

        return embed

    def maybe_update_output(self) -> bool:
        try:
            sanitized_input = preprocess_expression(self.input)
            full_output = evaluate(sanitized_input)
            self.output = float(round(full_output, 10))
            return True
        except EvaluatorError:
            self.output = "Math Error"
            return False

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        await self.ready.wait()

        if interaction.user is None:
            return False

        valid = interaction.user.id == self.author_id
        if not valid:
            await interaction.response.send_message(
                "You do not have permission to interact with this calculator.", ephemeral=True
            )
        return valid

    @discord.ui.button(label="(", style=discord.ButtonStyle.grey, row=0)
    async def open_bracket(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "("
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label=")", style=discord.ButtonStyle.grey, row=0)
    async def close_bracket(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += ")"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label=ZERO_WIDTH, style=discord.ButtonStyle.grey, row=0)
    async def empty_button(self, interaction: discord.Interaction, item: discord.ui.Item):
        await interaction.response.send_message("You found the useless button!", ephemeral=True)

    @discord.ui.button(label="÷", style=discord.ButtonStyle.blurple, row=0)
    async def divide(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "/"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="⌫", style=discord.ButtonStyle.red, row=0)
    async def backspace(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input = self.input[:-1]
        if len(self.input) == 0:
            self.input = "..."
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="7", style=discord.ButtonStyle.grey, row=1)
    async def seven(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "7"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="8", style=discord.ButtonStyle.grey, row=1)
    async def eight(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "8"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="9", style=discord.ButtonStyle.grey, row=1)
    async def nine(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "9"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="×", style=discord.ButtonStyle.blurple, row=1)
    async def multiply(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "*"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="Clear", style=discord.ButtonStyle.danger, row=1)
    async def clear(self, interaction: discord.Interaction, item: discord.ui.Item):
        self.input = "..."
        self.output = "..."
        self.new_edits_avaible.set()
        self.input_reset_ready = True

        await interaction.response.defer()

    @discord.ui.button(label="4", style=discord.ButtonStyle.grey, row=2)
    async def four(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "4"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="5", style=discord.ButtonStyle.grey, row=2)
    async def five(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "5"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="6", style=discord.ButtonStyle.grey, row=2)
    async def six(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "6"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="-", style=discord.ButtonStyle.blurple, row=2)
    async def minus(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "-"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.danger, row=2)
    async def exit(self, interaction: discord.Interaction, item: discord.ui.Item):
        await interaction.response.defer(thinking=True, ephemeral=True)

        await self.ready.wait()
        assert self.message is not None

        self.lazy_edit_task.cancel()

        self.stop()

        await self.message.edit(view=ClosedView())

        await interaction.followup.send("Calculator closed.", ephemeral=True)

    @discord.ui.button(label="1", style=discord.ButtonStyle.grey, row=3)
    async def one(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "1"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="2", style=discord.ButtonStyle.grey, row=3)
    async def two(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "2"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="3", style=discord.ButtonStyle.grey, row=3)
    async def three(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "3"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="+", style=discord.ButtonStyle.blurple, row=3)
    async def plus(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "+"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label="0", style=discord.ButtonStyle.grey, row=4)
    async def zero(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "0"
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label=".", style=discord.ButtonStyle.grey, row=4)
    async def decimal(self, interaction: discord.Interaction, item: discord.ui.Item):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "."
        self.maybe_update_output()
        self.new_edits_avaible.set()

        await interaction.response.defer()

    @discord.ui.button(label=EQUALS_LABEL, style=discord.ButtonStyle.green, row=4)
    async def equals(self, interaction: discord.Interaction, item: discord.ui.Item):
        if not self.maybe_update_output():
            self.output = "Math Error"
        self.input_reset_ready = True

        self.new_edits_avaible.set()

        await interaction.response.defer()
