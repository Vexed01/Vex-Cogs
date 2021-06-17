from typing import List, Tuple

from discord import ButtonStyle, Interaction, ui
from discord.ui import Button
from discord.ui.button import button

from .api import GitHubAPI
from .format import format_embed


class GHView(ui.View):
    def __init__(
        self, issue_data: dict, api: GitHubAPI, author_id: int, timeout: float = 300.0
    ):  # 5 min
        super().__init__(timeout=timeout)
        self.issue_data = issue_data
        self.api = api
        self.author_id = author_id
        self.is_pr = bool(issue_data.get("mergeable_state"))

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

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.author_id:
            return True

        await interaction.response.send_message(
            "You don't have have permission to do this.", ephemeral=True
        )
        return False

    async def regen_viw(self, interaction: Interaction):
        """Get the latest version and update the view."""
        data = await self.api.get_issue(self.issue_data["number"])
        embed = format_embed(data)
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Set milestone", style=ButtonStyle.green, row=0)
    async def btn_milestone(self, button: Button, interaction: Interaction):
        await interaction.response.send_message(
            content=(
                "Click a label to toggle it. Labels in GREEN are on the issue, labels in GREY "
                "are not on the issue."
            ),
            ephemeral=True,
        )

        repo_labels = await self.api.get_repo_labels()
        issue_labels = await self.api.get_issue_labels(self.issue_data["number"])

        rl_names: List[str] = [label["name"] for label in repo_labels]
        il_names: List[str] = [label["name"] for label in issue_labels]

        raw_labels = list({label: label in il_names for label in rl_names}.items())
        # label_name: on_issue

        def get_labels():
            # partially from a sketchy site
            for i in range(0, len(raw_labels), 25):
                yield raw_labels.items()[i : i + 25]

        labels = await get_labels()
        label_set: List[Tuple[str, bool]]
        for label_set in labels:
            view = ui.View()
            for label, on_issue in label_set:
                btn = LabelButton(self, label, on_issue)
                view.add_item(btn)
            await interaction.response.send_message("_ _", view=view)

    @button(label="Manage labels", style=ButtonStyle.green, row=0)
    async def btn_add_label(self, button: Button, interaction: Interaction):
        await interaction.response.send_message("Not implemented.")

    @button(label="Close", style=ButtonStyle.red, row=1)
    async def btn_close(self, button: Button, interaction: Interaction):
        await self.api.close(self.issue_data["number"])
        button.disabled = True
        self.btn_open.disabled = False
        if self.is_pr:
            self.btn_merge.disabled = True
        await self.regen_viw(interaction)

    @button(label="Open", style=ButtonStyle.green, row=1)
    async def btn_open(self, button: Button, interaction: Interaction):
        await self.api.open(self.issue_data["number"])
        button.disabled = True
        self.btn_close.disabled = False
        if self.is_pr:
            self.btn_merge.disabled = False
        await self.regen_viw(interaction)

    @button(label="Merge", style=ButtonStyle.blurple, row=1)
    async def btn_merge(self, button: Button, interaction: Interaction):
        # TODO: let them pick commit msg and merge method
        await self.api.merge(self.issue_data["number"], self.issue_data["title"])
        button.disabled = True
        self.btn_close.disabled = True
        self.btn_open.disabled = True
        await self.regen_viw(interaction)


class LabelButton(Button):
    def __init__(self, master: GHView, name: str, on_issue: bool):
        super().__init__(label=name, style=ButtonStyle.green if on_issue else ButtonStyle.grey)

        self.master = master
        self.on_issue = on_issue

    async def callback(self, interaction: Interaction):
        # TODO: this
        # - toggle label on issue
        # - switch button colour
        # - regen this message
        # - and regen master:
        #   await self.master.regen_viw(interaction)

        ...
