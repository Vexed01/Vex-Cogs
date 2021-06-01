from typing import Optional, Union

import discord
from discord import ButtonStyle, Interaction
from discord.partial_emoji import PartialEmoji
from discord.ui import Button
from discord.ui.view import View

from .api import GitHubAPI


def format_embed(issue_data: dict) -> discord.Embed:
    embed = discord.Embed(
        title=issue_data["state"].upper()
        + ": "
        + issue_data["title"]
        + " #"
        + str(issue_data["number"]),
        url=issue_data["html_url"],
        # TODO: colour and dont shove state in title
    )
    embed.set_author(name=issue_data["user"]["login"], icon_url=issue_data["user"]["avatar_url"])
    return embed


class GHButton(Button):
    def __init__(
        self,
        issue_data: dict,
        api: GitHubAPI,
        style: ButtonStyle,
        label: Optional[str],
        emoji: Optional[Union[str, PartialEmoji]],
        row: Optional[int],
    ):
        super().__init__(
            style=style,
            label=label,
            emoji=emoji,
            row=row,
        )
        self.issue_data = issue_data
        self.api = api

    async def regen_viw(self, interaction: Interaction, view: View):
        """Get the latest version and update the view."""
        data = await self.api.get_issue(self.issue_data["number"])
        embed = format_embed(data)
        await interaction.response.edit_message(embed=embed, view=view)


class CloseButton(GHButton):
    def __init__(self, *, issue_data: dict, api: GitHubAPI):
        super().__init__(issue_data, api, ButtonStyle.red, "Close", None, 1)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, GHView)
        await self.api.close(self.issue_data["number"])
        self.disabled = True
        await self.regen_viw(interaction, self.view)


class GHView(discord.ui.View):
    def __init__(self, issue_data: dict, api: GitHubAPI, timeout: float = 300.0):  # 5 min
        super().__init__(timeout=timeout)
        self.issue_data = issue_data

        if issue_data["state"] == "open":
            self.add_item(CloseButton(issue_data=issue_data, api=api))
