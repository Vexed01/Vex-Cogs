from typing import Optional, Union

import discord
from discord import ButtonStyle, Interaction
from discord.partial_emoji import PartialEmoji
from discord.ui import Button
from discord.ui.view import View
from redbot.core.utils.chat_formatting import humanize_list, pagify
from vexcogutils.chat import inline_hum_list

from .api import GitHubAPI


def format_embed(issue_data: dict) -> discord.Embed:
    embed = discord.Embed(
        title=issue_data["state"].upper()
        + ": "
        + issue_data["title"]
        + " #"
        + str(issue_data["number"]),
        url=issue_data["html_url"],
        # TODO: colour and dont shove state in title, title length limit
    )
    embed.set_author(name=issue_data["user"]["login"], icon_url=issue_data["user"]["avatar_url"])
    if issue_data["body"]:
        embed.description = list(pagify(issue_data["body"], page_length=500))[0]
    labels = issue_data.get("labels", [])
    if labels:  # want a lot
        if len(labels) > 15:
            labels = labels[0:13]
            extra = "..."
        else:
            extra = ""
        embed.add_field(name="Labels", value=inline_hum_list([i["name"] for i in labels]) + extra)
    milestone = issue_data.get("milestone")
    if milestone:
        embed.add_field(name="Milestone", value=milestone)
    merge_state = issue_data.get("mergeable_state")
    if merge_state:  # its a PR
        if issue_data["merged"]:
            merge_state = "merged"
        elif merge_state == "clean":
            merge_state = "mergeable"
        embed.add_field(name="State", value=merge_state.capitalize())
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
        disabled: Optional[bool],
    ):
        super().__init__(style=style, label=label, emoji=emoji, row=row, disabled=disabled)
        self.issue_data = issue_data
        self.api = api

    async def regen_viw(self, interaction: Interaction, view: View):
        """Get the latest version and update the view."""
        data = await self.api.get_issue(self.issue_data["number"])
        embed = format_embed(data)
        await interaction.response.edit_message(embed=embed, view=view)


# CHILD 0
class MilestoneButton(GHButton):
    def __init__(self, issue_data: dict, api: GitHubAPI):
        super().__init__(issue_data, api, ButtonStyle.green, "Milestone", None, 1, False)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, GHView)
        await interaction.response.send_message("Not implemented.")


# CHILD 1
class AddLabelsButton(GHButton):
    def __init__(self, issue_data: dict, api: GitHubAPI):
        super().__init__(issue_data, api, ButtonStyle.green, "Add Labels", None, 1, False)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, GHView)
        await interaction.response.send_message("Not implemented.")


# CHILD 2
class RemoveLabelsButton(GHButton):
    def __init__(self, issue_data: dict, api: GitHubAPI):
        super().__init__(issue_data, api, ButtonStyle.red, "Remove Labels", None, 1, False)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, GHView)
        await interaction.response.send_message("Not implemented.")


# CHILD 3
class CloseButton(GHButton):
    def __init__(self, issue_data: dict, api: GitHubAPI, disabled: bool):
        super().__init__(issue_data, api, ButtonStyle.red, "Close", None, 2, disabled)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, GHView)
        await self.api.close(self.issue_data["number"])
        self.disabled = True
        self.view.children[4].disabled = False
        if len(self.view.children) == 6:
            self.view.children[5].disabled = True
        await self.regen_viw(interaction, self.view)


# CHILD 4
class OpenButton(GHButton):
    def __init__(self, issue_data: dict, api: GitHubAPI, disabled: bool):
        super().__init__(issue_data, api, ButtonStyle.green, "Open", None, 2, disabled)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, GHView)
        await self.api.open(self.issue_data["number"])
        self.disabled = True
        self.view.children[3].disabled = False
        if len(self.view.children) == 6:
            self.view.children[5].disabled = False
        await self.regen_viw(interaction, self.view)


# CHILD 5 (PR only)
class MergeButton(GHButton):
    def __init__(self, issue_data: dict, api: GitHubAPI, disabled: bool):
        super().__init__(issue_data, api, ButtonStyle.blurple, "Merge", None, 2, disabled)

    async def callback(self, interaction: Interaction):
        assert isinstance(self.view, GHView)
        # TODO: let them pick commit msg and merge method
        await self.api.merge(self.issue_data["number"], self.issue_data["title"])
        self.disabled = True
        self.view.children[3].disabled = True
        self.view.children[4].disabled = True
        await self.regen_viw(interaction, self.view)


class GHView(discord.ui.View):
    def __init__(
        self, issue_data: dict, api: GitHubAPI, author_id: int, timeout: float = 300.0
    ):  # 5 min
        super().__init__(timeout=timeout)
        self.issue_data = issue_data
        self.author_id = author_id

        self.add_item(MilestoneButton(issue_data, api))
        self.add_item(AddLabelsButton(issue_data, api))
        self.add_item(RemoveLabelsButton(issue_data, api))

        if issue_data.get("merged"):
            openable = False
            closeable = False
            mergeable = False
        else:
            openable = issue_data["state"] == "closed" and not issue_data.get("merged", False)
            closeable = issue_data["state"] == "open"
            mergeable = issue_data.get("mergeable_state") == "clean"

        self.add_item(CloseButton(issue_data, api, not closeable))
        self.add_item(OpenButton(issue_data, api, not openable))

        state = issue_data.get("mergeable_state")
        if state:  # if its a PR
            self.add_item(MergeButton(issue_data, api, not mergeable))

    async def interaction_check(self, interaction: Interaction) -> bool:
        return interaction.user.id == self.author_id


# await ctx.send(embed=embed, view=GHView(...))
