from __future__ import annotations

import datetime
from typing import Any, NoReturn

import discord
from redbot.core import commands
from redbot.core.utils import AsyncIter

from .abc import MixinMeta
from .utils import channel_perm_check, format_bday_message, role_perm_check
from .vexutils import get_vex_logger

log = get_vex_logger(__name__)


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
                log.trace("ran coro %s", coro)
            except discord.HTTPException as e:
                log.warning("A queued coro failed to run.", exc_info=e)

        # just using one task for all guilds is okay. maybe it's not the fastest as no async-ness
        # to get them doe faster as (some) rate limits are per-guild
        # but it's fine for now and the loop is hourly

    async def add_role(self, me: discord.Member, member: discord.Member, role: discord.Role):
        if error := role_perm_check(me, role):
            log.warning(
                "Not adding role %s to %s in guild %s because %s",
                role.id,
                member.id,
                member.guild.id,
                error,
            )
            return
        log.trace("Queued birthday role add for %s in guild %s", member.id, member.guild.id)
        self.coro_queue.put_nowait(
            member.add_roles(role, reason="Birthday cog - birthday starts today")
        )

    async def remove_role(self, me: discord.Member, member: discord.Member, role: discord.Role):
        if error := role_perm_check(me, role):
            log.warning(
                "Not removing role to %s in guild %s because %s",
                member.id,
                member.guild.id,
                error,
            )
            return
        log.trace("Queued birthday role remove for %s in guild %s", member.id, member.guild.id)
        self.coro_queue.put_nowait(
            member.remove_roles(role, reason="Birthday cog - birthday ends today")
        )

    async def send_announcement(
        self, channel: discord.TextChannel, message: str, role_mention: bool
    ):
        if error := channel_perm_check(channel.guild.me, channel):
            log.warning(
                "Not sending announcement to %s in guild %s because %s",
                channel.id,
                channel.guild.id,
                error,
            )
            return

        log.trace("Queued birthday announcement for %s in guild %s", channel.id, channel.guild.id)
        log.trace("Message: %s", message)
        self.coro_queue.put_nowait(
            channel.send(
                message,
                allowed_mentions=discord.AllowedMentions(
                    everyone=False, roles=role_mention, users=True
                ),
            )
        )

    async def birthday_loop(self) -> NoReturn:
        """The Birthday loop. This coro will run forever."""
        await self.bot.wait_until_red_ready()
        await self.ready.wait()

        log.verbose("Birthday task started")

        # 1st loop
        try:
            self.loop_meta.iter_start()
            await self._update_birthdays()
            self.loop_meta.iter_finish()
            log.verbose("Initial loop has finished")
        except Exception as e:
            self.loop_meta.iter_error(e)
            log.exception(
                "Something went wrong in the Birthday loop. The loop will try again in an hour."
                "Please report this and the below information to Vexed.",
                exc_info=e,
            )

        # both iter_finish and iter_error set next_iter as not None
        assert self.loop_meta.next_iter is not None
        self.loop_meta.next_iter = self.loop_meta.next_iter.replace(
            minute=0
        )  # ensure further iterations are on the hour

        await self.loop_meta.sleep_until_next()

        # all further iterations
        while True:
            log.verbose("Loop has started next iteration")
            try:
                self.loop_meta.iter_start()
                await self._update_birthdays()
                self.loop_meta.iter_finish()
                log.verbose("Loop has finished")
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
            guild: discord.Guild | None = self.bot.get_guild(int(guild_id))
            if guild is None:
                log.trace("Guild %s is not in cache, skipping", guild_id)
                continue

            if all_settings.get(guild.id) is None:  # can happen with migration from ZeLarp's cog
                log.trace("Guild %s is not setup, skipping", guild_id)
                continue

            if await self.check_if_setup(guild) is False:
                log.trace("Guild %s is not setup, skipping", guild_id)
                continue

            birthday_members: dict[discord.Member, datetime.datetime] = {}

            hour_td = datetime.timedelta(seconds=all_settings[guild.id]["time_utc_s"])

            since_midnight = datetime.datetime.utcnow().replace(
                minute=0, second=0, microsecond=0
            ) - datetime.datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)

            if since_midnight.total_seconds() != hour_td.total_seconds():
                log.trace("Not correct time for update for guild %s, skipping", guild_id)
                continue

            today_dt = (datetime.datetime.utcnow() - hour_td).replace(
                hour=0, minute=0, second=0, microsecond=0
            )

            start = today_dt + hour_td
            end = start + datetime.timedelta(days=1)

            required_role = guild.get_role(all_settings[guild.id].get("required_role"))

            async for member_id, data in AsyncIter(guild_data.items(), steps=50):
                birthday = data["birthday"]
                if not birthday:  # birthday removed but user remains in config
                    continue
                member = guild.get_member(int(member_id))
                if member is None:
                    log.trace(
                        "Member %s for guild %s is not in cache, skipping", member_id, guild_id
                    )
                    continue

                proper_bday_dt = datetime.datetime(
                    year=birthday["year"] or 1, month=birthday["month"], day=birthday["day"]
                )
                this_year_bday_dt = proper_bday_dt.replace(year=today_dt.year) + hour_td

                if required_role and required_role not in member.roles:
                    log.trace(
                        "Member %s for guild %s does not have required role, skipping",
                        member_id,
                        guild_id,
                    )
                    continue

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

            log.trace("Members with birthdays in guild %s: %s", guild_id, birthday_members)

            for member, dt in birthday_members.items():
                if member not in role.members:
                    await self.add_role(guild.me, member, role)

                    if dt.year == 1:
                        await self.send_announcement(
                            channel,
                            format_bday_message(all_settings[guild.id]["message_wo_year"], member),
                            all_settings[guild.id]["allow_role_mention"],
                        )

                    else:
                        age = today_dt.year - dt.year
                        await self.send_announcement(
                            channel,
                            format_bday_message(
                                all_settings[guild.id]["message_w_year"], member, age
                            ),
                            all_settings[guild.id]["allow_role_mention"],
                        )

            for member in role.members:
                if member not in birthday_members:
                    await self.remove_role(guild.me, member, role)

            log.trace("Potential updates for %s have been queued", guild_id)
