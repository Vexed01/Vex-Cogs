from __future__ import annotations

import datetime

import discord
from dateutil import parser
from redbot.core import Config
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import box, warning

from ..consts import MAX_BDAY_MSG_LEN
from ..utils import format_bday_message


class SetupView(discord.ui.View):
    def __init__(self, author: discord.Member, bot: Red, config: Config):
        super().__init__()

        self.author = author

        self.bot = bot
        self.config = config

    @discord.ui.button(label="Start setup", style=discord.ButtonStyle.blurple)
    async def btn_start(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_modal(SetupModal(self.bot, self.config))

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user != self.author:
            await interaction.response.send_message("You are not authorized to use this button.")
            return False
        else:
            return True


class SetupModal(discord.ui.Modal):
    message_w_year = discord.ui.TextInput(
        label="Birthday message with a new age",
        max_length=MAX_BDAY_MSG_LEN,
        style=discord.TextStyle.long,
        placeholder=(
            "You can use {mention}, {name} and {new_age}\nExample:\n{mention}"
            " is now {new_age} years old!"
        ),
    )

    message_wo_year = discord.ui.TextInput(
        label="Birthday message without an age",
        max_length=MAX_BDAY_MSG_LEN,
        style=discord.TextStyle.long,
        placeholder=(
            "You can use {mention} and {name}\nExample:\n{mention}'s birthday"
            " is today! Happy Birthday!"
        ),
    )

    time = discord.ui.TextInput(
        label="Time of day to send messages in UTC",
        style=discord.TextStyle.short,
        placeholder='For example, "12AM" or "7:00" ',
    )

    def __init__(self, bot: Red, config: Config):
        super().__init__(title="Birthday setup")

        self.bot = bot
        self.config = config

    async def on_submit(self, interaction: discord.Interaction) -> None:
        def get_reminder() -> str:
            return (
                "Nothing's been set, try again.\n\nHere are your messages so you don't have to"
                " type them again.\n\nWith age:\n"
                + box(self.message_w_year.value or "Not set")
                + "\nWithout age:\n"
                + box(self.message_wo_year.value or "Not set")
            )

        try:
            time = parser.parse(self.time.value)
        except parser.ParserError:
            await interaction.response.send_message(
                warning(
                    "Invalid time format. Please use the format 'HH:MM' or 'HHAM' or 'HHPM'.\n\n"
                )
                + get_reminder(),
                ephemeral=True,
            )
            return

        try:
            format_bday_message(self.message_w_year.value, interaction.user, 1)
        except KeyError as e:
            await interaction.response.send_message(
                warning(
                    "You birthday message **with year** can only include `{mention}`, `{name}`"
                    " and `{new_age}`. You can't have anything else in `{}`. You did"
                    f" `{{{e.args[0]}}}` which is invalid.\n\n{get_reminder()}"
                ),
                ephemeral=True,
            )
            return

        try:
            format_bday_message(self.message_wo_year.value, interaction.user)
        except KeyError as e:
            await interaction.response.send_message(
                warning(
                    "You birthday message **without year** can only include `{mention}` and"
                    " `{name}`. You can't have anything else in `{}`. You did"
                    f" `{{{e.args[0]}}}` which is invalid.\n\n{get_reminder()}"
                ),
                ephemeral=True,
            )
            return

        time = time.replace(tzinfo=datetime.timezone.utc, year=1, month=1, day=1)

        midnight = datetime.datetime.now(tz=datetime.timezone.utc).replace(
            year=1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )

        time_utc_s = int((time - midnight).total_seconds())

        async with self.config.guild(interaction.guild).all() as conf:
            conf["time_utc_s"] = time_utc_s
            conf["message_w_year"] = self.message_w_year
            conf["message_wo_year"] = self.message_wo_year
            conf["setup_state"] = 3

        await interaction.response.send_message(
            "All set, but you're not quite ready yet. Just set up the channel and role with `bdset"
            " role` and `bdset channel` then birthdays will be sent and assigned. You can check"
            " with `bdset settings`"
        )
