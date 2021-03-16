ALL = "all"
LATEST = "latest"
EDIT = "edit"

WEBHOOK_REASON = "Created for {} status updates"

OLD_DEFAULTS = {"mode": ALL, "webhook": False}


FEED_URLS = {
    "discord": "https://discordstatus.com/history.atom",
    "github": "https://www.githubstatus.com/history.atom",
    "cloudflare": "https://www.cloudflarestatus.com/history.atom",
    "python": "https://status.python.org/history.atom",
    "twitter_api": "https://api.twitterstat.us/history.atom",
    "statuspage": "https://metastatuspage.com/history.atom",
    "zoom": "https://status.zoom.us/history.atom",
    "oracle_cloud": "https://ocistatus.oraclecloud.com/history.atom",
    "twitter": "https://status.twitterstat.us/pages/564314ae3309c22c3b0002fa/rss",
    "epic_games": "https://status.epicgames.com/history.atom",
    "digitalocean": "https://status.digitalocean.com/history.atom",
    "reddit": "https://www.redditstatus.com/history.atom",
    "aws": "https://status.aws.amazon.com/rss/all.rss",
    "gcp": "https://status.cloud.google.com/feed.atom",
    "smartthings": "https://status.smartthings.com/history.atom",
    "sentry": "https://status.sentry.io/history.atom",
    "status.io": "https://status.status.io/pages/51f6f2088643809b7200000d/rss",
}

FEED_FRIENDLY_NAMES = {
    "discord": "Discord",
    "github": "GitHub",
    "cloudflare": "Cloudflare",
    "python": "Python",
    "twitter_api": "Twitter API",
    "statuspage": "Statuspage",
    "zoom": "Zoom",
    "oracle_cloud": "Oracle Cloud",
    "twitter": "Twitter",
    "epic_games": "Epic Games",
    "digitalocean": "DigitalOcean",
    "reddit": "Reddit",
    "aws": "Amazon Web Services",
    "gcp": "Google Cloud Platform",
    "smartthings": "SmartThings",
    "sentry": "Sentry",
    "status.io": "Status.io",
}

AVALIBLE_MODES = {
    "discord": [ALL, LATEST, EDIT],
    "github": [ALL, LATEST, EDIT],
    "cloudflare": [ALL, LATEST, EDIT],
    "python": [ALL, LATEST, EDIT],
    "twitter_api": [ALL, LATEST, EDIT],
    "statuspage": [ALL, LATEST, EDIT],
    "zoom": [ALL, LATEST, EDIT],
    "oracle_cloud": [ALL, LATEST, EDIT],
    "twitter": [ALL, LATEST, EDIT],
    "epic_games": [ALL, LATEST, EDIT],
    "digitalocean": [ALL, LATEST, EDIT],
    "reddit": [ALL, LATEST, EDIT],
    "aws": [LATEST],
    "gcp": [LATEST],
    "smartthings": [ALL, LATEST, EDIT],
    "sentry": [ALL, LATEST, EDIT],
    "status.io": [ALL, LATEST, EDIT],
}

AVATAR_URLS = {
    "discord": "https://cdn.discordapp.com/attachments/813140082989989918/813140277367144458/discord.png",
    "github": "https://cdn.discordapp.com/attachments/813140082989989918/813140279120232488/github.png",
    "cloudflare": "https://cdn.discordapp.com/attachments/813140082989989918/813140275714195516/cloudflare.png",
    "python": "https://cdn.discordapp.com/attachments/813140082989989918/814490148917608458/unknown.png",
    "twitter_api": "https://cdn.discordapp.com/attachments/813140082989989918/814863181033898084/aaaaaaaaaaaaaa.png",
    "statuspage": "https://cdn.discordapp.com/attachments/813140082989989918/813140261987024976/statuspage.png",
    "zoom": "https://cdn.discordapp.com/attachments/813140082989989918/813140273751523359/zoom.png",
    "oracle_cloud": "https://media.discordapp.net/attachments/813140082989989918/813140282538721310/oracle_cloud.png",
    "twitter": "https://cdn.discordapp.com/attachments/813140082989989918/814863181033898084/aaaaaaaaaaaaaa.png",
    "epic_games": "https://cdn.discordapp.com/attachments/813140082989989918/813454141514317854/unknown.png",
    "digitalocean": "https://cdn.discordapp.com/attachments/813140082989989918/813454051613999124/gnlwek2zwhq369yryrzv.png",
    "reddit": "https://cdn.discordapp.com/attachments/813140082989989918/813466098040176690/reddit-logo-16.png",
    "aws": "https://cdn.discordapp.com/attachments/813140082989989918/813730858951245854/aws.png",
    "gcp": "https://cdn.discordapp.com/attachments/813140082989989918/820648558679556116/unknown.png",
    "smartthings": "https://cdn.discordapp.com/attachments/813140082989989918/814600450832859193/zbO2ggF6K2YVII3qOfr0Knj3P0H7OdtTjZAcGBo3kK0vJppGoYsG4TMZINqyPlLa9vI.png",
    "sentry": "https://cdn.discordapp.com/attachments/813140082989989918/819641924788682782/1595357387344.png",
    "status.io": "https://cdn.discordapp.com/attachments/813140082989989918/820621599987728394/4xJxuEM9.png",
}

SPECIAL_INFO = {
    "aws": "AWS frequently posts status updates in both English and the language local to where the incident affects.",
    "oracle_cloud": (
        "Oracle is frequently very slow to update their status page. Sometimes, they only update it when the "
        "incident is resolved."
    ),
}

DONT_REVERSE = ["twitter", "status.io"]
