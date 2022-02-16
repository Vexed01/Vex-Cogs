from __future__ import annotations

from discord import Member, Role
from discord.abc import GuildChannel


def format_bday_message(message: str, author: Member, new_age: int | None = None) -> str:
    """Format the birthday message.

    Parameters
    ----------
    message : str
        Unformatted message from Config

    role : discord.Role
        Birthday role

    Returns
    -------
    str
        Formatted message
    """
    if new_age:
        return message.format(mention=author.mention, name=author.display_name, new_age=new_age)
    else:
        return message.format(mention=author.mention, name=author.display_name)


def role_perm_check(me: Member, role: Role) -> str:
    """Check if I have the correct permissions for this to be the Birthday role.

    Parameters
    ----------
    me : discord.Member
        My user object

    role : discord.Role
        Role to check

    Returns
    -------
    str
        Error message or empty string
    """
    if me.top_role.position <= role.position:
        return (
            "I don't have the required role position. Make sure my role is above the birthday"
            " role."
        )
    if me.guild_permissions.manage_roles is False:
        return "I don't have the Manage Roles permission."
    return ""


def channel_perm_check(me: Member, channel: GuildChannel) -> str:
    """Check if I have the correct permissions for this to be the Birthday channel.

    Parameters
    ----------
    me : discord.Member
        My user object

    channel : discord.TextChannel
        Channel to check

    Returns
    -------
    str
        Error message or empty string
    """
    if channel.permissions_for(me).send_messages is False:
        return "I don't have the Send Messages permission."
    return ""
