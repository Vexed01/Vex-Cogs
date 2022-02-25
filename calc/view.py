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
            await asyncio.sleep(0.7)
            embed = await self.build_embed()
            self.new_edits_avaible.clear()
            await self.message.edit(embed=embed)
            await asyncio.sleep(0.8)  # hopefully this is enough... 1.5 wait in total

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
        embed.description = (
            "**Input:**\n" + box(friendly_input) + "\n**Output:**\n" + box(str(self.output))
        )
        # yes i dont handle over 4k embed limit.... but i dont care!! whos gunna do smth that long?

        return embed

    def maybe_update_output(self) -> bool:
        try:
            full_output = evaluate(self.input)
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
    async def open_bracket(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "("
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label=")", style=discord.ButtonStyle.grey, row=0)
    async def close_bracket(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += ")"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label=ZERO_WIDTH, style=discord.ButtonStyle.grey, row=0)
    async def empty_button(self, item: discord.ui.Item, interaction: discord.Interaction):
        await interaction.response.send_message("You found the useless button!", ephemeral=True)

    @discord.ui.button(label="÷", style=discord.ButtonStyle.blurple, row=0)
    async def divide(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "/"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="⌫", style=discord.ButtonStyle.red, row=0)
    async def backspace(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input = self.input[:-1]
        if len(self.input) == 0:
            self.input = "..."
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="7", style=discord.ButtonStyle.grey, row=1)
    async def seven(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "7"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="8", style=discord.ButtonStyle.grey, row=1)
    async def eight(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "8"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="9", style=discord.ButtonStyle.grey, row=1)
    async def nine(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "9"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="×", style=discord.ButtonStyle.blurple, row=1)
    async def multiply(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "*"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="Clear", style=discord.ButtonStyle.danger, row=1)
    async def clear(self, item: discord.ui.Item, interaction: discord.Interaction):
        self.input = "..."
        self.output = "..."
        self.new_edits_avaible.set()
        self.input_reset_ready = True

    @discord.ui.button(label="4", style=discord.ButtonStyle.grey, row=2)
    async def four(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "4"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="5", style=discord.ButtonStyle.grey, row=2)
    async def five(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "5"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="6", style=discord.ButtonStyle.grey, row=2)
    async def six(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "6"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="-", style=discord.ButtonStyle.blurple, row=2)
    async def minus(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "-"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="Exit", style=discord.ButtonStyle.danger, row=2)
    async def exit(self, item: discord.ui.Item, interaction: discord.Interaction):
        await self.ready.wait()
        assert self.message is not None

        self.lazy_edit_task.cancel()

        self.stop()

        await self.message.edit(view=ClosedView())

    @discord.ui.button(label="1", style=discord.ButtonStyle.grey, row=3)
    async def one(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "1"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="2", style=discord.ButtonStyle.grey, row=3)
    async def two(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "2"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="3", style=discord.ButtonStyle.grey, row=3)
    async def three(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "3"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="+", style=discord.ButtonStyle.blurple, row=3)
    async def plus(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "+"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label="0", style=discord.ButtonStyle.grey, row=4)
    async def zero(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "0"
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label=".", style=discord.ButtonStyle.grey, row=4)
    async def decimal(self, item: discord.ui.Item, interaction: discord.Interaction):
        if self.input_reset_ready:
            self.input = ""
            self.input_reset_ready = False
        self.input += "."
        self.maybe_update_output()
        self.new_edits_avaible.set()

    @discord.ui.button(label=EQUALS_LABEL, style=discord.ButtonStyle.green, row=4)
    async def equals(self, item: discord.ui.Item, interaction: discord.Interaction):
        if not self.maybe_update_output():
            self.output = "Math Error"
        self.input_reset_ready = True

        self.new_edits_avaible.set()
