# ======== PLEASE READ ======================================================
# Status is currently a bit of a mess. For this reason, I'll be undertaking a
# rewrite in the near future: https://github.com/Vexed01/Vex-Cogs/issues/13
#
# For this reason, unless it's minor, PLEASE DO NOT OPEN A PR.
# ===========================================================================


import datetime
import logging
import re
from typing import List

import discord
from dateutil.parser import ParserError, parse
from feedparser.util import FeedParserDict
from redbot.core.utils.chat_formatting import pagify

from .objects import FeedDict, UpdateField

_log = logging.getLogger("red.vexed.status.rsshelper")

# cspell:ignore tzinfos statusio


def process_feed(service: str, feed: FeedParserDict) -> List[FeedDict]:
    return [FEEDS[service](entry) for entry in feed.entries if entry]


def _strip_html(thing_to_strip) -> str:
    """Strip dat HTML!

    This removes anything between (and including) `<>` (be careful with this!).
    It will NOT strip `<>` if there is nothing in-between.

    `<br />` will be replaced with `\\n`.
    `<small>` will be replaced with `=-=SPLIT=-=`
    `</small>` wil also be reaplaced with `\\n`.
    Any other tags in format <> will be removed.

    Please don't use this elsewhere, it is designed for this special purpose.
    """
    tostrip = str(thing_to_strip)
    raw = tostrip.replace("<br />", "\n")
    raw = raw.replace("<small>", "=-=SPLIT=-=")
    raw = raw.replace("</p>", "\n")
    regex = re.compile("<.*?>")
    return re.sub(regex, "", raw)


def _parse_time(time: str):
    try:
        return parse(time, tzinfos={"PST": -28800, "PDT": -25200})
        #                                  - 8 h          - 7 h
    except (ValueError, ParserError):
        if not time.endswith("Feb 29, 00:00 UTC"):  # python not having many incidents and referencing a date from last
            # year, then the time parser assume it's this year with didn't have a feb 29
            _log.warning(f"Unable to parse timestamp '{time}'. Please report this to Vexed.")
        return discord.Embed.Empty


def _split_long_fields(old_fields: List[UpdateField]) -> List[UpdateField]:  # using updatefield because idk really
    """Split long fields (over 1024 chars) into multiple, retaining order."""
    new_fields = []
    for field in old_fields:
        field.value = re.sub(r"(\n\n\n)(\n)*", "\n\n", field.value)
        if len(field.value) <= 1024:
            new_fields.append(field)
        else:
            paged = list(pagify(field.value, page_length=1024))
            new_fields.append(UpdateField(field.name, paged[0], field.name))
            for page in paged[1:]:
                new_fields.append(UpdateField("Above continued (hit field limits)", page, field.name))

    return new_fields


def _parse_statuspage(feed: FeedParserDict):
    strippedcontent = _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    fields: List[UpdateField] = []
    desc = None

    for data in sections:
        try:
            if data != "":
                current = data.split("-", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0].lstrip()
                title = tt[1].rstrip()
                fields.append(UpdateField("{} - {}".format(title, time), content, _parse_time(time)))
        except IndexError:  # this would be a likely error if something didn't format as expected
            try:
                if data.startswith("THIS IS A SCHEDULED EVENT"):
                    split = data.split("EVENT", 1)
                    value = split[1].lstrip()
                    desc = f"Scheduled for **{value}**"
                    continue
            except IndexError:
                pass
            fields.append(
                UpdateField(
                    name="Something went wrong with this section",
                    value=f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                )
            )
            _log.warning(
                "Unable to parse a section of a feed properly. It was still send to all channels. See below debugs:"
                f"\nTimestamp: {datetime.datetime.utcnow()}"
                f"\nSection data: {data}"
            )

    actual_update_time = _parse_time(fields[0].name.split("-")[1])

    # statuspage why do you give everything in the wrong order...
    fields.reverse()
    fields = _split_long_fields(fields)

    return FeedDict(
        fields=fields,
        time=_parse_time(feed["published"]),
        title=feed["title"],
        link=feed["link"],
        actual_time=actual_update_time,
        description=desc,
    )


def _parse_statusio(feed: FeedParserDict):
    strippedcontent = _strip_html(feed["summary_detail"]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    fields = []

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                fields.append(UpdateField("{} - {}".format(title, time), content, _parse_time(time)))
        except IndexError:  # this would be a likely error if something didn't format as expected
            fields.append(
                UpdateField(
                    name="Something went wrong with this section",
                    value=f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                )
            )
            _log.warning(
                "Unable to parse a section of a feed properly. It was still send to all channels. See below debugs:"
                f"\nTimestamp: {datetime.datetime.utcnow()}"
                f"\nSection data: {data}"
            )

    actual_update_time = _parse_time(fields[-1].name.split("-")[1])

    fields = _split_long_fields(fields)

    return FeedDict(
        fields=fields,
        time=_parse_time(feed["published"]),
        title=feed["title"],
        link=feed["link"],
        actual_time=actual_update_time,
    )


def _parse_aws(feed: FeedParserDict):
    updated = _parse_time(feed["published"])
    fields = _split_long_fields([UpdateField(feed["published"], feed["description"], updated)])

    return FeedDict(
        fields=fields,
        time=updated,
        title=feed["title"],
        link="https://status.aws.amazon.com/",
        actual_time=updated,
    )


def _parse_gcp(feed: FeedParserDict):
    updated = _parse_time(feed["updated"])
    name = updated.strftime("%b %d, %H:%M %Z") if isinstance(updated, datetime.datetime) else "Details"
    fields = _split_long_fields([UpdateField(name, feed["description"], updated)])

    return FeedDict(
        fields=fields,
        time=updated,
        title=feed["title"],
        link="https://status.cloud.google.com/",
        actual_time=updated,
    )


FEEDS = {
    # statuspage
    "discord": _parse_statuspage,
    "github": _parse_statuspage,
    "cloudflare": _parse_statuspage,
    "python": _parse_statuspage,
    "twitter_api": _parse_statuspage,
    "statuspage": _parse_statuspage,
    "zoom": _parse_statuspage,
    "oracle_cloud": _parse_statuspage,
    "epic_games": _parse_statuspage,
    "digitalocean": _parse_statuspage,
    "reddit": _parse_statuspage,
    "smartthings": _parse_statuspage,
    "sentry": _parse_statuspage,
    # status.io
    "twitter": _parse_statusio,
    "status.io": _parse_statusio,
    # custom
    "aws": _parse_aws,
    "gcp": _parse_gcp,
}
