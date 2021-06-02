import discord
from discord import ButtonStyle, Interaction, ui
from discord.ui import Button
from discord.ui.button import button
from redbot.core.utils.chat_formatting import pagify
from vexcogutils.chat import inline_hum_list

from .api import GitHubAPI


def format_embed(issue_data: dict) -> discord.Embed:
    # thanks Kowlin
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
        return interaction.user.id == self.author_id

    async def regen_viw(self, interaction: Interaction):
        """Get the latest version and update the view."""
        data = await self.api.get_issue(self.issue_data["number"])
        embed = format_embed(data)
        await interaction.response.edit_message(embed=embed, view=self)

    @button(label="Set milestone", style=ButtonStyle.green, row=0)
    async def btn_milestone(self, button: Button, interaction: Interaction):
        await interaction.response.send_message("Not implemented.")

    @button(label="Add labels", style=ButtonStyle.green, row=0)
    async def btn_add_label(self, button: Button, interaction: Interaction):
        await interaction.response.send_message("Not implemented.")

    @button(label="Remove labels", style=ButtonStyle.red, row=0)
    async def btn_remove_label(self, button: Button, interaction: Interaction):
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


# await ctx.send(embed=embed, view=GHView(...))
