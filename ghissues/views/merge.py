import asyncio
from typing import TYPE_CHECKING, Optional

from discord import Interaction
from discord.channel import DMChannel
from discord.message import Message
from discord.ui import View
from discord.ui.button import Button, ButtonStyle, button
from redbot.core.utils.chat_formatting import box

from ghissues.views.merge_confirm import MergeConfirm

if TYPE_CHECKING:
    from .master import GHView


class MergeView(View):
    def __init__(self, master: "GHView"):
        super().__init__()
        self.master = master

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.master.author_id:
            return True

        await interaction.response.send_message(
            "You don't have have permission to do this.", ephemeral=True
        )
        return False

    async def get_commit_and_confirm(self, merge_method: str):
        assert self.master.master_msg is not None
        channel = self.master.master_msg.channel

        await channel.send(
            "Please choose your commit message. You'll be able to confirm or cancel the merge "
            "once you've sent a message. There's a timeout of 60 seconds."
        )

        def check(m: Message):
            if isinstance(channel, DMChannel):  # could be DM
                return m.author.id == self.master.author_id and m.guild is None
            return m.author.id == self.master.author_id and m.channel.id == channel.id

        try:
            commit: str = (
                await self.master.bot.wait_for("message", check=check, timeout=60)
            ).content
        except asyncio.TimeoutError:
            await channel.send("Timeout. Please try again.")

        split_commit_msg = commit.split("\n", 1)

        commit_title = split_commit_msg[0]
        if len(split_commit_msg) == 1:
            commit_message: Optional[str] = None
        else:
            commit_message = split_commit_msg[1]

        if commit_message:
            commit = box(commit_title) + box(commit_message)
        else:
            commit = box(commit_title)

        await channel.send(
            f"Please confirm the merge with method **{merge_method}** and commit: {commit}",
            view=MergeConfirm(self.master, commit_title, commit_message, merge_method),
        )

    @button(label="Merge")
    async def btn_merge(self, button: Button, interaction: Interaction):
        button.style = ButtonStyle.green
        await interaction.response.edit_message(view=self)
        self.stop()
        await self.get_commit_and_confirm("merge")

    @button(label="Squash")
    async def btn_squash(self, button: Button, interaction: Interaction):
        button.style = ButtonStyle.green
        await interaction.response.edit_message(view=self)
        self.stop()
        await self.get_commit_and_confirm("squash")

    @button(label="Rebase")
    async def btn_rebase(self, button: Button, interaction: Interaction):
        button.style = ButtonStyle.green
        await interaction.response.edit_message(view=self)
        self.stop()
        await self.get_commit_and_confirm("rebase")
