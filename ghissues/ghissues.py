import asyncio
from asyncio import TimeoutError
from typing import List, Mapping

import discord
from gidgethub import HTTPException
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.predicates import MessagePredicate
from vexcogutils import format_help, format_info, inline_hum_list

from ghissues.view import GHView, format_embed

from .api import GitHubAPI
from .consts import CROSS, EXCEPTIONS
from .errors import CustomError

# cspell:ignore labelify kowlin's resp


class GHIssues(commands.Cog):
    """
    Create, comment, labelify and close GitHub issues.

    This cog is only for bot owners.
    I made it for managing issues on my cog repo as a small project,
    but it certainly could be used for other situations where you want
    to manage GitHub issues from Discord.

    If you would like a way to search or view issues, I highly recommend
    Kowlin's approved `githubcards` cog (on the repo
    https://github.com/Kowlin/Sentinel)

    At present, this cannot support multiple repos.

    PRs are mostly supported. You can comment on them or close them
    but not merge them or create them.

    Get started with the `ghi howtoken` command to set your GitHub token.
    You don't have to do this if you have already set it for a different
    cog, eg `githubcards`. Then set up with `ghi setrepo`.
    """

    __version__ = "1.0.0"
    __author__ = "Vexed#3211"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(
            self, identifier=418078199982063626, force_registration=True
        )
        self.config.register_global(repo=None)

        self.api = GitHubAPI("", "")

        asyncio.create_task(self.async_init())

    async def async_init(self) -> None:
        token = (await self.bot.get_shared_api_tokens("github")).get("token", "")
        repo = await self.config.repo()

        self.api = GitHubAPI(repo, token)

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """Nothing to delete"""
        return

    async def _handle_error(self, ctx: commands.Context, error: Exception) -> None:
        if isinstance(error, HTTPException):
            if error.status_code == 404:
                await ctx.send("It looks like that isn't a valid issue or PR number.")
            else:
                await ctx.send(f"HTTP error occurred: `{error.status_code}`")

        elif not isinstance(error, CustomError):
            raise error

    @commands.Cog.listener()
    async def on_red_api_tokens_update(self, service_name: str, api_tokens: Mapping[str, str]):
        if service_name != "github":
            return

        self.token = api_tokens.get("api_key", "")  # want it to directly reflect shared thingy

    @commands.command(hidden=True)
    async def ghissuesinfo(self, ctx: commands.Context):
        extras = {"Token": bool(self.token), "Repo": bool(self.repo)}
        main = await format_info(
            self.qualified_name, self.__version__, extras=extras  # type:ignore
        )

        if not (self.token and self.repo):
            extra = (
                f"\nIt is expected these are `{CROSS}` if no commands have been used since "
                "the cog was last loaded."
            )
        else:
            extra = ""

        await ctx.send(f"{main}{extra}")

    @commands.group(aliases=["ghissues"], invoke_without_command=True)
    @commands.is_owner()
    async def ghi(self, ctx: commands.Context, issue: int):
        """
        Command to interact with this cog.

        All commands are owner only.

        To open the interactive issue view, run `[p]ghi <issue_num>`.

        **Examples:**
            - `[p]ghi 11`
            - `[p]ghi howtoken`
            - `[p]ghi create`
        """
        async with ctx.typing():
            assert self.api is not None
            issue_info = await self.api.get_issue(issue)
            embed = format_embed(issue_info)
        await ctx.send(embed=embed, view=GHView(issue_info, self.api, ctx.author.id))

    @ghi.command()
    async def howtoken(self, ctx: commands.Context):
        """Instructions on how to set up a token."""
        p = ctx.clean_prefix
        await ctx.send(
            "Note: if you have already set up a GH API token with your bot (eg for `githubcards`) "
            "then this cog will already work.\n\n"
            "1. Create a new token at <https://github.com/settings/tokens> and tick the `repo` "
            "option at the top.\n"
            "2. Copy the token and, in my DMs, run this command: "
            f"`{p}set api github token PUTYOURTOKENHERE`\n"
            f"3. Set up a repo with `{p}gh setrepo`"
        )

    @ghi.command()
    async def setrepo(self, ctx: commands.Context, slug: str):
        """Set up a repo to use as a slug (`USERNAME/REPO`)."""
        try:
            await self.api.repo_info(slug)
        except HTTPException:
            return await ctx.send(
                "That looks like a invalid slug or a private repo my token doesn't let me view."
            )
        except CustomError:
            return

        self.api.repo = slug
        await self.config.repo.set(slug)
        await ctx.send(f"Set the repo to use as `{slug}`")

    # @ghi.command(aliases=["addlabel"])
    # async def addlabels(self, ctx: commands.Context, issue: int):
    #     """Interactive command to add labels to an issue or PR."""
    #     try:
    #         repo_labels = await GitHubAPI.get_repo_labels()
    #         issue_labels = await GitHubAPI.get_issue_labels(issue)
    #     except EXCEPTIONS as e:
    #         return await self._handle_error(ctx, e)

    #     rl_names = []
    #     for label in repo_labels:
    #         rl_names.append(label["name"])

    #     il_names = []
    #     for label in issue_labels:
    #         il_names.append(label["name"])

    #     avaliable_labels = inline_hum_list([l for l in rl_names if l not in il_names])
    #     used_labels = inline_hum_list(il_names)
    #     await ctx.send(
    #         "You have 30 seconds, please say what label you want to add. Any invalid input will "
    #         "be ignored. This is case sensitive.\n\n"
    #         f"Available labels: {avaliable_labels}\nLabels currently on issue: {used_labels}"
    #     )

    #     def check(msg):
    #         return (
    #             msg.author == ctx.author
    #             and msg.channel == ctx.channel
    #             and (msg.content in rl_names or msg.content.casefold() in ["save", "exit"])
    #         )

    #     to_add: List[str] = []
    #     while True:
    #         try:
    #             answer: discord.Message = await self.bot.wait_for(
    #                 "message", check=check, timeout=30.0
    #             )
    #         except TimeoutError:
    #             return await ctx.send("Timeout. No changes were saved.")
    #         if answer.content.casefold() == "save":
    #             break
    #         elif answer.content.casefold() == "exit":
    #             to_add = []
    #             break
    #         elif answer.content in il_names:
    #             await ctx.send(
    #                 "It looks like that label's already on the issue. Choose another, 30 seconds"
    #             )
    #             continue
    #         to_add.append(answer.content)
    #         il_names.append(answer.content)
    #         rl_names.remove(answer.content)

    #         avaliable_labels = inline_hum_list(
    #             [label for label in rl_names if label not in il_names]
    #         )
    #         used_labels = inline_hum_list(il_names)
    #         await ctx.send(
    #             "Label added. Again, 30 seconds. Say another label name if you want to add more,"
    #             "**`save` to save your changes** or **`exit` to exit without saving.**\n\n"
    #             f"Available labels: {avaliable_labels}\nLabels currently on issue: {used_labels}"
    #         )
    #     if to_add:
    #         try:
    #             await GitHubAPI.add_labels(issue, to_add)
    #             issue_info = await GitHubAPI.get_issue(issue)
    #         except EXCEPTIONS as e:
    #             return await self._handle_error(ctx, e)
    #         await ctx.send(
    #             "Added labels to issue `{}` by `{}`".format(
    #                 issue_info.get("title"), issue_info.get("user", {}).get("login")
    #             )
    #         )
    #     else:
    #         await ctx.send("No changes were saved.")

    # @ghi.command(aliases=["removelabel"])
    # async def removelabels(self, ctx: commands.Context, issue: int):
    #     """Interactive command to remove labels from an issue or PR."""
    #     try:
    #         issue_labels = await GitHubAPI.get_issue_labels(issue)
    #     except EXCEPTIONS as e:
    #         return await self._handle_error(ctx, e)

    #     il_names = []
    #     for label in issue_labels:
    #         il_names.append(label["name"])

    #     used_labels = inline_hum_list(il_names)
    #     await ctx.send(
    #         "You have 30 seconds, please say what label you want to add. Any invalid input will "
    #         "be ignored. This is case sensitive.\n\n"
    #         f"Labels currently on issue: {used_labels}"
    #     )

    #     def check(msg: discord.Message):
    #         return (
    #             msg.author == ctx.author
    #             and msg.channel == ctx.channel
    #             and (msg.content in il_names or msg.content.casefold() == "exit")
    #         )

    #     while True:
    #         try:
    #             answer: discord.Message = await self.bot.wait_for(
    #                 "message", check=check, timeout=30.0
    #             )
    #         except TimeoutError:
    #             return await ctx.send("Timeout.")
    #         if answer.content.casefold() == "exit":
    #             return await ctx.send("Done.")
    #         try:
    #             await GitHubAPI.remove_label(issue, answer.content)
    #         except EXCEPTIONS as e:
    #             return await self._handle_error(ctx, e)

    #         il_names.remove(answer.content)

    #         used_labels = inline_hum_list(il_names)
    #         await ctx.send(
    #             "Label removed. Again, 30 seconds. Say another label name if you want to remove "
    #             f"one, or `exit` to finish.\n\nLabels currently on issue: {used_labels}"
    #         )

    @ghi.command()
    async def open(self, ctx: commands.Context, *, title: str):
        """Open a new issue. Does NOT reopen."""
        try:
            await self._get_token(ctx)
            await self._get_repo(ctx)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)

        await ctx.send(
            "Your next message will be the description of the issue. If you answer exactly "
            "`cancel` I won't make an issue.\n"
            "You've got 5 minutes, remember the 2000 Discord character limit!"
        )
        try:
            answer: discord.Message = await self.bot.wait_for(
                "message", check=MessagePredicate.same_context(ctx), timeout=300.0
            )
        except TimeoutError:
            return await ctx.send("Aborting.")
        if answer.content.casefold() == "cancel":
            return await ctx.send("Aborting.")
        else:
            description = answer.content

        await ctx.send(
            "Do you want to add one or more labels to this issue? (yes or no, 15 seconds)"
        )
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            answer = await self.bot.wait_for("message", check=pred, timeout=15.0)
        except TimeoutError:
            return await ctx.send("Aborting.")

        to_add: List[str] = []
        if pred.result is True:
            repo_labels = await self.api.get_repo_labels()
            rl_names = []
            for label in repo_labels:
                rl_names.append(label["name"])

            avaliable_labels = inline_hum_list(rl_names)
            await ctx.send(
                "You have 30 seconds, please say what label you want to add. Any invalid input "
                "will be ignored. This is case sensitive. Say `exit` to abort creating the issue, "
                f"or **`create` to make the issue**.\n\nAvaliable labels: {avaliable_labels}"
            )

            def check(msg: discord.Message):
                return (
                    msg.author == ctx.author
                    and msg.channel == ctx.channel
                    and (msg.content in rl_names or msg.content.casefold() in ["create", "exit"])
                )

            to_add = []
            while True:
                try:
                    answer = await self.bot.wait_for("message", check=check, timeout=30.0)
                except TimeoutError:
                    await ctx.send("Timeout on this label.")
                    break
                if answer.content.casefold() == "exit":
                    await ctx.send("Exiting. No changes were saved.")
                    return
                if answer.content.casefold() == "create":
                    break
                elif answer.content in to_add:
                    await ctx.send(
                        "It looks like that label's already on the issue. Choose another, 30 "
                        "seconds."
                    )
                    continue
                to_add.append(answer.content)
                rl_names.remove(answer.content)

                avaliable_labels = inline_hum_list(rl_names)
                used_labels = inline_hum_list(to_add)
                await ctx.send(
                    "Label added. Again, 30 seconds. Say another label name if you want to add "
                    "more, `create` to create the issue or `exit` to exit without saving.\n\n"
                    f"Avaliable labels: {avaliable_labels}\nLabels currently on issue: "
                    f"{used_labels}"
                )
        try:
            resp = await self.api.create_issue(title, description, to_add)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)

        await ctx.send(
            "Created issue {}: {}".format(resp.get("number"), "<{}>".format(resp.get("html_url")))
        )
