from __future__ import annotations

import logging
import re

from discord import Colour, Embed
from redbot.core.utils.chat_formatting import pagify

from status.core import FEEDS, LINK_RE, SERVICE_LITERAL

from .incidentdata import Update

_log = logging.getLogger("red.vex.status.sendupdate")


# TODO: implement separation for normal embeds and webhook embeds here


class SendCache:
    def __init__(self, update: Update, service: SERVICE_LITERAL):
        self.__incidentdata = update.incidentdata
        self.__new_fields = update.new_fields
        self.__service = service

        self.embed_latest = self._make_embed_latest()
        self.embed_all = self._make_embed_all()
        self.plain_all = self._make_plain_latest()
        self.plain_latest = self._make_plain_all()

    def __repr__(self):
        return (
            f'SendCache({self.embed_latest}, {self.embed_all}, "{self.plain_all}", '
            f'"{self.plain_latest}")'
        )

    def _make_embed_base(self) -> Embed:
        return Embed(
            title=self.__incidentdata.title,
            url=self.__incidentdata.link,
            description=self.__incidentdata.description,
            timestamp=self.__incidentdata.actual_time or self.__incidentdata.time or None,
            colour=self._get_colour(),
        )

    def _make_embed_latest(self) -> Embed:
        embed = self._make_embed_base()
        for field in self.__new_fields:
            embed.add_field(name=field.name, value=field.value, inline=False)

        return self._handle_field_limits(embed)

    def _make_embed_all(self) -> Embed:
        embed = self._make_embed_base()
        for field in self.__incidentdata.fields:
            embed.add_field(name=field.name, value=field.value, inline=False)

        return self._handle_field_limits(embed)

    @staticmethod
    def _handle_field_limits(embed: Embed) -> Embed:
        before_fields = len(embed.fields)
        if before_fields > 25:
            dict_embed = embed.to_dict()

            dict_embed["fields"] = dict_embed.get("fields", [])[-25:]
            embed = Embed.from_dict(dict_embed)
            embed.set_field_at(
                0,
                name=f"{before_fields - 24} earlier updates were omitted.",
                value="This is because embeds are limited to 25 fields.",
            )

        if len(embed) > 6000:  # ffs
            if isinstance(embed.description, str):
                embed.description += (
                    "\nNote: some earlier updates were omitted due to embed limits."
                )
            else:
                embed.description = "Note: some earlier updates were omitted due to embed limits."
            while len(embed) > 6000:
                embed.remove_field(0)

        return embed

    def _make_plain_base(self) -> str:
        title = self.__incidentdata.title
        description = (
            f"{self.__incidentdata.description}\n" if self.__incidentdata.description else ""
        )
        link = self.__incidentdata.link
        name = FEEDS[self.__service]["friendly"]

        return f"**{name} Status Update\n{title}**\nIncident link: {link}\n{description}\n"

    def _make_plain_latest(self) -> str:
        msg = self._make_plain_base()
        for field in self.__new_fields:
            msg += f"**{field.name}**\n{field.value}\n"

        msg = re.sub(LINK_RE, r"<\1>", msg)

        return list(pagify(msg))[0]  # i really dont care about better handling for plain messages

    def _make_plain_all(self) -> str:
        msg = self._make_plain_base()
        for field in self.__incidentdata.fields:
            msg += f"**{field.name}**\n{field.value}\n"

        msg = re.sub(LINK_RE, r"<\1>", msg)

        return list(pagify(msg))[0]  # i really dont care about better handling for plain messages

    def _get_colour(self) -> Colour:
        try:
            last_title = self.__incidentdata.fields[-1].name
            status = last_title.split(" ")[0].lower()

            if status == "identified":
                return Colour.red()
            elif status in [
                "update",
                "monitoring",
                "investigating",
                "scheduled",  # decided to put this in orange as is in future, not now
                "in",  # scheduled - full is "in progress"
                "verifying",
            ]:
                return Colour.orange()
            elif status in ["resolved", "completed"]:
                return Colour.green()
            else:
                return Colour(1812720)
        except Exception:  # hopefully never happens but will keep this for a while
            _log.warning(
                f"Error with getting correct colour for {self.__service}. The update will still "
                "be sent.",
                exc_info=True,
            )
            return Colour(1812720)
