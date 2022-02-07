from __future__ import annotations

import aiohttp
import gidgethub.aiohttp

# cspell:ignore resp

# TODO: dont re-create session


class GitHubAPI:
    def __init__(self, repo: str, token: str) -> None:
        self.repo = repo
        self.token = token

    async def repo_info(self, slug: str) -> dict | bool:
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
            return await gh.getitem(f"/repos/{self.repo}/labels?per_page=100")

    async def get_issue_labels(self, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.getitem(f"/repos/{self.repo}/issues/{issue}/labels?per_page=100")

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

    async def create_issue(self, title: str, body: str) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.post(f"/repos/{self.repo}/issues", data={"title": title, "body": body})

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

    async def open(self, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.post(f"/repos/{self.repo}/issues/{issue}", data={"state": "open"})

    async def merge(
        self, issue: int, commit_title: str, commit_message: str | None, merge_method: str
    ) -> dict:
        data = {
            "commit_title": commit_title,
            "merge_method": merge_method,
        }
        if commit_message:
            data["commit_message"] = commit_message

        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=self.token)
            return await gh.put(f"/repos/{self.repo}/pulls/{issue}/merge", data=data)
