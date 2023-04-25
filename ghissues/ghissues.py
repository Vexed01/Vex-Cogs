from asyncio import TimeoutError
from typing import Mapping

import discord
from gidgethub import HTTPException
from redbot.core import Config, commands
from redbot.core.bot import Red
from redbot.core.utils.predicates import MessagePredicate

from .api import GitHubAPI
from .consts import EXCEPTIONS
from .errors import CustomError
from .format import format_embed
from .vexutils import format_help, format_info
from .vexutils.button_pred import wait_for_yes_no
from .views.master import GHView

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
    __author__ = "Vexed#0714"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(
            self, identifier=418078199982063626, force_registration=True
        )
        self.config.register_global(repo=None)

        self.api = GitHubAPI("", "")

        self.setup = False

    async def async_init(self) -> None:
        token = (await self.bot.get_shared_api_tokens("github")).get("token", "")
        repo = await self.config.repo()

        if repo and token:
            self.api = GitHubAPI(repo, token)
            self.setup = True

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
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

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
        - `[p]ghi newissue`
        """
        if self.setup is False:
            return await ctx.send(
                "You need to set up a repo and token. Take a look at (`ghi howtoken`)."
            )
        async with ctx.typing():
            issue_info = await self.api.get_issue(issue)
            embed = format_embed(issue_info)
        view = GHView(issue_info, self.api, self.bot, ctx.author.id)
        msg = await ctx.send(embed=embed, view=view)
        view.master_msg = msg

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
            f"3. Set up a repo with `{p}gh setrepo`\n"
            f"4. Reload the cog with `{p}reload ghissues`"
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

    @ghi.command()
    async def newissue(self, ctx: commands.Context, *, title: str):
        """Open a new issue. If you want to reopen, then use the normal interactive view."""
        if self.setup is False:
            return await ctx.send(
                "You need to set up a repo (`ghi setrepo`) and token (`ghi howtoken`)."
            )
        await ctx.send(
            "Your next message will be the description of the issue. If you answer exactly "
            "`cancel` I'll cancel. You will have another opportunity to cancel later on.\n"
            "You've got 5 minutes."
        )
        try:
            answer: discord.Message = await self.bot.wait_for(
                "message", check=MessagePredicate.same_context(ctx), timeout=300.0
            )
        except TimeoutError:
            return await ctx.send("Timeout. Aborting.")
        if answer.content.casefold() == "cancel":
            return await ctx.send("Aborting.")
        else:
            description = answer.content

        msg = "Are you happy with your issue? You'll be able to add labels once I've created it."
        try:
            result = await wait_for_yes_no(ctx, msg)
        except TimeoutError:
            return await ctx.send("Timeout. Aborting.")

        if result is False:
            return await ctx.send("Aborting.")

        async with ctx.typing():
            try:
                issue_info = await self.api.create_issue(title, description)
            except EXCEPTIONS as e:
                return await self._handle_error(ctx, e)

        embed = format_embed(issue_info)
        view = GHView(issue_info, self.api, self.bot, ctx.author.id)
        msg = await ctx.send("Issue created:", embed=embed, view=view)
        view.master_msg = msg
