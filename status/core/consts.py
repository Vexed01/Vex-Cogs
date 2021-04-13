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
]


LINK_RE = (
    r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]|\(([^\s()<>]|(\([^"
    r"\s()<>]+\)))*\))+(?:\(([^\s()<>]|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"
)
# regex from https://stackoverflow.com/a/28187496

OLD_DEFAULTS = {"mode": ALL, "webhook": False}

UPDATE_NAME = "{} Status Update"

_AVATAR_BASE = "https://cdn.discordapp.com/attachments/813140082989989918/"
# used to keep line length down

FEEDS = {
    "discord": {
        "url": "https://discordstatus.com/",
        # c-spell: disable-next-line
        "id": "srhpyqt94yxb",
        "friendly": "Discord",
        "avatar": _AVATAR_BASE + "813140277367144458/discord.png",
    },
    "github": {
        "url": "https://www.githubstatus.com/",
        # c-spell: disable-next-line
        "id": "kctbh9vrtdwd",
        "friendly": "GitHub",
        "avatar": _AVATAR_BASE + "813140279120232488/github.png",
    },
    "cloudflare": {
        "url": "https://www.cloudflarestatus.com/",
        # c-spell: disable-next-line
        "id": "yh6f0r4529hb",
        "friendly": "Cloudflare",
        "avatar": _AVATAR_BASE + "813140275714195516/cloudflare.png",
    },
    "python": {
        "url": "https://status.python.org/",
        # c-spell: disable-next-line
        "id": "2p66nmmycsj3",
        "friendly": "Python",
        "avatar": _AVATAR_BASE + "814490148917608458/unknown.png",
    },
    "twitter_api": {
        "url": "https://api.twitterstat.us/",
        # c-spell: disable-next-line
        "id": "zjttvm6ql9lp",
        "friendly": "Twitter API",
        "avatar": _AVATAR_BASE + "814863181033898084/aaaaaaaaaaaaaa.png",
    },
    "statuspage": {
        "url": "https://metastatuspage.com/",
        # c-spell: disable-next-line
        "id": "y2j98763l56x",
        "friendly": "Statuspage",
        "avatar": _AVATAR_BASE + "813140261987024976/statuspage.png",
    },
    "zoom": {
        "url": "https://status.zoom.us/",
        # c-spell: disable-next-line
        "id": "14qjgk812kgk",
        "friendly": "Zoom",
        "avatar": _AVATAR_BASE + "813140273751523359/zoom.png",
    },
    "oracle_cloud": {
        "url": "https://ocistatus.oraclecloud.com/",
        # c-spell: disable-next-line
        "id": "2bsbdh54lcgq",
        "friendly": "Oracle Cloud",
        "avatar": _AVATAR_BASE + "813140282538721310/oracle_cloud.png",
    },
    "epic_games": {
        "url": "https://status.epicgames.com/",
        # c-spell: disable-next-line
        "id": "ft308v428dv3",
        "friendly": "Epic Games",
        "avatar": _AVATAR_BASE + "813454141514317854/unknown.png",
    },
    "digitalocean": {
        "url": "https://status.digitalocean.com/",
        # c-spell: disable-next-line
        "id": "s2k7tnzlhrpw",
        "friendly": "DigitalOcean",
        "avatar": _AVATAR_BASE + "813454051613999124/gnlwek2zwhq369yryrzv.png",
    },
    "reddit": {
        "url": "https://www.redditstatus.com/",
        # c-spell: disable-next-line
        "id": "2kbc0d48tv3j",
        "friendly": "Reddit",
        "avatar": _AVATAR_BASE + "813466098040176690/reddit-logo-16.png",
    },
    "sentry": {
        "url": "https://status.sentry.io/",
        # c-spell: disable-next-line
        "id": "t687h3m0nh65",
        "friendly": "Sentry",
        "avatar": _AVATAR_BASE + "819641924788682782/1595357387344.png",
    },
    "geforcenow": {
        "url": "https://status.geforcenow.com/",
        # c-spell: disable-next-line
        "id": "2bdwmtrb0hg9",
        "friendly": "GeForce NOW",
        "avatar": _AVATAR_BASE + "827981724926345226/unknown.png",
    },
}

SPECIAL_INFO = {
    "oracle_cloud": (
        "Oracle is frequently very slow to update their status page. Sometimes, they only update "
        "it when the incident is resolved."
    ),
}
