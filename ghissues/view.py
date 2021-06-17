from typing import Dict, Generator, List, Optional, Tuple

from discord import ButtonStyle, Interaction, ui
from discord.message import Message
from discord.ui import Button
from discord.ui.button import button

from .api import GitHubAPI
from .format import format_embed


def make_label_content(page: int = 0, total_pages: int = 0):
    base = (
        "Click a label to toggle it. Labels in GREEN are on the issue, labels in GREY "
        "are not on the issue."
    )
    page_info = (
        "\nAs you've got lots of labels, click the bottons at the bottom to change "
        f"pages.\n\nPage {page + 1} of {total_pages}"
        if total_pages > 1
        else ""
    )

    return base + page_info


def get_label_sets(raw_labels: Dict[str, bool]) -> Generator[List[Tuple[str, bool]], None, None]:
    sorted_labels = {k: v for k, v in sorted(raw_labels.items(), key=lambda item: not item[1])}
    labels = list(sorted_labels.items())
    # partially from a sketchy site
    for i in range(0, len(labels), 20):
        yield labels[i : i + 20]


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
        assert self.master_id is not None, self.inter_channel is not None
        await self.master_msg.edit(embed=embed, view=self)

    @button(label="Set milestone", style=ButtonStyle.grey, row=0)
    async def btn_milestone(self, button: Button, interaction: Interaction):
        self.master_id = interaction.id
        self.inter_channel = interaction.channel
        await interaction.response.send_message("Not implemented.")

    @button(label="Manage labels", style=ButtonStyle.grey, row=0)
    async def btn_add_label(self, button: Button, interaction: Interaction):
        self.master_id = interaction.id
        self.inter_channel = interaction.channel
        repo_labels = await self.api.get_repo_labels()
        issue_labels = await self.api.get_issue_labels(self.issue_data["number"])

        rl_names: List[str] = [label["name"] for label in repo_labels]
        il_names: List[str] = [label["name"] for label in issue_labels]

        raw_labels = {label: label in il_names for label in rl_names}

        view = BaseLabelView(self, raw_labels)
        await interaction.response.send_message(
            content=make_label_content(0, len(list(get_label_sets(raw_labels)))), view=view
        )

    @button(label="Close", style=ButtonStyle.red, row=1)
    async def btn_close(self, button: Button, interaction: Interaction):
        self.master_id = interaction.id
        self.inter_channel = interaction.channel
        await self.api.close(self.issue_data["number"])
        button.disabled = True
        self.btn_open.disabled = False
        if self.is_pr:
            self.btn_merge.disabled = True
        await self.regen_viw()

    @button(label="Open", style=ButtonStyle.green, row=1)
    async def btn_open(self, button: Button, interaction: Interaction):
        self.master_id = interaction.id
        self.inter_channel = interaction.channel
        await self.api.open(self.issue_data["number"])
        button.disabled = True
        self.btn_close.disabled = False
        if self.is_pr:
            self.btn_merge.disabled = False
        await self.regen_viw()

    @button(label="Merge", style=ButtonStyle.blurple, row=1)
    async def btn_merge(self, button: Button, interaction: Interaction):
        self.master_id = interaction.id
        # TODO: let them pick commit msg and merge method
        await self.api.merge(self.issue_data["number"], self.issue_data["title"])
        button.disabled = True
        self.btn_close.disabled = True
        self.btn_open.disabled = True
        await self.regen_viw()


class BaseLabelView(ui.View):
    def __init__(self, master: GHView, raw_labels: Dict[str, bool]):
        super().__init__()
        self.master = master
        self.page = 0
        self.raw_labels = raw_labels

        self.current_label_buttons: List[LabelButton] = []

        self.remake_buttons(0)

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user.id == self.master.author_id:
            return True

        await interaction.response.send_message(
            "You don't have have permission to do this.", ephemeral=True
        )
        return False

    def remake_buttons(self, page: int):
        for btn in self.current_label_buttons:
            self.remove_item(btn)
        self.current_label_buttons = []

        labels = list(get_label_sets(self.raw_labels))
        for label, on_issue in labels[page]:
            btn = LabelButton(self.master, label, on_issue)
            self.add_item(btn)
            self.current_label_buttons.append(btn)

    async def regen(self, page: int, interaction: Interaction):
        self.remake_buttons(page)
        await interaction.response.edit_message(
            content=make_label_content(page, len(list(get_label_sets(self.raw_labels)))),
            view=self,
        )

    @button(emoji="◀", style=ButtonStyle.blurple, row=4)
    async def page_left(self, button: Button, interaction: Interaction):
        # pages start from 0
        if self.page == 0:
            return

        self.page -= 1
        await self.regen(self.page, interaction)

    @button(emoji="▶", style=ButtonStyle.blurple, row=4)
    async def page_right(self, button: Button, interaction: Interaction):
        max_pages = len(list(get_label_sets(self.raw_labels)))
        # pages start from 0
        if self.page + 1 >= max_pages:
            return

        self.page += 1
        await self.regen(self.page, interaction)


class LabelButton(Button):
    def __init__(self, master: GHView, name: str, on_issue: bool):
        super().__init__(label=name, style=ButtonStyle.green if on_issue else ButtonStyle.grey)
        self.master = master
        self.name = name
        self.on_issue = on_issue

    async def callback(self, interaction: Interaction):
        # dont need to worry about fixing this buttons on_issue/colour, full regen happens
        if self.on_issue:
            await self.master.api.remove_label(self.master.issue_data["number"], self.name)
        else:
            await self.master.api.add_labels(self.master.issue_data["number"], [self.name])

        await self.master.regen_viw()

        assert isinstance(self.view, BaseLabelView)

        view: BaseLabelView = self.view
        view.raw_labels[self.name] = not self.on_issue
        await view.regen(view.page, interaction)
