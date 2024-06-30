from __future__ import annotations

import asyncio
import datetime
from typing import TYPE_CHECKING, Optional

from discord import AllowedMentions, Member, Message, Object, Role
from redbot.core import commands
from redbot.core.bot import Red
from redbot.core.config import Config
from redbot.core.utils.chat_formatting import box, humanize_timedelta, pagify

from .vexutils import format_help, format_info, get_vex_logger
from .vexutils.button_pred import wait_for_yes_no

log = get_vex_logger(__name__)


class AutoPing(commands.Cog):
    """
    Automatically ping a user/role when a message is sent in a channel.

    Can be used to notify a user or role when a message is sent in a channel.

    Pings are always sent in the channel the message was sent in.

    Pings are rate limited to a default of 1 per hour.

    If the latest message in the channel when a ping is about to be sent includes a ping of the target user OR is sent by the target user, that user will not be pinged. Roles are always pinged.

    Messages from bots/webhooks are ignored.

    Anyone can run `autoping add` to add themselves to the autoping list for the channel, and users with manage messages permissions or mod can add other users/roles. You can restrict this with the Permissions cog.

    Only users with manage message permissions or mod can change the rate limit.
    """

    __version__ = "1.0.0"
    __author__ = "@vexingvexed"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(self, 418078199982063626, force_registration=True)
        self.config.register_global(version=1)
        self.config.register_channel(autoping=[], rate_limit=3600)

        # channel -> last ping time
        self.last_ping: dict[int, datetime.datetime] = {}

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        # TODO: add deletion for user ids only, ignore roles
        return

    @commands.Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.guild:
            return

        rate_limit = await self.config.channel(message.channel).rate_limit()
        if message.channel.id in self.last_ping:
            if (datetime.datetime.utcnow()) - self.last_ping[
                message.channel.id
            ] < datetime.timedelta(seconds=rate_limit):
                return

        pings_to_remove = set()
        for user in message.mentions:
            pings_to_remove.add(user.id)
        for role in message.role_mentions:
            pings_to_remove.add(role.id)

        pings_to_remove.add(message.author.id)

        ids_to_ping: set[int] = set(await self.config.channel(message.channel).autoping())

        for user_id in pings_to_remove:
            if user_id in ids_to_ping:
                ids_to_ping.remove(user_id)

        self.last_ping[message.channel.id] = datetime.datetime.utcnow()

        roles_to_ping = []
        for user_role_id in ids_to_ping:
            role = message.guild.get_role(user_role_id)
            if role is not None:
                roles_to_ping.append(user_role_id)

        users_to_ping = ids_to_ping.difference(roles_to_ping)

        if not users_to_ping and not roles_to_ping:
            return

        await message.channel.send(
            " ".join(f"<@{user_id}>" for user_id in users_to_ping)
            + "\n"
            + " ".join(f"<@&{role_id}>" for role_id in roles_to_ping),
            allowed_mentions=AllowedMentions(everyone=False, users=True, roles=True),
        )

    @commands.command(hidden=True)
    async def autopinginfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    @commands.group()
    @commands.guild_only()
    async def autoping(self, ctx: commands.Context):
        """Configure autopings for this channel.

        Docs at https://s.vexcodes.com/c/autoping"""

    @autoping.command()
    async def add(
        self,
        ctx: commands.Context,
        *,
        target: Optional[commands.MemberConverter | commands.RoleConverter | str] = None,
    ):
        """Add yourself or a user/role to the autoping list for this channel.

        Only moderators can add other users or roles.

        **Examples:**
        - `[p]autoping add` to add yourself to the list.
        - `[p]autoping add @user` to add a user to the list.
        - `[p]autoping add ID` to add a role/user by ID.
        - `[p]autoping add Role Name` to add a role by name.
        """
        # guild only
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.author, Member)
            real_target: Member | Role

        # did not match a converter
        if isinstance(target, str):
            await ctx.send("User or role not found.")
            return

        if target is None or ctx.author == target:
            real_target = ctx.author
        elif ctx.author.guild_permissions.manage_messages or self.bot.is_mod(ctx.author):
            real_target = target
        else:
            await ctx.send("You do not have permission to add other users or roles.")
            return

        async with self.config.channel(ctx.channel).autoping() as autoping:
            if real_target.id not in autoping:
                autoping.append(real_target.id)
                if real_target == ctx.author:
                    await ctx.send(
                        f"You have been added to the autoping list for this channel. You will be pinged when a message is sent in this channel."
                    )
                else:
                    await ctx.send(
                        f"{real_target.mention} has been added to the autoping list for this channel and will be pinged on new messages."
                    )
            else:
                await ctx.send(
                    f"{real_target.mention} is already on the autoping list for this channel."
                )

    @autoping.command()
    async def remove(
        self,
        ctx: commands.Context,
        *,
        target: Optional[
            commands.ObjectConverter | commands.MemberConverter | commands.RoleConverter | str
        ] = None,
    ):
        """Remove yourself or a user/role from the autoping list for this channel.

        Only moderators can remove other users or roles.

        **Examples:**
        - `[p]autoping remove` to remove yourself from the list.
        - `[p]autoping remove @user` to remove a user from the list.
        - `[p]autoping remove ID` to remove a role/user by ID.
        - `[p]autoping remove Role Name` to remove a role by name.
        """
        # guild only
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.author, Member)
            real_target: Member | Role | Object

        # did not match a converter
        if isinstance(target, str):
            await ctx.send("User or role not found.")
            return

        if target is None or ctx.author == target:
            real_target = ctx.author
        elif ctx.author.guild_permissions.manage_messages or self.bot.is_mod(ctx.author):
            real_target = target
        else:
            await ctx.send("You do not have permission to remove other users or roles.")
            return

        if isinstance(real_target, Object):
            mention = f"ID {real_target.id}"
        else:
            mention = real_target.mention

        async with self.config.channel(ctx.channel).autoping() as autoping:
            if real_target.id in autoping:
                autoping.remove(real_target.id)
                await ctx.send(
                    f"{mention} has been removed from the autoping list for this channel."
                )
            else:
                await ctx.send(f"{mention} is not on the autoping list for this channel.")

    @commands.mod_or_permissions(manage_messages=True)
    @autoping.command()
    async def ratelimit(self, ctx: commands.Context, *, time: commands.TimedeltaConverter):
        """Set the rate limit for autoping in this channel.

        Only moderators can change the rate limit.

        **Examples:**
        - `[p]autoping ratelimit 10 minutes` to set the rate limit to 10 minutes.
        - `[p]autoping ratelimit 1 hour` to set the rate limit to 1 hour.
        """
        # guild only
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.author, Member)

        if time < datetime.timedelta(minutes=1):
            await ctx.send("Rate limit must be at least 1 minute.")
            return

        await self.config.channel(ctx.channel).rate_limit.set(time.total_seconds())

        await ctx.send(f"Rate limit set to {humanize_timedelta(timedelta=time)}.")

    @commands.mod_or_permissions(manage_messages=True)
    @autoping.command()
    async def clear(self, ctx: commands.Context):
        """Clear the autoping list for this channel.

        Only moderators can clear the list.
        """
        # guild only
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.author, Member)

        try:
            result = await wait_for_yes_no(
                ctx,
                "Are you sure you want to remove all users and roles from the autoping list for this channel?",
            )
        except asyncio.TimeoutError:
            return

        if result is True:
            await self.config.channel(ctx.channel).autoping.set([])
            await ctx.send("Autoping list cleared.")
        else:
            await ctx.send("Operation cancelled.")

    @commands.mod_or_permissions(manage_messages=True)
    @autoping.command()
    async def settings(self, ctx: commands.Context):
        """Show the current autoping settings for this channel.

        Only moderators can view the settings.

        Also shows currently added users and roles.
        """
        # guild only
        if TYPE_CHECKING:
            assert ctx.guild is not None
            assert isinstance(ctx.author, Member)

        autoping = await self.config.channel(ctx.channel).autoping()
        rate_limit = await self.config.channel(ctx.channel).rate_limit()

        if not autoping:
            await ctx.send(
                "There are no users or roles on the autoping list for this channel. The rate "
                f"limit is set to {humanize_timedelta(timedelta=datetime.timedelta(seconds=rate_limit))}."
            )
            return

        text = f"Rate limit: {humanize_timedelta(timedelta=datetime.timedelta(seconds=rate_limit))}\n\n"
        unknown_from_user = set()
        unknown_from_role = set()
        text += "Users on the autoping list:\n"
        for user_id in autoping:
            user = ctx.guild.get_member(user_id)
            if user is not None:
                text += f"{user_id} - @{user.name}\n"
            else:
                unknown_from_user.add(user_id)

        text += "\nRoles on the autoping list:\n"
        for role_id in autoping:
            role = ctx.guild.get_role(role_id)
            if role is not None:
                text += f"{role_id} - {role.name}\n"
            else:
                unknown_from_role.add(role_id)

        if unknown := unknown_from_role.intersection(unknown_from_user):
            text += "\nUnknown users/roles:\n"
            for unknown_id in unknown:
                text += f"{unknown_id}\n"

        for page in pagify(text, shorten_by=12):
            await ctx.send(box(page))
