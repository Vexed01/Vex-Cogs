from __future__ import annotations

from discord import Member


def format_bday_message(message: str, author: Member, new_age: int | None = None) -> str:
    """
    Formats the birthday message.
    """
    if new_age:
        return message.format(mention=author.mention, name=author.display_name, new_age=new_age)
    else:
        return message.format(mention=author.mention, name=author.display_name)
