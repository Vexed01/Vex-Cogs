from asyncio import TimeoutError

from gidgethub import HTTPException
from redbot.core import Config, checks, commands
from redbot.core.bot import Red
from redbot.core.utils.chat_formatting import humanize_list, inline
from redbot.core.utils.predicates import MessagePredicate

from .api import GitHubAPI
from .errors import CustomError

GET_ISSUE = "get_issue"
GET_REPO_LABELS = "get_repo_labels"
GET_ISSUE_LABELS = "get_issue_labels"

ADD_LABEL = "add_label"
REMOVE_LABEL = "remove_label"

CREATE_ISSUE = "create_issue"
COMMENT = "comment"
CLOSE = "close"
CHECK_REAL = "check_real"

EXCEPTIONS = (HTTPException, CustomError)


class GitHub(commands.Cog):
    """
    Create, comment, labelify and close GitHub issues.

    This cog is only for bot owners.
    I made it for managing issues on my cog repo as a small project,
    but it certainly could be used for other situations where you want
    to manage GitHub issues from Discord.

    If you would like a way to search or view issues, I highly reccomend
    Kowlin's approved `githubcards` cog (on the repo
    https://github.com/Kowlin/Sentinel)

    At present, this cannot support multiple repos.

    PRs are mostly supported. You can comment on them or close them
    but not merge them or create them.

    Get started with the `gh howtoken` command to set your GitHub token.
    You don't have to do this if you have already set it for a different
    cog, eg `ghcards`. Then set up with `gh setrepo`.
    """

    __version__ = "1.0.0"
    __author__ = "Vexed#3211"

    def format_help_for_context(self, ctx: commands.Context):
        """Thanks Sinbad."""
        docs = (
            "This cog has docs! Check them out at\nhttps://vex-cogs.readthedocs.io/en/latest/cogs/github.html"
        )
        pre_processed = super().format_help_for_context(ctx)
        return f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: **`{self.__version__}`**\n{docs}"
        # adding docs link here so doesn't show up in auto generated docs

    def __init__(self, bot: Red):
        self.bot = bot

        self.config = Config.get_conf(self, identifier=418078199982063626, force_registration=True)
        self.config.register_global(repo=None)

    async def red_delete_data_for_user(self, **kwargs):
        """Nothing to delete"""
        return

    async def _handle_error(self, ctx: commands.Context, error: Exception):
        if isinstance(error, HTTPException):
            if error.status_code == 404:
                await ctx.send("It looks like that isn't a valid issue or PR number.")
            else:
                await ctx.send(f"HTTP error occured: `{error.status_code}`")

        elif not isinstance(error, CustomError):
            raise error

    def _inline_list(self, list: list):
        inline_list = []
        for i in list:
            inline_list.append(inline(i))
        return humanize_list(inline_list)

    async def _get_repo(self, ctx: commands.Context):
        """Get the repo. Return immediately on CustomError."""
        repo = await self.config.repo()
        if not repo:
            await ctx.send("The bot owner must decide what repo to use (`gh setrepo`).")
            raise CustomError
        return repo

    async def _get_token(self, ctx: commands.Context):
        """Get the token. Return immediately on CustomError."""
        token = (await self.bot.get_shared_api_tokens("github")).get("token")
        if not token:
            await ctx.send("The bot owner must set the token (`gh howtoken`).")
            raise CustomError
        return token

    @commands.group(aliases=["github"])
    @checks.is_owner()
    async def gh(self, ctx):
        """
        Base command for interacting with this cog.

        All commands are owner only.
        """

    @gh.command()
    async def howtoken(self, ctx: commands.Context):
        """Instructions on how to set up a token."""
        p = ctx.clean_prefix
        await ctx.send(
            "Note: if you have already set up a GH API token with your bot (eg for `ghcards`) then this cog will "
            "already work.\n\n"
            "1. Create a new token at <https://github.com/settings/tokens> and tick the `repo` option at the top.\n"
            "2. Copy the token and, in my DMs, run this command: "
            f"`{p}set api github token PUTYOURTOKENHERE`\n"
            f"3. Set up a repo with `{p}gh setrepo`"
        )

    @gh.command()
    async def setrepo(self, ctx: commands.Context, slug: str):
        """Set up a repo to use as a slug (`USERNAME/REPO`)."""
        try:
            await GitHubAPI.repo_info(await self._get_token(ctx), slug)
        except HTTPException:
            return await ctx.send(
                "That looks like a invalid slug or a private repo my token doesn't let me view."
            )
        except CustomError:
            return
        await self.config.repo.set(slug)
        await ctx.send(f"Set the repo to use as `{slug}`")

    @gh.command()
    async def comment(self, ctx: commands.Context, issue: int, *, text: str):
        """Comment on an issue or PR."""
        try:
            repo = await self._get_repo(ctx)
            token = await self._get_token(ctx)
            await GitHubAPI.comment(token, repo, issue, text)
            issue_info = await GitHubAPI.get_issue(token, repo, issue)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)

        await ctx.send(
            "Added comment to issue `{}` by `{}`".format(
                issue_info.get("title"), issue_info.get("user", {}).get("login")
            )
        )

    @gh.command()
    async def close(self, ctx: commands.Context, issue: int):
        """Close an issue or PR."""
        try:
            repo = await self._get_repo(ctx)
            token = await self._get_token(ctx)
            await GitHubAPI.close(token, repo, issue)
            issue_info = await GitHubAPI.get_issue(token, repo, issue)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)
        await ctx.send(
            "Closed `{}` by `{}`".format(issue_info.get("title"), issue_info.get("user", {}).get("login"))
        )

    @gh.command()
    async def commentclose(self, ctx: commands.Context, issue: int, *, text: str):
        """Comment on, then close, an issue or PR."""
        try:
            repo = await self._get_repo(ctx)
            token = await self._get_token(ctx)
            await GitHubAPI.comment(token, repo, issue, text)
            await GitHubAPI.close(token, repo, issue)
            issue_info = await GitHubAPI.get_issue(token, repo, issue)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)
        await ctx.send(
            "Commented on and closed issue `{}` by `{}`".format(
                issue_info.get("title"), issue_info.get("user", {}).get("login")
            )
        )

    @gh.command(aliases=["addlabel"])
    async def addlabels(self, ctx: commands.Context, issue: int):
        """Interactive command to add labels to an issue or PR."""
        try:
            token = await self._get_token(ctx)
            repo = await self._get_repo(ctx)
            repo_labels = await GitHubAPI.get_repo_labels(token, repo)
            issue_labels = await GitHubAPI.get_issue_labels(token, repo, issue)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)

        rl_names = []
        for label in repo_labels:
            rl_names.append(label["name"])

        il_names = []
        for label in issue_labels:
            il_names.append(label["name"])

        avalible_labels = self._inline_list([l for l in rl_names if l not in il_names])
        used_labels = self._inline_list(il_names)
        await ctx.send(
            "You have 30 seconds, please say what label you want to add. Any invalid input will be ignored."
            " This is case sensitive.\n\n"
            f"Avalible labels: {avalible_labels}\nLabels currently on issue: {used_labels}"
        )

        def check(msg):
            return (
                msg.author == ctx.author
                and msg.channel == ctx.channel
                and (msg.content in rl_names or msg.content.casefold() in ["save", "exit"])
            )

        to_add = []
        while True:
            try:
                answer = await self.bot.wait_for("message", check=check, timeout=30.0)
            except TimeoutError:
                return await ctx.send("Timeout. No changes were saved.")
            if answer.content.casefold() == "save":
                break
            elif answer.content.casefold() == "exit":
                to_add = []
                break
            elif answer.content in il_names:
                await ctx.send("It looks like that label's already on the issue. Choose another, 30 seconds.")
                continue
            to_add.append(answer.content)
            il_names.append(answer.content)
            rl_names.remove(answer.content)

            avalible_labels = self._inline_list([l for l in rl_names if l not in il_names])
            used_labels = self._inline_list(il_names)
            await ctx.send(
                "Label added. Again, 30 seconds. Say another label name if you want to add more, **`save` to save your "
                "changes** or **`exit` to exit without saving.**\n\n"
                f"Avalible labels: {avalible_labels}\nLabels currently on issue: {used_labels}"
            )
        if to_add:
            try:
                await GitHubAPI.add_labels(token, repo, issue, to_add)
                issue_info = await GitHubAPI.get_issue(token, repo, issue)
            except EXCEPTIONS as e:
                return await self._handle_error(ctx, e)
            await ctx.send(
                "Added labels to issue `{}` by `{}`".format(
                    issue_info.get("title"), issue_info.get("user", {}).get("login")
                )
            )
        else:
            await ctx.send("No changes were saved.")

    @gh.command(aliases=["removelabel"])
    async def removelabels(self, ctx: commands.Context, issue: int):
        """Interactive command to remove labels from an issue or PR."""
        try:
            token = await self._get_token(ctx)
            repo = await self._get_repo(ctx)
            issue_labels = await GitHubAPI.get_issue_labels(token, repo, issue)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)

        il_names = []
        for label in issue_labels:
            il_names.append(label["name"])

        used_labels = self._inline_list(il_names)
        await ctx.send(
            "You have 30 seconds, please say what label you want to add. Any invalid input will be ignored."
            " This is case sensitive.\n\n"
            f"Labels currently on issue: {used_labels}"
        )

        def check(msg):
            return (
                msg.author == ctx.author
                and msg.channel == ctx.channel
                and (msg.content in il_names or msg.content.casefold() == "exit")
            )

        while True:
            try:
                answer = await self.bot.wait_for("message", check=check, timeout=30.0)
            except TimeoutError:
                return await ctx.send("Timeout.")
            if answer.content.casefold() == "exit":
                return await ctx.send("Done.")
            try:
                await GitHubAPI.remove_label(token, repo, issue, answer.content)
            except EXCEPTIONS as e:
                return await self._handle_error(ctx, e)

            il_names.remove(answer.content)

            used_labels = self._inline_list(il_names)
            await ctx.send(
                "Label removed. Again, 30 seconds. Say another label name if you want to remove one, or `exit` to "
                f"finish.\n\nLabels currently on issue: {used_labels}"
            )

    @gh.command()
    async def open(self, ctx: commands.Context, *, title: str):
        """Open a new issue. Does NOT reopen."""
        try:
            token = await self._get_token(ctx)
            repo = await self._get_repo(ctx)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)

        await ctx.send(
            "Your next message will be the description of the issue. If you answer exactly `cancel` I won't make an"
            " issue. You've got 5 minutes, remember the 2000 Discord character limit!"
        )
        try:
            answer = await self.bot.wait_for(
                "message", check=MessagePredicate.same_context(ctx), timeout=300.0
            )
        except TimeoutError:
            return await ctx.send("Aborting.")
        if answer.content.casefold() == "cancel":
            return await ctx.send("Aborting.")
        else:
            description = answer.content

        await ctx.send("Do you want to add one or more labels to this issue? (yes or no, 15 seconds)")
        pred = MessagePredicate.yes_or_no(ctx)
        try:
            answer = await self.bot.wait_for("message", check=pred, timeout=15.0)
        except TimeoutError:
            return await ctx.send("Aborting.")
        to_add = []
        if pred.result is True:
            repo_labels = await GitHubAPI.get_repo_labels(token, repo)
            rl_names = []
            for label in repo_labels:
                rl_names.append(label["name"])

            avalible_labels = self._inline_list(rl_names)
            await ctx.send(
                "You have 30 seconds, please say what label you want to add. Any invalid input will be ignored."
                " This is case sensitive. Say `exit` to abort creating the issue, or **`create` to make the issue**.\n\n"
                f"Avalible labels: {avalible_labels}"
            )

            def check(msg):
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
                        "It looks like that label's already on the issue. Choose another, 30 seconds."
                    )
                    continue
                to_add.append(answer.content)
                rl_names.remove(answer.content)

                avalible_labels = self._inline_list(rl_names)
                used_labels = self._inline_list(to_add)
                await ctx.send(
                    "Label added. Again, 30 seconds. Say another label name if you want to add more, `create` to create "
                    "the issue or `exit` to exit without saving.\n\n"
                    f"Avalible labels: {avalible_labels}\nLabels currently on issue: {used_labels}"
                )
        try:
            resp = await GitHubAPI.create_issue(token, repo, title, description, to_add)
        except EXCEPTIONS as e:
            return await self._handle_error(ctx, e)

        await ctx.send("Created issue {}: {}".format(resp.get("number"), "<{}>".format(resp.get("html_url"))))
