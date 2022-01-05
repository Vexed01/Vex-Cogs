from typing import TYPE_CHECKING, Dict, List

from discord import ButtonStyle, Interaction, ui
from discord.ui.button import Button, button

from .utils import get_menu_sets, make_label_content

if TYPE_CHECKING:
    from .master import GHView


class BaseLabelView(ui.View):
    def __init__(self, master: "GHView", raw_labels: Dict[str, bool]):
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

        labels = list(get_menu_sets(self.raw_labels))
        for label, on_issue in labels[page]:
            btn = LabelButton(self.master, label, on_issue)
            self.add_item(btn)
            self.current_label_buttons.append(btn)

    async def regen(self, page: int, interaction: Interaction):
        self.remake_buttons(page)
        await interaction.response.edit_message(
            content=make_label_content(page, len(list(get_menu_sets(self.raw_labels)))),
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
        max_pages = len(list(get_menu_sets(self.raw_labels)))
        # pages start from 0
        if self.page + 1 >= max_pages:
            return

        self.page += 1
        await self.regen(self.page, interaction)


class LabelButton(Button):
    def __init__(self, master: "GHView", name: str, on_issue: bool):
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

        view: BaseLabelView = self.view
        view.raw_labels[self.name] = not self.on_issue
        await view.regen(view.page, interaction)
