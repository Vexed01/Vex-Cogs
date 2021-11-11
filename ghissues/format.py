# most of the issue formatting design is from Kowin's `githubcards` cog, a big thank you goes there
# the code itself has been modified
# the original code was licensed under Mozilla Public License 2.0 from http://mozilla.org/MPL/2.0/
# MPL 2.0 is compatible with this program's overall license, GNU GPL v3

import datetime

import discord
from redbot.core.utils.chat_formatting import inline, pagify

from .vexutils.chat import inline_hum_list


def format_embed(issue_data: dict) -> discord.Embed:
    embed = discord.Embed(
        url=issue_data["html_url"],
    )
    embed.set_author(
        name=issue_data["user"]["login"],
        url=issue_data["user"]["html_url"],
        icon_url=issue_data["user"]["avatar_url"],
    )
    number_suffix = f" #{issue_data['number']}"
    max_len = 256 - len(number_suffix)
    if len(issue_data["title"]) > max_len:
        embed.title = f"{issue_data['title'][:max_len-3]}...{number_suffix}"
    else:
        embed.title = f"{issue_data['title']}{number_suffix}"

    if len(issue_data["body"]) > 300:
        embed.description = (
            next(pagify(issue_data["body"], delims=[" ", "\n"], page_length=300, shorten_by=0))
            + "..."
        )
    else:
        embed.description = issue_data["body"]

    if issue_data.get("merged"):
        embed.colour = 0xA371F7
        state = "Merged"
    elif issue_data.get("draft"):
        embed.colour = 0x8B949E
        state = "Draft"
    elif issue_data["state"] == "open":
        embed.colour = 0x3FB950
        state = "Open"
    elif issue_data["state"] == "closed":
        embed.colour = 0xF85149
        state = "Closed"
    else:
        embed.color = 0x8B949E
        state = "Unknown"

    formatted_datetime = datetime.datetime.fromisoformat(
        issue_data["created_at"].rstrip("Z")
    ).strftime("%d %b %Y, %H:%M")

    if issue_data.get("mergeable_state"):  # is PR:
        repo = issue_data["base"]["repo"]["full_name"].lstrip("https://api.github.com/repos/")
    else:
        repo = issue_data["repository_url"].lstrip("https://api.github.com/repos/")
    # REST API has no way of doing ^ nicely for either issues or PRs :sad:
    embed.set_footer(text=f"{repo} • Created on {formatted_datetime}")
    if issue_data["labels"]:
        if len(issue_data["labels"]) > 10:
            labels = issue_data["labels"][0:8]
            value = f"{', '.join([inline(label) for label in labels])}, ..."
        else:
            value = inline_hum_list([label["name"] for label in issue_data["labels"]])
        embed.add_field(
            name=f"Labels [{len(issue_data['labels'])}]",
            value=value,
        )

    embed.add_field(name="State", value=state)
    if issue_data["milestone"]:
        embed.add_field(name="Milestone", value=inline(issue_data["milestone"]["title"]))
    return embed
