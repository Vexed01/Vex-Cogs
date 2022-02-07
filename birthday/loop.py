from __future__ import annotations

import datetime
from logging import getLogger
from typing import Any

import discord
from redbot.core import commands
from redbot.core.utils import AsyncIter

from .abc import MixinMeta
from .utils import format_bday_message

log = getLogger("red.vex.birthday.loop")


class BirthdayLoop(MixinMeta):
    @commands.command(hidden=True)
    @commands.is_owner()
    async def bdloopdebug(self, ctx: commands.Context) -> None:
        """
        Sends the current state of the Birthday loop.
        """
        await ctx.send(embed=self.loop_meta.get_debug_embed())

    async def birthday_role_manager(self) -> None:
        """Birthday role manager to handle coros, so they don't slow
        down the main loop. Remember d.py handles ratelimits."""
        while True:
            try:
                coro = await self.coro_queue.get()
                await coro
            except discord.HTTPException as e:
                log.debug("A queued coro failed to run.", exc_info=e)

        # just using one task for all guilds is okay. maybe it's not the fastest as no async-ness
        # but it's fine for now and the loop is at max hourly

    async def birthday_loop(self) -> None:
        """The Birthday loop. This coro will run forever."""
        await self.bot.wait_until_red_ready()
        await self.ready.wait()

        while True:
            log.debug("Loop has started next iteration")
            try:
                self.loop_meta.iter_start()
                await self._update_birthdays()
                self.loop_meta.iter_finish()
                log.debug("Loop has finished")
            except Exception as e:
                self.loop_meta.iter_error(e)
                log.exception(
                    "Something went wrong in the Birthday loop. The loop will try again "
                    "in an hour. Please report this and the below information to Vexed.",
                    exc_info=e,
                )

            await self.loop_meta.sleep_until_next()

    async def _update_birthdays(self):
        """Update birthdays"""
        all_birthdays: dict[int, dict[int, dict[str, Any]]] = await self.config.all_members()
        all_settings: dict[int, dict[str, Any]] = await self.config.all_guilds()

        async for guild_id, guild_data in AsyncIter(all_birthdays.items(), steps=5):
            guild = self.bot.get_guild(int(guild_id))
            if guild is None:
                log.debug("Guild %s is not in cache, skipping", guild_id)
                continue

            if all_settings.get(guild.id) is None:  # can happen with migration from ZeLarp's cog
                log.debug("Guild %s is not setup, skipping", guild_id)
                continue

            if await self.check_if_setup(guild) is False:
                log.debug("Guild %s is not setup, skipping", guild_id)
                continue

            birthday_members: dict[discord.Member, datetime.datetime] = {}

            today_dt = datetime.datetime.utcnow().replace(
                hour=0, minute=0, second=0, microsecond=0
            )
            start = today_dt + datetime.timedelta(seconds=all_settings[guild.id]["time_utc_s"])
            end = start + datetime.timedelta(days=1)

            async for member_id, data in AsyncIter(guild_data.items(), steps=50):
                birthday = data["birthday"]
                member = guild.get_member(int(member_id))
                if member is None:
                    log.debug(
                        "Member %s for guild %s is not in cache, skipping", member_id, guild_id
                    )
                    continue

                proper_bday_dt = datetime.datetime(
                    year=birthday["year"] or 1, month=birthday["month"], day=birthday["day"]
                )
                this_year_bday_dt = proper_bday_dt.replace(year=today_dt.year)

                if start <= this_year_bday_dt < end:  # birthday is today
                    birthday_members[member] = proper_bday_dt

            role = guild.get_role(all_settings[guild.id]["role_id"])
            if role is None:
                log.warning(
                    "Role %s for guild %s (%s) was not found",
                    all_settings[guild.id]["role_id"],
                    guild_id,
                    guild.name,
                )
                continue

            channel = guild.get_channel(all_settings[guild.id]["channel_id"])
            if channel is None or not isinstance(channel, discord.TextChannel):
                log.warning(
                    "Channel %s for guild %s (%s) was not found",
                    all_settings[guild.id]["channel_id"],
                    guild_id,
                    guild.name,
                )
                continue

            log.debug("Members with birthdays in guild %s: %s", guild_id, birthday_members)

            for member, dt in birthday_members.items():
                if member not in role.members:
                    self.coro_queue.put_nowait(
                        member.add_roles(role, reason="Birthday cog - birthday starts today")
                    )
                    log.debug("Queued birthday role add for %s in guild %s", member.id, guild_id)
                    if dt.year == 1:
                        self.coro_queue.put_nowait(
                            channel.send(
                                format_bday_message(
                                    all_settings[guild.id]["message_wo_year"], member
                                )
                            )
                        )
                        log.debug(
                            "Queued birthday message wo year for %s in guild %s",
                            member.id,
                            guild_id,
                        )

                    else:
                        age = today_dt.year - dt.year
                        self.coro_queue.put_nowait(
                            channel.send(
                                format_bday_message(
                                    all_settings[guild.id]["message_w_year"], member, age
                                )
                            )
                        )
                        log.debug(
                            "Queued birthday message w year for %s in guild %s",
                            member.id,
                            guild_id,
                        )

            for member in role.members:
                if member not in birthday_members:
                    self.coro_queue.put_nowait(
                        member.remove_roles(role, reason="Birthday cog - birthday ends today")
                    )
                    log.debug(
                        "Queued birthday role remove for %s in guild %s", member.id, guild_id
                    )

            log.debug("Potential updates for %s have been queued", guild_id)
