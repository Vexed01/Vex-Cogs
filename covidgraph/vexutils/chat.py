import datetime
from io import StringIO
from typing import Any, Literal, Sequence, Union

from redbot.core.utils.chat_formatting import box, humanize_list, humanize_number, inline
from rich.console import Console

TimestampFormat = Literal["f", "F", "d", "D", "t", "T", "R"]


def no_colour_rich_markup(*objects: Any, lang: str = "") -> str:
    """
    Slimmed down version of rich_markup which ensure no colours (/ANSI) can exist
    https://github.com/Cog-Creators/Red-DiscordBot/pull/5538/files (Kowlin)
    """
    temp_console = Console(  # Prevent messing with STDOUT's console
        color_system=None,
        file=StringIO(),
        force_terminal=True,
        width=80,
    )
    temp_console.print(*objects)
    return box(temp_console.file.getvalue(), lang=lang)  # type: ignore


def _hum(num: Union[int, float], unit: str, ndigits: int) -> str:
    """Round a number, then humanize."""
    return humanize_number(round(num, ndigits)) + f" {unit}"


def humanize_bytes(bytes: Union[int, float], ndigits: int = 0) -> str:
    """Humanize a number of bytes, rounding to ndigits. Only supports up to GB.

    This assumes 1GB = 1000MB, 1MB = 1000KB, 1KB = 1000B"""
    if bytes > 10000000000:  # 10GB
        gb = bytes / 1000000000
        return _hum(gb, "GB", ndigits)
    if bytes > 10000000:  # 10MB
        mb = bytes / 1000000
        return _hum(mb, "MB", ndigits)
    if bytes > 10000:  # 10KB
        kb = bytes / 1000
        return _hum(kb, "KB", ndigits)
    return _hum(bytes, "B", 0)  # no point in rounding


# maybe think about adding to core
def inline_hum_list(items: Sequence[str], *, style: str = "standard") -> str:
    """Similar to core's humanize_list, but all items are in inline code blocks. **Can** be used
    outside my cogs.

    Strips leading and trailing whitespace.

    Does not support locale.

    Does support style (see core's docs for available styles)

    Parameters
    ----------
    items : Sequence[str]
        The items to humanize
    style : str, optional
        The style. See core's docs, by default "standard"

    Returns
    -------
    str
        Humanized inline list.
    """
    inline_list = [inline(i.strip()) for i in items]
    return humanize_list(inline_list, style=style)


def datetime_to_timestamp(dt: datetime.datetime, format: TimestampFormat = "f") -> str:
    """Generate a Discord timestamp from a datetime object.

    <t:TIMESTAMP:FORMAT>

    Parameters
    ----------
    dt : datetime.datetime
        The datetime object to use
    format : TimestampFormat, by default `f`
        The format to pass to Discord.
        - `f` short date time | `18 June 2021 02:50`
        - `F` long date time  | `Friday, 18 June 2021 02:50`
        - `d` short date      | `18/06/2021`
        - `D` long date       | `18 June 2021`
        - `t` short time      | `02:50`
        - `T` long time       | `02:50:15`
        - `R` relative time   | `8 days ago`

    Returns
    -------
    str
        Formatted timestamp
    """
    t = str(int(dt.timestamp()))
    return f"<t:{t}:{format}>"
