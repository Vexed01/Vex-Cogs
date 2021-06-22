from typing import Literal

ALL = "all"
LATEST = "latest"
EDIT = "edit"

TYPES_LITERAL = Literal["incidents", "scheduled"]
MODES_LITERAL = Literal["all", "latest", "edit"]
SERVICE_LITERAL = Literal[  # we love DRY
    "discord",
    "github",
    "cloudflare",
    "python",
    "twitter_api",
    "statuspage",
    "zoom",
    "oracle_cloud",
    "epic_games",
    "digitalocean",
    "reddit",
    "sentry",
    "geforcenow",
    "fastly",
]


LINK_RE = (
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]|(\([^"
    r"\s()<>]+\)))*\))+(?:\(([^\s()<>]|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
)
# regex from https://stackoverflow.com/a/28187496

OLD_DEFAULTS = {"mode": ALL, "webhook": False}

UPDATE_NAME = "{} Status Update"

ICON_BASE = "https://vexed01.github.io/Vex-Cogs/api/v1/status_icons/{}.png"

FEEDS = {
    "discord": {
        "url": "https://discordstatus.com/",
        # c-spell: disable-next-line
        "id": "srhpyqt94yxb",
        "friendly": "Discord",
    },
    "github": {
        "url": "https://www.githubstatus.com/",
        # c-spell: disable-next-line
        "id": "kctbh9vrtdwd",
        "friendly": "GitHub",
    },
    "cloudflare": {
        "url": "https://www.cloudflarestatus.com/",
        # c-spell: disable-next-line
        "id": "yh6f0r4529hb",
        "friendly": "Cloudflare",
    },
    "python": {
        "url": "https://status.python.org/",
        # c-spell: disable-next-line
        "id": "2p66nmmycsj3",
        "friendly": "Python",
    },
    "twitter_api": {
        "url": "https://api.twitterstat.us/",
        # c-spell: disable-next-line
        "id": "zjttvm6ql9lp",
        "friendly": "Twitter API",
    },
    "statuspage": {
        "url": "https://metastatuspage.com/",
        # c-spell: disable-next-line
        "id": "y2j98763l56x",
        "friendly": "Statuspage",
    },
    "zoom": {
        "url": "https://status.zoom.us/",
        # c-spell: disable-next-line
        "id": "14qjgk812kgk",
        "friendly": "Zoom",
    },
    "oracle_cloud": {
        "url": "https://ocistatus.oraclecloud.com/",
        # c-spell: disable-next-line
        "id": "2bsbdh54lcgq",
        "friendly": "Oracle Cloud",
    },
    "epic_games": {
        "url": "https://status.epicgames.com/",
        # c-spell: disable-next-line
        "id": "ft308v428dv3",
        "friendly": "Epic Games",
    },
    "digitalocean": {
        "url": "https://status.digitalocean.com/",
        # c-spell: disable-next-line
        "id": "s2k7tnzlhrpw",
        "friendly": "DigitalOcean",
    },
    "reddit": {
        "url": "https://www.redditstatus.com/",
        # c-spell: disable-next-line
        "id": "2kbc0d48tv3j",
        "friendly": "Reddit",
    },
    "sentry": {
        "url": "https://status.sentry.io/",
        # c-spell: disable-next-line
        "id": "t687h3m0nh65",
        "friendly": "Sentry",
    },
    "geforcenow": {
        "url": "https://status.geforcenow.com/",
        # c-spell: disable-next-line
        "id": "2bdwmtrb0hg9",
        "friendly": "GeForce NOW",
    },
    "fastly": {
        "url": "https://status.fastly.com/",
        # c-spell: disable-next-line
        "id": "889dh1w1xtt0",
        "friendly": "Fastly",
    },
}

SPECIAL_INFO = {
    "oracle_cloud": (
        "Oracle is frequently very slow to update their status page. Sometimes, they only update "
        "it when the incident is resolved."
    ),
}
