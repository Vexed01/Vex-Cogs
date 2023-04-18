from __future__ import annotations

import asyncio
import json
from pathlib import Path
from typing import Literal, NamedTuple

import aiohttp
from red_commons.logging import RedTraceLogger
from red_commons.logging import getLogger as red_get_logger
from redbot.core import VersionInfo, commands
from redbot.core import version_info as cur_red_version
from rich import box as rich_box
from rich.table import Table  # type:ignore

from .chat import no_colour_rich_markup
from .consts import DOCS_BASE, GREEN_CIRCLE, RED_CIRCLE
from .loop import VexLoop

log = red_get_logger("red.vex-utils")


cog_ver_lock = asyncio.Lock()


def get_vex_logger(name: str) -> RedTraceLogger:
    """Get a logger for the given name.

    Parameters
    ----------
    name : str
        The ``__name__`` of the file

    Returns
    -------
    Logger
        The logger
    """
    final_name = "red.vex."
    split = name.split(".")
    if len(split) == 2 and split[0] == split[1]:  # for example make `cmdlog.cmdlog` just `cmdlog`
        final_name += split[0]
    else:  # otherwise use full path
        final_name += name

    return red_get_logger(final_name)


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
    pre_processed = super(type(self), self).format_help_for_context(ctx)  # type:ignore

    return (
        f"{pre_processed}\n\nAuthor: **`{self.__author__}`**\nCog Version: "  # type:ignore
        f"**`{self.__version__}`**\n{docs}"  # type:ignore
    )
    # adding docs link here so doesn't show up in auto generated docs


# TODO: stop using red internal util


async def format_info(
    ctx: commands.Context,
    qualified_name: str,
    cog_version: str,
    extras: dict[str, str | bool] = {},
    loops: list[VexLoop] = [],
) -> str:
    """Generate simple info text about the cog. **Not** currently for use outside my cogs.

    Parameters
    ----------
    ctx : commands.Context
        Context
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
        latest = await _get_latest_vers(cog_name)

        cog_updated = current.cog >= latest.cog
        utils_updated = current.utils == latest.utils
        red_updated = current.red >= latest.red
    except Exception:  # anything and everything, eg aiohttp error or version parsing error
        log.warning("Unable to parse versions.", exc_info=True)
        cog_updated, utils_updated, red_updated = "Unknown", "Unknown", "Unknown"
        latest = UnknownVers()

    start = f"{qualified_name} by Vexed.\n<https://github.com/Vexed01/Vex-Cogs>\n\n"

    main_table = Table(
        "", "Current", "Latest", "Up to date?", title="Versions", box=rich_box.MINIMAL
    )

    main_table.add_row(
        "This Cog",
        str(current.cog),
        str(latest.cog),
        GREEN_CIRCLE if cog_updated else RED_CIRCLE,
    )
    main_table.add_row(
        "Bundled Utils",
        current.utils,
        latest.utils,
        GREEN_CIRCLE if utils_updated else RED_CIRCLE,
    )
    main_table.add_row(
        "Red",
        str(current.red),
        str(latest.red),
        GREEN_CIRCLE if red_updated else RED_CIRCLE,
    )

    update_msg = "\n"
    if not cog_updated:
        update_msg += f"To update this cog, use the `{ctx.clean_prefix}cog update` command.\n"
    if not utils_updated:
        update_msg += (
            f"To update the bundled utils, use the `{ctx.clean_prefix}cog update` command.\n"
        )
    if not red_updated:
        update_msg += "To update Red, see https://docs.discord.red/en/stable/update_red.html\n"

    extra_table = Table("Key", "Value", title="Extras", box=rich_box.MINIMAL)

    data = []
    if loops:
        for loop in loops:
            extra_table.add_row(loop.friendly_name, GREEN_CIRCLE if loop.integrity else RED_CIRCLE)

    if extras:
        if data:
            extra_table.add_row("", "")
        for key, value in extras.items():
            if isinstance(value, bool):
                str_value = GREEN_CIRCLE if value else RED_CIRCLE
            else:
                assert isinstance(value, str)
                str_value = value
            extra_table.add_row(key, str_value)

    boxed = no_colour_rich_markup(main_table)
    boxed += update_msg
    if loops or extras:
        boxed += no_colour_rich_markup(extra_table)

    return f"{start}{boxed}"


async def out_of_date_check(cogname: str, currentver: str) -> None:
    """Send a log at warning level if the cog is out of date."""
    try:
        async with cog_ver_lock:
            vers = await _get_latest_vers(cogname)
        if VersionInfo.from_str(currentver) < vers.cog:
            log.warning(
                f"Your {cogname} cog, from Vex, is out of date. You can update your cogs with the "
                "'cog update' command in Discord."
            )
        else:
            log.debug(f"{cogname} cog is up to date")
    except Exception as e:
        log.debug(
            f"Something went wrong checking if {cogname} cog is up to date. See below.", exc_info=e
        )
        # really doesn't matter if this fails so fine with debug level
        return


class Vers(NamedTuple):
    cogname: str
    cog: VersionInfo
    utils: str
    red: VersionInfo


class UnknownVers(NamedTuple):
    cogname: str = "Unknown"
    cog: VersionInfo | Literal["Unknown"] = "Unknown"
    utils: str = "Unknown"
    red: VersionInfo | Literal["Unknown"] = "Unknown"


async def _get_latest_vers(cogname: str) -> Vers:
    data: dict
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://api.vexcodes.com/v2/vers/{cogname}", timeout=3) as r:
            data = await r.json()
            latest_utils = data["utils"][:7]
            latest_cog = VersionInfo.from_str(data.get(cogname, "0.0.0"))
        async with session.get("https://pypi.org/pypi/Red-DiscordBot/json", timeout=3) as r:
            data = await r.json()
            latest_red = VersionInfo.from_str(data.get("info", {}).get("version", "0.0.0"))

    return Vers(cogname, latest_cog, latest_utils, latest_red)


def _get_current_vers(curr_cog_ver: str, qual_name: str) -> Vers:
    with open(Path(__file__).parent / "commit.json") as fp:
        data = json.load(fp)
        latest_utils = data.get("latest_commit", "Unknown")[:7]

    return Vers(
        qual_name,
        VersionInfo.from_str(curr_cog_ver),
        latest_utils,
        cur_red_version,
    )
