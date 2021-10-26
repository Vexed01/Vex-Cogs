import asyncio
from logging import getLogger
from typing import Dict, List, NamedTuple, Union

import aiohttp
import tabulate
from asyncache import cached
from cachetools import TTLCache
from redbot.core import VersionInfo, commands
from redbot.core import version_info as cur_red_version
from redbot.core.utils.chat_formatting import box

from .consts import DOCS_BASE, GREEN_CIRCLE, RED_CIRCLE
from .loop import VexLoop
from .version import __version__ as cur_utils_version

log = getLogger("red.vex-utils")


cog_ver_cache: TTLCache = TTLCache(maxsize=16, ttl=300)  # ttl is 5 mins
cog_ver_lock = asyncio.Lock()


def format_help(self: commands.Cog, ctx: commands.Context) -> str:
    """Wrapper for format_help_for_context. **Not** currently for use outside my cogs.

    Thanks Sinbad.

    Parameters
    ----------
    self : commands.Cog
        The Cog class
    context : commands.Context
        Context

    Returns
    -------
    str
        Formatted help
    """
    docs = DOCS_BASE.format(self.qualified_name.lower())
    pre_processed = super(type(self), self).format_help_for_context(ctx)

    return (
        f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: "
        f"**`{self.__version__}`**\n{docs}"
    )
    # adding docs link here so doesn't show up in auto generated docs


# TODO: get utils version directly from pypi and stop using red internal util


async def format_info(
    qualified_name: str,
    cog_version: str,
    extras: Dict[str, Union[str, bool]] = {},
    loops: List[VexLoop] = [],
) -> str:
    """Generate simple info text about the cog. **Not** currently for use outside my cogs.

    Parameters
    ----------
    qualified_name : str
        The name you want to show, eg "BetterUptime"
    cog_version : str
        The version of the cog
    extras : Dict[str, Union[str, bool]], optional
        Dict which is foramtted as key: value\\n. Bools as a value will be replaced with
        check/cross emojis, by default {}
    loops : List[VexLoop], optional
        List of VexLoops you want to show, by default []

    Returns
    -------
    str
        Simple info text.
    """
    cog_name = qualified_name.lower()
    current = _get_current_vers(cog_version, qualified_name)
    try:
        latest = await _get_latest_vers()

        cog_updated = (
            GREEN_CIRCLE if current.cogs.get(cog_name) >= latest.cogs.get(cog_name) else RED_CIRCLE
        )
        utils_updated = GREEN_CIRCLE if current.utils >= latest.utils else RED_CIRCLE
        red_updated = GREEN_CIRCLE if current.red >= latest.red else RED_CIRCLE
    except Exception:  # anything and everything, eg aiohttp error or version parsing error
        log.warning("Unable to parse versions.", exc_info=True)
        cog_updated, utils_updated, red_updated = "Unknown", "Unknown", "Unknown"
        latest = UnknownVers({cog_name: "Unknown"})

    start = f"{qualified_name} by Vexed.\n<https://github.com/Vexed01/Vex-Cogs>\n\n"
    versions = [
        ["Cog", current.cogs.get(cog_name), latest.cogs.get(cog_name), cog_updated],
        ["Utils", current.utils, latest.utils, utils_updated],
        ["Red", current.red, latest.red, red_updated],
    ]

    data = []
    if loops:
        for loop in loops:
            data.append([loop.friendly_name, GREEN_CIRCLE if loop.integrity else RED_CIRCLE])

    if extras:
        if data:
            data.append([])
        for key, value in extras.items():
            if isinstance(value, bool):
                str_value = GREEN_CIRCLE if value else RED_CIRCLE
            else:
                assert isinstance(value, str)
                str_value = value
            data.append([key, str_value])

    boxed = box(
        tabulate.tabulate(versions, headers=["", "Your Version", "Latest version", "Up to date?"])
    )
    if data:
        boxed += box(tabulate.tabulate(data, tablefmt="plain"))

    return f"{start}{boxed}"


async def out_of_date_check(cogname: str, currentver: str) -> None:
    """Send a log at warning level if the cog is out of date."""
    try:
        async with cog_ver_lock:
            vers = await _get_latest_vers()
    except Exception as e:
        log.debug(
            f"Something went wrong checking if {cogname} cog is up to date. See below.", exc_info=e
        )
        # really doesn't matter if this fails so fine with debug level
        return
    if VersionInfo.from_str(currentver) < vers.cogs.get(cogname):
        log.warning(
            f"Your {cogname} cog, from Vex, is out of date. You can update your cogs with the "
            "'cog update' command in Discord."
        )
    else:
        log.debug(f"{cogname} cog is up to date")


class Vers(NamedTuple):
    cogs: Dict[str, VersionInfo]
    utils: VersionInfo
    red: VersionInfo


class UnknownVers(NamedTuple):
    cogs: Dict[str, str]
    utils: str = "Unknown"
    red: str = "Unknown"


@cached(cog_ver_cache)  # ttl is 5 mins
async def _get_latest_vers() -> Vers:
    data: dict
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://static.vexcodes.com/v1/versions.json", timeout=3  # ik its called static :)
        ) as r:
            data = await r.json()
            latest_cogs = data.get("cogs", {})
        async with session.get("https://pypi.org/pypi/Red-DiscordBot/json", timeout=3) as r:
            data = await r.json()
            latest_red = VersionInfo.from_str(data.get("info", {}).get("version", "0.0.0"))
        async with session.get("https://pypi.org/pypi/vex-cog-utils/json", timeout=3) as r:
            data = await r.json()
            latest_utils = VersionInfo.from_str(data.get("info", {}).get("version", "0.0.0"))

    obj_latest_cogs = {
        str(cogname): VersionInfo.from_str(ver) for cogname, ver in latest_cogs.items()
    }

    return Vers(obj_latest_cogs, latest_utils, latest_red)


def _get_current_vers(curr_cog_ver: str, qual_name: str) -> Vers:
    return Vers(
        {qual_name.lower(): VersionInfo.from_str(curr_cog_ver)},
        VersionInfo.from_str(cur_utils_version),
        cur_red_version,
    )
