import datetime
import logging
import re

from dateutil.parser import parse
import discord
from feedparser.util import FeedParserDict
from .objects import FeedDict, UpdateField


log = logging.getLogger("red.vexed.status.rsshelper")


async def process_feed(service: str, feed: FeedParserDict) -> FeedDict:
    return await FEEDS[service](feed.entries[0])


async def _strip_html(thing_to_strip) -> str:
    """Strip dat HTML!

    This removes anything between (and including) `<>` (be careful with this!).
    It will NOT strip `<>` if there is nothing inbeteween.

    `<br />` will be relaced with `\\n`.
    `<small>` will be replaced with `=-=SPLIT=-=`
    `</small>` wil also be reaplaced with `\\n`.
    Any other tags in format <> will be removed.

    Please don't use this elsewhere, it is very funky and tempremental.
    """
    tostrip = str(thing_to_strip)
    raw = tostrip.replace("<br />", "\n")
    raw = raw.replace("<small>", "=-=SPLIT=-=")
    raw = raw.replace("</p>", "\n")
    regex = re.compile("<.*?>")
    stripped = re.sub(regex, "", raw)
    return stripped


def _parse_time(time: str, tzinfos=None):
    try:
        return parse(time, tzinfos=tzinfos)
    except ValueError:
        return discord.Embed.Empty


async def _parse_statuspage(feed: FeedParserDict):
    strippedcontent = await _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    fields = []

    for data in sections:
        try:
            if data != "":
                current = data.split("-", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0].lstrip()
                title = tt[1].rstrip()
                fields.append(UpdateField(name="{} - {}".format(title, time), value=content))
        except IndexError:  # this would be a likely error if something didn't format as expected
            try:
                if data.startswith("THIS IS A SCHEDULED EVENT"):
                    split = data.split("EVENT", 1)
                    value = split[1]
                    fields.append(
                        UpdateField(name="THIS IS A SCHEDULED EVENT", value=f"It is scheduled for {value}")
                    )
                    continue
            except IndexError:
                pass
            fields.append(
                UpdateField(
                    name="Something went wrong with this section",
                    value=f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                )
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    return FeedDict(
        fields=fields,
        time=_parse_time(feed["published"]),
        title=feed["title"],
        link=feed["link"],
    )


async def _parse_statusio(feed: FeedParserDict):
    strippedcontent = await _strip_html(feed["summary_detail"]["value"])

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
                fields.append(UpdateField(name="{} - {}".format(title, time), value=content))
        except IndexError:  # this would be a likely error if something didn't format as expected
            fields.append(
                UpdateField(
                    name="Something went wrong with this section",
                    value=f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                )
            )
            log.warning(
                "Something went wrong while parsing the status for Discord. You can report this to Vexed#3211."
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    return FeedDict(
        fields=fields,
        time=_parse_time(feed["published"]),
        title=feed["title"],
        link=feed["link"],
    )


async def _parse_aws(feed: FeedParserDict):
    fields = [UpdateField(name=feed["published"], value=feed["description"])]

    return FeedDict(
        fields=fields,
        time=_parse_time(feed["published"], tzinfos={"PST": -28800}),
        title=feed["title"],
        link=feed["link"],
    )


async def _parse_gcp(feed: FeedParserDict):
    updated = _parse_time(feed["updated"])
    name = updated.strftime("%b %d, %H:%M %Z") if isinstance(updated, datetime.datetime) else "Details"
    fields = [UpdateField(name=name, value=feed["description"])]

    return FeedDict(
        fields=fields,
        time=updated,
        title=feed["title"],
        link=feed["link"],
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
