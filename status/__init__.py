import contextlib
import importlib
import json
from pathlib import Path
from typing import AsyncContextManager

from redbot.core import VersionInfo
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils import AsyncIter

from status.vexutils.meta import out_of_date_check

from . import vexutils
from .core.core import Status

with open(Path(__file__).parent / "info.json") as fp:
    __red_end_user_data_statement__ = json.load(fp)["end_user_data_statement"]


async def maybe_migrate_config_identifier() -> None:
    old_config: Config = Config.get_conf(
        None, cog_name="Status", identifier="Vexed-status"  # type:ignore
    )
    new_config: Config = Config.get_conf(None, cog_name="Status", identifier=418078199982063626)
    new_config.register_global(migrated_identifier=False)

    if await new_config.migrated_identifier() is True:
        return

    await new_config.version.set(await old_config.version())
    await new_config.feed_store.set(await old_config.feed_store())
    await new_config.old_ids.set(await old_config.old_ids())

    old_channel_data = await old_config.all_channels()
    async for channel, data in AsyncIter(old_channel_data.items(), steps=25):
        await new_config.channel_from_id(channel).feeds.set(data.get("feeds"))

    old_guild_data = await old_config.all_guilds()
    async for guild, data in AsyncIter(old_guild_data.items(), steps=25):
        await new_config.guild_from_id(guild).service_restrictions.set(
            data.get("service_restrictions")
        )

    await new_config.migrated_identifier.set(True)
    await old_config.clear_all()


async def setup(bot: Red) -> None:
    await maybe_migrate_config_identifier()

    cog = Status(bot)
    await out_of_date_check("status", cog.__version__)
    await cog.async_init()
    bot.add_cog(cog)
