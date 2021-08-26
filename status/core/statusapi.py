from typing import Dict, NamedTuple

from aiohttp import ClientSession
from asyncache import cached
from cachetools import TTLCache

from status.core import FEEDS


class APIResp(NamedTuple):
    resp_json: Dict[str, dict]
    etag: str
    status: int


def get_base(service_id: str) -> str:
    if service_id != FEEDS["statuspage"]["id"]:
        return f"https://{service_id}.statuspage.io/api/v2"
    else:  # statuspage's meta status redirects on main domain
        return f"https://{service_id}.metastatuspage.com/api/v2"


class StatusAPI:
    """Interact with the Status API. Includes a cache with a TTL of 90 seconds."""

    # loop is every 120 seconds, so a 90 sec TTL means it *will* refresh each time

    def __init__(self, session: ClientSession):
        self.session = session

    # these endpoints are documented at /api/v2/ of every statuspage domain/subdomain
    # example: https://discordstatus.com/api/v2/

    # the only information i could find about rate limits was at
    # https://support.atlassian.com/statuspage/docs/what-are-the-different-apis-under-statuspage/
    # where they say there are no limits for the status api

    # i will still catch 429s because why not :P

    # you'll see this doesn't implement the whole 8 endpoints of the API, im lazy

    @cached(TTLCache(maxsize=64, ttl=90))
    async def components(self, service_id: str) -> APIResp:
        base = get_base(service_id)

        resp = await self.session.get(f"{base}/components.json")

        respo_json = await resp.json() if resp.status == 200 else {}
        return APIResp(respo_json, resp.headers.get("Etag", ""), resp.status)

    @cached(TTLCache(maxsize=64, ttl=90))
    async def summary(self, service_id: str) -> APIResp:
        base = get_base(service_id)

        resp = await self.session.get(f"{base}/summary.json", timeout=10)

        resp_json = await resp.json() if resp.status == 200 else {}
        return APIResp(resp_json, resp.headers.get("Etag", ""), resp.status)

    @cached(TTLCache(maxsize=64, ttl=90))
    async def scheduled_maintenance(self, service_id: str, etag: str = "") -> APIResp:
        headers = {"If-None-Match": etag}
        base = get_base(service_id)

        resp = await self.session.get(
            f"{base}/scheduled-maintenances.json", headers=headers, timeout=10
        )

        resp_json = await resp.json() if resp.status == 200 else {}
        return APIResp(resp_json, resp.headers.get("Etag", ""), resp.status)

    @cached(TTLCache(maxsize=64, ttl=90))
    async def incidents(self, service_id: str, etag: str = "") -> APIResp:
        headers = {"If-None-Match": etag}
        base = get_base(service_id)

        resp = await self.session.get(f"{base}/incidents.json", headers=headers, timeout=10)

        resp_json = await resp.json() if resp.status == 200 else {}
        return APIResp(resp_json, resp.headers.get("Etag", ""), resp.status)
