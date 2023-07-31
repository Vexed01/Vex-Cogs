from __future__ import annotations

import random
from typing import TYPE_CHECKING, Optional, TypedDict

import discord
from redbot.core import Config, commands
from redbot.core.bot import Red

from .vexutils import format_help, format_info, get_vex_logger

log = get_vex_logger(__name__)


class Cache(TypedDict):
    main_channel: discord.TextChannel | None
    log_channel: discord.TextChannel | None
    embed: bool
    radio: bool
    delete_after: int | None
    radiotitle: str
    radioimage: str | None
    radiofooter: str | None


class RolePlay(commands.Cog):
    """
    Set up a role play, where the author of messages are secret - the bot reposts all messages.

    Admins can get started with `[p]roleplay channel`, as well as some other configuration options.
    """

    __version__ = "1.1.0"
    __author__ = "@vexingvexed"

    def __init__(self, bot: Red) -> None:
        self.bot = bot

        self.config: Config = Config.get_conf(
            self, identifier=418078199982063626, force_registration=True
        )
        self.config.register_guild(
            main_channel=None,
            log_channel=None,
            embed=False,
            radio=False,
            delete_after=None,
            radiotitle="New radio transmission detected",
            radioimage=None,
            radiofooter=None,
        )

        self.cache: dict[int, Cache] = {}

    async def populate_cache(self) -> None:
        raw = await self.config.all_guilds()
        for guild_id, data in raw.items():
            self.cache[guild_id] = {
                "main_channel": self.bot.get_channel(data["main_channel"]),
                "log_channel": self.bot.get_channel(data["log_channel"]),
                "embed": data["embed"],
                "radio": data["radio"],
                "delete_after": data["delete_after"],
                "radiotitle": data["radiotitle"],
                "radioimage": data["radioimage"],
                "radiofooter": data["radiofooter"],
            }

    def format_help_for_context(self, ctx: commands.Context) -> str:
        """Thanks Sinbad."""
        return format_help(self, ctx)

    async def red_delete_data_for_user(self, **kwargs) -> None:
        """User's messages are anonymized so it is not possible to delete them."""
        return

    @commands.command(hidden=True)
    async def roleplayinfo(self, ctx: commands.Context):
        await ctx.send(await format_info(ctx, self.qualified_name, self.__version__))

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message) -> None:
        if message.author.bot:
            return

        if message.guild is None:
            return

        if message.guild.id not in self.cache.keys():
            return

        if message.channel != self.cache[message.guild.id]["main_channel"]:
            return

        try:
            await message.delete()
        except discord.HTTPException as e:
            log.warning(
                "Could not delete message in guild %s",
                message.guild.id,
                exc_info=e,
            )
            return

        data = self.cache[message.guild.id]

        if data["main_channel"] is None:  # should have been caught earlier
            return

        allowed_mentions = discord.AllowedMentions(everyone=False, users=False, roles=False)
        delete_after = data["delete_after"] * 60 if data["delete_after"] else None

        if data["radio"]:
            distorted_text = ""
            for c in message.content:
                if c.isspace() or c.isnumeric():
                    distorted_text += c
                    continue

                if random.choices([True, False], [0.1, 0.9], k=1)[0]:  # cut out 1 in 10 characters
                    distorted_text += "-"
                else:
                    distorted_text += c

            if data["embed"]:
                embed = discord.Embed(
                    title=data["radiotitle"],
                    description=distorted_text,
                    color=await self.bot.get_embed_color(message.channel),
                    timestamp=message.created_at,
                )

                if data["radioimage"]:
                    embed.set_thumbnail(url=data["radioimage"])
                if data["radiofooter"]:
                    embed.set_footer(text=data["radiofooter"])

                allowed_mentions = (allowed_mentions,)
                delete_after = (delete_after,)
                new_msg = await data["main_channel"].send(embed=embed)
            else:
                new_msg = await data["main_channel"].send(
                    distorted_text,
                    allowed_mentions=allowed_mentions,
                    delete_after=delete_after,
                )

        else:
            if data["embed"]:
                new_msg = await data["main_channel"].send(
                    embed=discord.Embed(
                        description=message.content,
                        timestamp=message.created_at,
                        colour=await self.bot.get_embed_color(message.channel),
                    ),
                    allowed_mentions=allowed_mentions,
                    delete_after=delete_after,
                )
            else:
                new_msg = await data["main_channel"].send(
                    message.content,
                    allowed_mentions=allowed_mentions,
                    delete_after=delete_after,
                )

        if data["log_channel"]:
            embed = discord.Embed(title="New role play message", description=message.content)
            embed.set_author(
                name=f"{str(message.author)} ({message.author.id})",
                icon_url=message.author.display_avatar.url,
            )
            embed.add_field(name="Jump link", value=new_msg.jump_url)
            try:
                await data["log_channel"].send(embed=embed)
            except discord.HTTPException as e:
                log.warning("Unable to log roleplay in guild %s", message.guild.id, exc_info=e)

    @commands.group()
    @commands.guild_only()
    @commands.admin_or_permissions(manage_guild=True)
    @commands.bot_has_permissions(manage_messages=True)
    async def roleplay(self, ctx: commands.Context):
        """
        Role play configuration.

        This is a group command, so you can use it to configure the roleplay for a channel.

        Get started with `[p]roleplay channel`.
        """

    @roleplay.command()
    async def channel(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """
        Set the channel for the roleplay.

        Leave blank to disable.

        **Examples:**
        - `[p]roleplay channel` - disable roleplay
        - `[p]roleplay channel #roleplay` - set the channel to #roleplay
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if channel is None:
            await self.config.guild(ctx.guild).main_channel.set(None)
            if self.cache.get(ctx.guild.id):
                del self.cache[ctx.guild.id]
            await ctx.send(
                f"Roleplay disabled. If you meant to set it, see `{ctx.clean_prefix}help roleplay"
                " channel`."
            )
            return

        async with self.config.guild(ctx.guild).all() as conf:
            conf["main_channel"] = channel.id

            self.cache[ctx.guild.id] = {
                "main_channel": channel,
                "log_channel": ctx.guild.get_channel(conf["log_channel"]),
                "embed": conf["embed"],
                "radio": conf["radio"],
                "delete_after": conf["delete_after"],
            }

        await ctx.send(f"Roleplay channel set to {channel.mention}. I'll start right away!")

    @roleplay.command()
    async def embed(self, ctx: commands.Context, embed: bool):
        """Enable or disable embeds.

        The default is disabled.

        **Examples:**
        - `[p]roleplay embed true` - enable
        - `[p]roleplay embed false` - disable
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a channel first.")
            return

        await self.config.guild(ctx.guild).embed.set(embed)
        self.cache[ctx.guild.id]["embed"] = embed

        await ctx.send(f"Embed mode set to {embed}.")

    @roleplay.command()
    async def radio(self, ctx: commands.Context, radio: bool):
        """Enable or disable radio.

        The default is disabled.

        **Examples:**
        - `[p]roleplay radio true` - enable radio mode
        - `[p]roleplay radio false` - disable radio mode
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a channel first.")
            return

        await self.config.guild(ctx.guild).radio.set(radio)
        self.cache[ctx.guild.id]["radio"] = radio

        await ctx.send(f"Radio mode set to {radio}.")

    @roleplay.command()
    async def log(self, ctx: commands.Context, channel: Optional[discord.TextChannel]):
        """Set a channel to log role play messages to.

        If you do not specify a channel logging will be disabled.

        **Examples:**
        - `[p]roleplay log #logs` - set to a channel called logs
        - `[p]roleplay log` - disable logging
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a main channel first with `roleplay channel`.")
            return

        if channel is None:
            await self.config.guild(ctx.guild).log_channel.set(None)
            self.cache[ctx.guild.id]["log_channel"] = None

            await ctx.send(
                f"Logging disabled. If you meant to set it see `{ctx.clean_prefix}help roleplay"
                " log`."
            )
            return

        await self.config.guild(ctx.guild).log_channel.set(channel.id)
        self.cache[ctx.guild.id]["log_channel"] = channel

        await ctx.send(f"Log channel set to {channel.mention}.")

    @roleplay.command()
    async def delete(self, ctx: commands.Context, delete_after: Optional[int]):
        """Automatically delete messages in the role play channel after time has passed.

        The time is in minutes.

        The default is disabled.

        **Examples:**
        - `[p]roleplay delete 5` - delete after 5 mins
        - `[p]roleplay delete 30` - delete after 30 mins
        - `[p]roleplay delete` - disable deletion
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a main channel first with `roleplay channel`.")
            return

        if delete_after is None:
            await self.config.guild(ctx.guild).delete_after.set(None)
            self.cache[ctx.guild.id]["delete_after"] = None

            await ctx.send(
                f"Deletion disabled. If you meant to set it see `{ctx.clean_prefix}help roleplay"
                " delete`."
            )
            return

        if delete_after < 1:
            await self.config.guild(ctx.guild).delete_after.set(None)
            self.cache[ctx.guild.id]["delete_after"] = None

            await ctx.send("Deletion disabled because you entered a number below 1.")
            return

        await self.config.guild(ctx.guild).delete_after.set(delete_after)
        self.cache[ctx.guild.id]["delete_after"] = delete_after

        await ctx.send(f"Deletion set to {delete_after} minutes.")

    @roleplay.command()
    async def radiotitle(self, ctx: commands.Context, *, title: str):
        """Set a title for radio mode (embed only)

        This only applies to embeds.

        **Example:**
        - `[p]roleplay radiotitle New radio transmission detected` - the default
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a main channel first with `roleplay channel`.")
            return

        await self.config.guild(ctx.guild).radiotitle.set(title)
        self.cache[ctx.guild.id]["radiotitle"] = title

        await ctx.send(f"Radio title set to {title}.")

    @roleplay.command()
    async def radioimage(self, ctx: commands.Context, image_url: Optional[str]):
        """Set an image for radio mode (embed only)

        This only applies to embeds.

        **Example:**
        - `[p]roleplay radioimage https://i.imgur.com/example.png`
        - `[p]roleplay radioimage` - reset to none
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a main channel first with `roleplay channel`.")
            return

        if image_url is None:
            await self.config.guild(ctx.guild).radioimage.set(None)
            self.cache[ctx.guild.id]["radioimage"] = None

            await ctx.send(
                f"Radio image reset. If you meant to set it see `{ctx.clean_prefix}help roleplay"
                " radioimage`."
            )
            return

        await self.config.guild(ctx.guild).radioimage.set(image_url)
        self.cache[ctx.guild.id]["radioimage"] = image_url

        await ctx.send(f"Radio image set to {image_url}.")

    @roleplay.command()
    async def radiofooter(self, ctx: commands.Context, *, footer: Optional[str]) -> None:
        """Set a footer for radio mode (embed only)

        This only applies to embeds.

        **Example:**
        - `[p]roleplay radiofooter Transmission over`
        - `[p]roleplay radiofooter` - reset to none
        """
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a main channel first with `roleplay channel`.")
            return

        if not footer:
            await ctx.send(
                f"Radio footer reset. If you meant to set it see `{ctx.clean_prefix}help roleplay"
                " radiofooter`."
            )
            await self.config.guild(ctx.guild).radioimage.set(None)
            self.cache[ctx.guild.id]["radiofooter"] = None
            return

        await self.config.guild(ctx.guild).radiofooter.set(footer)
        self.cache[ctx.guild.id]["radiofooter"] = footer

        await ctx.send("Radio footer set")

    @roleplay.command()
    async def settings(self, ctx: commands.Context):
        """View the current settings for the roleplay."""
        # guild check on group command
        if TYPE_CHECKING:
            assert ctx.guild is not None

        if ctx.guild.id not in self.cache.keys():
            await ctx.send("You need to set a main channel first with `roleplay channel`.")
            return

        data = self.cache[ctx.guild.id]

        embed = discord.Embed(
            title="Roleplay Settings",
            description="These are the current settings for the roleplay.",
            colour=await self.bot.get_embed_color(ctx.channel),
        )

        embed.add_field(name="Main Channel", value=data["main_channel"].mention)
        embed.add_field(
            name="Log Channel",
            value=data["log_channel"].mention if data["log_channel"] else "Disabled",
        )
        embed.add_field(name="Embed Mode", value=data["embed"])
        embed.add_field(name="Radio Mode", value=data["radio"])
        embed.add_field(
            name="Delete After", value=(str(data["delete_after"]) + "mins") or "Disabled"
        )
        embed.add_field(name="Radio Title", value=data["radiotitle"])
        embed.add_field(name="Radio image", value=data.get("radioimage", "Not set"))
        embed.add_field(name="Radio footer", value=data.get("radiofooter", "Not set"))

        await ctx.send(embed=embed)
