from typing import List, Optional

from discord import ButtonStyle, Interaction, ui
from discord.message import Message
from discord.ui import Button
from discord.ui.button import button
from redbot.core.bot import Red

from ghissues.api import GitHubAPI
from ghissues.format import format_embed
from ghissues.views.merge import MergeView

from .label import BaseLabelView
from .utils import get_menu_sets, make_label_content


class GHView(ui.View):
    def __init__(
        self, issue_data: dict, api: GitHubAPI, bot: Red, author_id: int, timeout: float = 300.0
    ):  # 5 min
        super().__init__(timeout=timeout)
        self.issue_data = issue_data
        self.api = api
        self.bot = bot
        self.author_id = author_id
        self.is_pr = bool(issue_data.get("mergeable_state"))

        self.add_item(
            Button(
                style=ButtonStyle.link, label="View on GitHub", url=issue_data["html_url"], row=1
            )
        )

        if issue_data.get("merged"):
            openable = False
            closeable = False
            mergeable = False
        else:
            openable = issue_data["state"] == "closed" and not issue_data.get("merged", False)
            closeable = issue_data["state"] == "open"
            mergeable = issue_data.get("mergeable_state") == "clean"

        self.btn_open.disabled = not openable
        self.btn_close.disabled = not closeable

        if not self.is_pr:
            self.remove_item(self.btn_merge)
        else:
            self.btn_merge.disabled = not mergeable

        self.master_msg: Optional[Message] = None

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.author_id:
            return True

        await interaction.response.send_message(
            "You don't have have permission to do this.", ephemeral=True
        )
        return False

    async def regen_viw(self):
        """Get the latest version and update the view."""
        data = await self.api.get_issue(self.issue_data["number"])
        embed = format_embed(data)
        await self.master_msg.edit(embed=embed, view=self)

    @button(label="Manage labels", style=ButtonStyle.grey)
    async def btn_add_label(self, button: Button, interaction: Interaction):
        repo_labels = await self.api.get_repo_labels()
        issue_labels = await self.api.get_issue_labels(self.issue_data["number"])

        rl_names: List[str] = [label["name"] for label in repo_labels]
        il_names: List[str] = [label["name"] for label in issue_labels]

        raw_labels = {label: label in il_names for label in rl_names}

        view = BaseLabelView(self, raw_labels)
        await interaction.response.send_message(
            content=make_label_content(0, len(list(get_menu_sets(raw_labels)))), view=view
        )

    @button(label="Close issue", style=ButtonStyle.red)
    async def btn_close(self, button: Button, interaction: Interaction):
        await self.api.close(self.issue_data["number"])
        button.disabled = True
        self.btn_open.disabled = False
        if self.is_pr:
            self.btn_merge.disabled = True
        await self.regen_viw()

    @button(label="Reopen issue", style=ButtonStyle.green)
    async def btn_open(self, button: Button, interaction: Interaction):
        await self.api.open(self.issue_data["number"])
        button.disabled = True
        self.btn_close.disabled = False
        if self.is_pr:
            self.btn_merge.disabled = False
        await self.regen_viw()

    @button(label="Merge", style=ButtonStyle.blurple)
    async def btn_merge(self, button: Button, interaction: Interaction):
        await interaction.response.send_message(
            "Please choose the merge method. You'll be able to choose a commit message later.",
            view=MergeView(self),
        )

    @button(emoji="❌", row=1, style=ButtonStyle.grey)
    async def btn_del(self, button: Button, interaction: Interaction):
        assert self.master_msg is not None
        await self.master_msg.delete()
