import logging

from discord import TextChannel, Webhook
from redbot.core.bot import Red

from status.objects import ChannelData, CogDisabled, ConfChannelSettings, NoPermission, NotFound

_log = logging.getLogger("red.vex.status.sendupdate")


async def get_webhook(channel: TextChannel) -> Webhook:
    """Get, or create, a webhook for the specified channel and return it.

    Parameters
    ----------
    channel : TextChannel
        Target channel

    Returns
    -------
    Webhook
        Valid webhook
    """
    # thanks flare for your webhook logic (redditpost) (or trusty?)
    webhook = None
    for hook in await channel.webhooks():
        if hook.name == channel.guild.me.name:
            webhook = hook

    if webhook is None:
        webhook = await channel.create_webhook(
            name=channel.guild.me.name, reason="Created for status updates"
        )

    return webhook


async def get_channel_data(bot: Red, c_id: int, settings: ConfChannelSettings) -> ChannelData:
    """Get ChannelData from the raw config TypedDict ConfChannelSettings

    Parameters
    ----------
    bot : Red
        Bot
    c_id : int
        Channel ID
    settings : ConfChannelSettings
        TypedDict from config

    Returns
    -------
    ChannelData
        ChannelData obj

    Raises
    ------
    NotFound
        Channel not found
    CogDisabled
        Cog disabled in guild
    NoPermission
        No permission to send
    """
    channel: TextChannel = bot.get_channel(c_id)  # type:ignore
    if channel is None:
        # TODO: maybe remove from config
        _log.info(f"I can't find the channel with id {c_id} - skipping")
        raise NotFound

    if await bot.cog_disabled_in_guild_raw("Status", channel.guild.id):
        _log.info(
            f"Cog is disabled in guild {channel.guild.id} (trying to send to channel {c_id}) - "
            "skipping"
        )
        raise CogDisabled

    if settings["webhook"] and not channel.permissions_for(channel.guild.me).manage_webhooks:
        _log.info(
            f"I don't have permission to send as a webhook in {c_id} in guild {channel.guild.id} "
            "- will send as normal message"
        )
        settings["webhook"] = False

    if not settings.get("webhook") and not channel.permissions_for(channel.guild.me).send_messages:
        _log.info(
            f"Unable to send messages in channel {c_id} in guild {channel.guild.id} - skipping"
        )
        raise NoPermission

    if not settings["webhook"]:
        use_embed = await bot.embed_requested(channel, channel.guild.me)
    else:
        use_embed = True

    return ChannelData(
        channel=channel,
        mode=settings.get("mode", "latest"),
        webhook=settings.get("webhook", False),
        edit_id=settings.get("edit_id", {}),
        embed=use_embed,
    )
