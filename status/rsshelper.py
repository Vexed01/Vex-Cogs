import datetime
import logging
import re
from dateutil.parser import parse
from feedparser.util import FeedParserDict

log = logging.getLogger("red.vexed.status.rsshelper")


def __init__(self, bot):
    self.bot = bot


async def process_feed(service: str, feed: FeedParserDict):
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


async def parse_discord(feed: FeedParserDict) -> dict:
    """Parse for Discord

    Parameters
    ----------
    feed : FeedParserDict
        From feedparser

    Returns
    -------
    dict
        Standard dict
    """
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])
    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.warning(
                "Something went wrong while parsing the status for Discord. You can report this to Vexed#3211."
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": datetime.datetime.strptime(feed["published"], "%Y-%m-%dT%H:%M:%S%z")})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 7308754})
    return parseddict


async def parse_github(feed: FeedParserDict) -> dict:
    """Parse for GitHub

    Parameters
    ----------
    feed : FeedParserDict
        From feedparser

    Returns
    -------
    dict
        Standard dict
    """
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])
    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 1448738})
    return parseddict


async def parse_cloudflare(feed: FeedParserDict) -> dict:
    """Parser for Cloudflare

    Parameters
    ----------
    feed : FeedParserDict
        From feedparser

    Returns
    -------
    dict
        Standard dict
    """
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])
    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split("\n", 1)
                tc = current[1].split("-", 1)
                time = current[0]
                title = tc[0]
                content = tc[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.warning(
                "Something went wrong while parsing the status for Cloudflare. You can report this to Vexed#3211."
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": datetime.datetime.strptime(feed["published"], "%Y-%m-%dT%H:%M:%S%z")})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 16494144})
    return parseddict


async def parse_python(feed: FeedParserDict) -> dict:
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])
    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 3765669})
    return parseddict


async def parse_twitter_api(feed: FeedParserDict):
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])
    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}
    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )
    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 41715})
    return parseddict


async def parse_statuspage(feed: FeedParserDict):
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 2524415})
    return parseddict


async def parse_zoom(feed: FeedParserDict):
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 2985215})
    return parseddict


async def parse_oracle_cloud(feed: FeedParserDict):
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 13059636})
    return parseddict


async def parse_twitter(feed: FeedParserDict):
    # status.io
    strippedcontent = await _strip_html(feed["summary_detail"]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.warning(
                "Something went wrong while parsing the status for Discord. You can report this to Vexed#3211."
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 2985215})
    return parseddict


async def parse_epic_games(feed: FeedParserDict):
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 949999})
    return parseddict


async def parse_digitalocean(feed: FeedParserDict):
    # statuspage
    strippedcontent = await _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 27134})
    return parseddict


async def parse_reddit(feed: FeedParserDict):
    strippedcontent = await _strip_html(feed["content"][0]["value"])

    sections = strippedcontent.split("=-=SPLIT=-=")
    parseddict = {"fields": []}

    for data in sections:
        try:
            if data != "":
                current = data.split(" - ", 1)
                content = current[1]
                tt = current[0].split("\n")
                time = tt[0]
                title = tt[1]
                parseddict["fields"].append({"name": "{} - {}".format(title, time), "value": content})
        except IndexError:  # this would be a likely error if something didn't format as expected
            parseddict["fields"].append(
                {
                    "name": "Something went wrong with this section",
                    "value": f"I couldn't turn it into the embed properly. Here's the raw data:\n```{data}```",
                }
            )
            log.debug(
                "Unable to parse feed properly. It was still send to all channels. See below debugs:"
                f" Timestamp: {datetime.datetime.utcnow()}"
            )

    parseddict.update({"time": parse(feed["published"])})
    parseddict.update({"title": feed["title"]})
    parseddict.update({"link": feed["link"]})
    parseddict.update({"colour": 16734234})
    return parseddict


FEEDS = {
    "discord": parse_discord,
    "github": parse_github,
    "cloudflare": parse_cloudflare,
    "python": parse_python,
    "twitter_api": parse_twitter_api,
    "statuspage": parse_statuspage,
    "zoom": parse_zoom,
    "oracle_cloud": parse_oracle_cloud,
    "twitter": parse_twitter,
    "epic_games": parse_epic_games,
    "digitalocean": parse_digitalocean,
    "reddit": parse_reddit,
}
