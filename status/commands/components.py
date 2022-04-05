from __future__ import annotations

import discord
from discord import ui


class AddServiceView(ui.View):
    def __init__(self, author: discord.Member, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.author_id = author.id

        self.mode: str | None = None
        self.webhook: bool | None = None
        self.restrict: bool | None = None

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        if interaction.user.id == self.author_id:
            return True

        await interaction.response.send_message(
            "You do not have permission to interact with this."
        )
        return False

    @ui.select(
        placeholder="Mode",
        options=[
            discord.SelectOption(label="Mode: all", value="all"),
            discord.SelectOption(label="Mode: latest", value="latest"),
            discord.SelectOption(label="Mode: edit", value="edit"),
        ],
    )
    async def slt_mode(self, interaction: discord.Interaction, select: ui.Select):
        self.mode = select.values[0]

    @ui.select(
        placeholder="Webhook",
        options=[
            discord.SelectOption(label="Webhook: yes", value="yes"),
            discord.SelectOption(label="Webhook: no", value="no"),
        ],
    )
    async def slt_webhook(self, interaction: discord.Interaction, select: ui.Select):
        self.webhook = select.values[0] == "yes"

    @ui.select(
        placeholder="Restrict",
        options=[
            discord.SelectOption(label="Restrict: yes", value="yes"),
            discord.SelectOption(label="Restrict: no", value="no"),
        ],
    )
    async def slt_restrict(self, interaction: discord.Interaction, select: ui.Select):
        self.restrict = select.values[0] == "yes"

    @ui.button(label="Submit", style=discord.ButtonStyle.primary)
    async def btn_submit(self, interaction: discord.Interaction, button: ui.Button):
        if self.mode is None:
            await interaction.response.send_message("Please select a mode.")
            return
        if self.webhook is None:
            await interaction.response.send_message("Please select a webhook option.")
            return
        if self.restrict is None:
            await interaction.response.send_message("Please select a restrict option.")
            return

        self.stop()
