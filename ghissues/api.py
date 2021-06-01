from typing import Union

import aiohttp
import gidgethub.aiohttp

# cspell:ignore resp

# TODO: dont re-create session


class GitHubAPI:
    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    async def repo_info(self, slug: str) -> Union[dict, bool]:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            try:
                resp = await gh.getitem(f"/repos/{slug}")
                return resp
            except Exception:
                return False

    async def get_issue(self, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            ret = await gh.getitem(f"/repos/{self.repo}/issues/{issue}")
            if pr_url := ret.get("pull_request", {}).get("url"):
                return await gh.getitem(pr_url)
            return ret

    async def get_repo_labels(self) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.getitem(f"/repos/{self.repo}/labels")

    async def get_issue_labels(self, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.getitem(f"/repos/{self.repo}/issues/{issue}/labels")

    async def add_labels(self, issue: int, labels: list) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.post(
                f"/repos/{self.repo}/issues/{issue}/labels", data={"labels": labels}
            )

    async def remove_label(self, issue: int, label: str) -> None:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.delete(f"/repos/{self.repo}/issues/{issue}/labels/{label}")

    async def create_issue(self, title: str, body: str, labels: list) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.post(
                f"/repos/{self.repo}/issues", data={"title": title, "body": body, "labels": labels}
            )

    async def comment(self, issue: int, body: str) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.post(
                f"/repos/{self.repo}/issues/{issue}/comments", data={"body": body}
            )

    async def close(self, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.post(f"/repos/{self.repo}/issues/{issue}", data={"state": "closed"})
