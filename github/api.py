from __future__ import annotations

import aiohttp
import gidgethub.aiohttp

# cspell:ignore resp


class GitHubAPI:
    @staticmethod
    async def repo_info(token: str, slug: str) -> dict | bool:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            try:
                resp = await gh.getitem(f"/repos/{slug}")
                return resp
            except Exception:
                return False

    @staticmethod
    async def get_issue(token: str, repo: str, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.getitem(f"/repos/{repo}/issues/{issue}")

    @staticmethod
    async def get_repo_labels(token: str, repo: str) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.getitem(f"/repos/{repo}/labels")

    @staticmethod
    async def get_issue_labels(token: str, repo: str, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.getitem(f"/repos/{repo}/issues/{issue}/labels")

    @staticmethod
    async def add_labels(token: str, repo: str, issue: int, labels: list) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.post(f"/repos/{repo}/issues/{issue}/labels", data={"labels": labels})

    @staticmethod
    async def remove_label(token: str, repo: str, issue: int, label: str) -> None:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.delete(f"/repos/{repo}/issues/{issue}/labels/{label}")

    @staticmethod
    async def create_issue(token: str, repo: str, title: str, body: str, labels: list) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.post(
                f"/repos/{repo}/issues", data={"title": title, "body": body, "labels": labels}
            )

    @staticmethod
    async def comment(token: str, repo: str, issue: int, body: str) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.post(f"/repos/{repo}/issues/{issue}/comments", data={"body": body})

    @staticmethod
    async def close(token: str, repo: str, issue: int) -> dict:
        async with aiohttp.ClientSession() as session:
            gh = gidgethub.aiohttp.GitHubAPI(session, "GHCog", oauth_token=token)
            return await gh.post(f"/repos/{repo}/issues/{issue}", data={"state": "closed"})
