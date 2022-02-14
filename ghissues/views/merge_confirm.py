from typing import TYPE_CHECKING, Optional

from discord import Interaction
from discord.enums import ButtonStyle
from discord.ui import View
from discord.ui.button import Button, button

from ..vexutils import get_vex_logger

if TYPE_CHECKING:
    from .master import GHView

log = get_vex_logger(__name__)


class MergeConfirm(View):
    def __init__(
        self, master: "GHView", commit_title: str, commit_message: Optional[str], merge_method: str
    ):
        super().__init__()
        self.master = master

        self.commit_message = commit_message
        self.commit_title = commit_title
        self.merge_method = merge_method

    async def interaction_check(self, interaction: Interaction) -> bool:
        if interaction.user is None:
            return False

        if interaction.user.id == self.master.author_id:
            return True

        await interaction.response.send_message(
            "You don't have have permission to do this.", ephemeral=True
        )
        return False

    @button(label="Confirm merge", style=ButtonStyle.green)
    async def btn_confirm(self, button: Button, interaction: Interaction):
        self.stop()
        try:
            await self.master.api.merge(
                self.master.issue_data["number"],
                self.commit_title,
                self.commit_message,
                self.merge_method,
            )
        except Exception as e:  # lazy
            log.warning("Unable to merge PR. See the logs for more info.", exc_info=e)
        else:
            self.master.btn_merge.disabled = True
            self.master.btn_close.disabled = True
            self.master.btn_open.disabled = True
            await self.master.regen_viw()
            await interaction.response.send_message("Pull request merged.")

    @button(label="Cancel merge", style=ButtonStyle.red)
    async def btn_cancel(self, button: Button, interaction: Interaction):
        self.stop()
        await interaction.response.send_message("Merge cancelled.")
